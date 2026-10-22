from datetime import datetime

from fastapi import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    unusable_password,
    REFRESH_COOKIE,
    REFRESH_COOKIE_PATH,
)
from app.models.employee import Employee
from app.models.user import User, UserRole, AuthProvider


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    full_name: str | None,
    password: str | None = None,
    *,
    role: str = UserRole.EMPLOYEE,
    is_verified: bool = False,
    auth_provider: str = AuthProvider.LOCAL,
    google_id: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Create a user. Role is chosen by trusted server code only — never from request bodies."""
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password) if password else unusable_password(),
        full_name=full_name,
        role=role,
        is_verified=is_verified,
        auth_provider=auth_provider,
        google_id=google_id,
        avatar_url=avatar_url,
    )
    db.add(user)
    await db.flush()

    if role == UserRole.EMPLOYEE:
        db.add(Employee(user_id=user.id))
        await db.flush()

    await db.refresh(user)
    return user


def issue_tokens(response: Response, user: User) -> dict:
    """Return an access token and set the refresh token as an httpOnly cookie."""
    access = create_access_token(user.id, user.role, user.token_version)
    refresh = create_refresh_token(user.id, user.token_version)
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh,
        max_age=settings.jwt_refresh_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )
    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_minutes * 60,
    }


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)


def record_successful_login(user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
