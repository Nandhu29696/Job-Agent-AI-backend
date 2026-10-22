from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import generate_otp, hash_otp, constant_time_equals
from app.models.otp import OtpCode
from app.services.email import send_otp_email


async def issue_otp(db: AsyncSession, email: str, purpose: str, enforce_cooldown: bool = True) -> None:
    email = email.lower()
    now = datetime.utcnow()

    if enforce_cooldown:
        latest = (
            await db.execute(
                select(OtpCode)
                .where(OtpCode.email == email, OtpCode.purpose == purpose)
                .order_by(OtpCode.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest and (now - latest.created_at).total_seconds() < settings.otp_resend_cooldown_seconds:
            wait = settings.otp_resend_cooldown_seconds - int((now - latest.created_at).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait}s before requesting another code.",
            )

    # Invalidate any previous unused codes for this purpose
    await db.execute(
        update(OtpCode)
        .where(OtpCode.email == email, OtpCode.purpose == purpose, OtpCode.consumed == False)  # noqa: E712
        .values(consumed=True)
    )

    code = generate_otp(settings.otp_length)
    db.add(
        OtpCode(
            email=email,
            purpose=purpose,
            code_hash=hash_otp(email, code),
            expires_at=now + timedelta(seconds=settings.otp_expiry_seconds),
        )
    )
    await db.flush()
    await send_otp_email(email, code, purpose)


async def verify_otp(db: AsyncSession, email: str, purpose: str, code: str) -> None:
    """Consume a valid OTP or raise 400. Attempts are counted per code."""
    email = email.lower()
    otp = (
        await db.execute(
            select(OtpCode)
            .where(OtpCode.email == email, OtpCode.purpose == purpose, OtpCode.consumed == False)  # noqa: E712
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    invalid = HTTPException(status_code=400, detail="Invalid or expired code")
    if not otp or otp.expires_at < datetime.utcnow():
        raise invalid
    if otp.attempts >= settings.otp_max_attempts:
        otp.consumed = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Too many attempts. Request a new code.")

    if not constant_time_equals(otp.code_hash, hash_otp(email, code.strip())):
        otp.attempts += 1
        # Commit the attempt counter even though the request fails
        await db.commit()
        raise invalid

    otp.consumed = True
    await db.flush()
