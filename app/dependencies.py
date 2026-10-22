from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import decode_token, ACCESS

# auto_error=False so we control the response status (401 not 403)
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _user_from_token(token: str, db: AsyncSession) -> User | None:
    try:
        payload = decode_token(token, ACCESS)
        user_id = int(payload["sub"])
        version = int(payload.get("ver", 0))
    except (JWTError, KeyError, ValueError, TypeError):
        return None

    user = await db.get(User, user_id)
    if not user or not user.is_active or user.token_version != version:
        return None
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise _unauthorized()
    user = await _user_from_token(credentials.credentials, db)
    if not user:
        raise _unauthorized("Invalid or expired token")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns the logged-in user or None — does NOT raise 401 if no token."""
    if not credentials:
        return None
    return await _user_from_token(credentials.credentials, db)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Admin or super admin."""
    if current_user.role not in UserRole.STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return current_user
