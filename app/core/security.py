import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS = "access"
REFRESH = "refresh"
OAUTH_STATE = "oauth_state"

REFRESH_COOKIE = "ja_refresh"
REFRESH_COOKIE_PATH = "/api/auth"


# ── Passwords ────────────────────────────────────────────────────────────────

PASSWORD_RULES = (
    "at least 8 characters, including an uppercase letter, a lowercase letter and a number"
)


def validate_password_strength(password: str) -> str:
    """Raise ValueError if the password is weak. Used by pydantic validators."""
    if len(password) < 8:
        raise ValueError(f"Password must be {PASSWORD_RULES}")
    # bcrypt silently truncates after 72 bytes
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes")
    if not (re.search(r"[a-z]", password) and re.search(r"[A-Z]", password) and re.search(r"\d", password)):
        raise ValueError(f"Password must be {PASSWORD_RULES}")
    return password


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or hashed.startswith("!"):
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


def unusable_password() -> str:
    return "!" + secrets.token_urlsafe(32)


# ── JWT ──────────────────────────────────────────────────────────────────────

def _encode(payload: dict, minutes: int) -> str:
    now = datetime.utcnow()
    payload = {**payload, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: int, role: str, token_version: int) -> str:
    return _encode(
        {"sub": str(user_id), "role": role, "ver": token_version, "type": ACCESS},
        settings.jwt_access_minutes,
    )


def create_refresh_token(user_id: int, token_version: int) -> str:
    return _encode(
        {"sub": str(user_id), "ver": token_version, "type": REFRESH, "jti": uuid.uuid4().hex},
        settings.jwt_refresh_minutes,
    )


def create_state_token(nonce: str) -> str:
    return _encode({"nonce": nonce, "type": OAUTH_STATE}, 10)


def decode_token(token: str, expected_type: str) -> dict:
    """Decode and validate type. Raises jose.JWTError on any problem."""
    from jose import JWTError

    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != expected_type:
        raise JWTError("Wrong token type")
    return payload


# ── OTP helpers ──────────────────────────────────────────────────────────────

def generate_otp(length: int) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(email: str, code: str) -> str:
    return hmac.new(
        settings.secret_key.encode(), f"{email.lower()}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
