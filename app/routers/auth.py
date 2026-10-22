import logging
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import login_limiter, register_limiter, otp_limiter
from app.core.security import (
    REFRESH, OAUTH_STATE, REFRESH_COOKIE,
    create_state_token, decode_token, hash_password, verify_password,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models.otp import OtpPurpose
from app.models.user import User, AuthProvider
from app.schemas.user import (
    AuthResponse, ChangePasswordRequest, EmailRequest, LoginRequest, MessageResponse,
    RegisterRequest, ResetPasswordRequest, Token, UserOut, VerifyOtpRequest,
)
from app.services import app_settings
from app.services.audit import audit
from app.services.auth import (
    clear_refresh_cookie, create_user, get_user_by_email, issue_tokens, record_successful_login,
)
from app.services.google_oauth import GoogleOAuthError, build_authorize_url, exchange_code_for_profile
from app.services.otp import issue_otp, verify_otp

logger = logging.getLogger("job_agent.auth")

router = APIRouter()
# Mounted at the path configured as GMAIL_REDIRECT_URI in Google Cloud Console
oauth_callback_router = APIRouter()

STATE_COOKIE = "ja_oauth_state"
GENERIC_OTP_MSG = "If an account exists for this email, a verification code has been sent."


def _auth_response(response: Response, user: User) -> dict:
    return {**issue_tokens(response, user), "user": UserOut.model_validate(user)}


# ── Public config ────────────────────────────────────────────────────────────

@router.get("/config")
async def auth_config(db: AsyncSession = Depends(get_db)):
    return {
        "google_enabled": settings.google_enabled,
        "registration_open": await app_settings.get_value(db, "registration_open"),
        "razorpay_key_id": settings.razorpay_key_id or None,
        "maintenance_banner": await app_settings.get_value(db, "maintenance_banner"),
    }


# ── Registration + email verification ───────────────────────────────────────

@router.post("/register", response_model=MessageResponse, status_code=201,
             dependencies=[Depends(register_limiter)])
async def register(data: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if not await app_settings.get_value(db, "registration_open"):
        raise HTTPException(status_code=403, detail="Registration is currently closed")

    existing = await get_user_by_email(db, data.email)
    if existing:
        if existing.is_verified or existing.auth_provider != AuthProvider.LOCAL:
            raise HTTPException(status_code=400, detail="Email already registered. Please sign in.")
        # Unverified local account: refresh its details and resend a code
        existing.full_name = data.full_name
        existing.hashed_password = hash_password(data.password)
        await issue_otp(db, existing.email, OtpPurpose.VERIFY_EMAIL, enforce_cooldown=False)
        return {"message": "Verification code sent to your email.", "code": "OTP_SENT"}

    user = await create_user(db, data.email, data.full_name, data.password, is_verified=False)
    await issue_otp(db, user.email, OtpPurpose.VERIFY_EMAIL, enforce_cooldown=False)
    await audit(db, "user.register", user.id, request=request)
    return {"message": "Verification code sent to your email.", "code": "OTP_SENT"}


@router.post("/verify-email", response_model=AuthResponse, dependencies=[Depends(otp_limiter)])
async def verify_email(data: VerifyOtpRequest, request: Request, response: Response,
                       db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    await verify_otp(db, user.email, OtpPurpose.VERIFY_EMAIL, data.otp)
    user.is_verified = True
    record_successful_login(user)
    await audit(db, "user.verify_email", user.id, request=request)
    await db.flush()
    return _auth_response(response, user)


@router.post("/resend-otp", response_model=MessageResponse, dependencies=[Depends(otp_limiter)])
async def resend_otp(data: EmailRequest, purpose: str = OtpPurpose.VERIFY_EMAIL,
                     db: AsyncSession = Depends(get_db)):
    if purpose not in OtpPurpose.ALL:
        raise HTTPException(status_code=400, detail="Invalid purpose")
    user = await get_user_by_email(db, data.email)
    should_send = user and user.is_active and (
        purpose == OtpPurpose.RESET_PASSWORD or not user.is_verified
    )
    if should_send:
        await issue_otp(db, user.email, purpose)
    return {"message": GENERIC_OTP_MSG}


# ── Login / refresh / logout ─────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(login_limiter)])
async def login(data: LoginRequest, request: Request, response: Response,
                db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    invalid = HTTPException(status_code=401, detail="Invalid email or password")
    if not user:
        raise invalid

    now = datetime.utcnow()
    if user.locked_until and user.locked_until > now:
        minutes = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status_code=423, detail=f"Account locked. Try again in {minutes} min.")

    if not verify_password(data.password, user.hashed_password):
        if not user.has_password:
            raise HTTPException(status_code=401,
                                detail="This account uses Google sign-in. Continue with Google.")
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= settings.max_failed_logins:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            user.failed_login_attempts = 0
            await audit(db, "user.locked", user.id, request=request)
        await db.commit()
        raise invalid

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled. Contact support.")

    if not user.is_verified:
        try:
            await issue_otp(db, user.email, OtpPurpose.VERIFY_EMAIL)
        except HTTPException:
            pass  # cooldown — a recent code is still valid
        await db.commit()
        raise HTTPException(
            status_code=403,
            detail={"message": "Please verify your email. We sent you a code.", "code": "EMAIL_NOT_VERIFIED"},
        )

    record_successful_login(user)
    await audit(db, "user.login", user.id, request=request)
    return _auth_response(response, user)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No session")
    try:
        payload = decode_token(token, REFRESH)
        user = await db.get(User, int(payload["sub"]))
        version = int(payload.get("ver", 0))
    except (JWTError, KeyError, ValueError, TypeError):
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Session expired")

    if not user or not user.is_active or user.token_version != version:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Session expired")
    return _auth_response(response, user)  # rotates the refresh cookie


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(request: Request, response: Response, db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    user.token_version += 1
    clear_refresh_cookie(response)
    await audit(db, "user.logout_all", user.id, request=request)
    return {"message": "Logged out from all devices"}


# ── Password management ─────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(otp_limiter)])
async def forgot_password(data: EmailRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if user and user.is_active:
        try:
            await issue_otp(db, user.email, OtpPurpose.RESET_PASSWORD)
        except HTTPException:
            pass  # cooldown; keep the response identical to avoid account enumeration
    return {"message": GENERIC_OTP_MSG}


@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(otp_limiter)])
async def reset_password(data: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    await verify_otp(db, user.email, OtpPurpose.RESET_PASSWORD, data.otp)
    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1  # sign out everywhere
    user.failed_login_attempts = 0
    user.locked_until = None
    user.is_verified = True  # they proved inbox ownership
    await audit(db, "user.reset_password", user.id, request=request)
    return {"message": "Password reset successfully. Please sign in."}


@router.post("/change-password", response_model=Token)
async def change_password(data: ChangePasswordRequest, request: Request, response: Response,
                          db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.has_password:
        if not data.current_password or not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if verify_password(data.new_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="New password must differ from the current one")
    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1  # revoke other sessions; this one gets fresh tokens
    await audit(db, "user.change_password", user.id, request=request)
    await db.flush()
    return issue_tokens(response, user)


# ── Google OAuth ─────────────────────────────────────────────────────────────

@router.get("/google/login")
async def google_login():
    if not settings.google_enabled:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    nonce = secrets.token_urlsafe(24)
    state = create_state_token(nonce)
    redirect = RedirectResponse(build_authorize_url(state), status_code=302)
    redirect.set_cookie(STATE_COOKIE, nonce, max_age=600, httponly=True,
                        secure=settings.cookie_secure, samesite="lax", path="/")
    return redirect


def _frontend_redirect(path: str, **params) -> RedirectResponse:
    query = f"?{urlencode(params)}" if params else ""
    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}{path}{query}", status_code=302)


@oauth_callback_router.get("/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None,
                          error: str | None = None, db: AsyncSession = Depends(get_db)):
    if error or not code or not state:
        return _frontend_redirect("/login", error="Google sign-in was cancelled")

    nonce_cookie = request.cookies.get(STATE_COOKIE)
    try:
        payload = decode_token(state, OAUTH_STATE)
    except JWTError:
        return _frontend_redirect("/login", error="Sign-in session expired, please try again")
    if not nonce_cookie or not secrets.compare_digest(payload.get("nonce", ""), nonce_cookie):
        return _frontend_redirect("/login", error="Invalid sign-in state, please try again")

    try:
        profile = await exchange_code_for_profile(code)
    except (GoogleOAuthError, Exception):  # noqa: BLE001
        logger.exception("Google OAuth exchange failed")
        return _frontend_redirect("/login", error="Could not sign in with Google")

    google_id = str(profile["sub"])
    email = profile["email"].lower()
    user = (await db.execute(select(User).where(User.google_id == google_id))).scalar_one_or_none()
    if not user:
        user = await get_user_by_email(db, email)
        if user:
            user.google_id = google_id  # link to existing account (Google verified the email)
            user.is_verified = True
            user.avatar_url = user.avatar_url or profile.get("picture")
        else:
            if not await app_settings.get_value(db, "registration_open"):
                return _frontend_redirect("/login", error="Registration is currently closed")
            user = await create_user(
                db, email, profile.get("name"), None, is_verified=True,
                auth_provider=AuthProvider.GOOGLE, google_id=google_id,
                avatar_url=profile.get("picture"),
            )
            await audit(db, "user.register", user.id, detail={"provider": "google"}, request=request)

    if not user.is_active:
        return _frontend_redirect("/login", error="Account disabled. Contact support.")

    record_successful_login(user)
    await audit(db, "user.login", user.id, detail={"provider": "google"}, request=request)
    await db.flush()

    redirect = _frontend_redirect("/auth/callback")
    issue_tokens(redirect, user)  # sets refresh cookie; frontend calls /refresh
    redirect.delete_cookie(STATE_COOKIE, path="/")
    return redirect
