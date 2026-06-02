from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.employee import Employee
from app.schemas.user import UserCreate
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    role = data.role if data.role in (UserRole.ADMIN, UserRole.EMPLOYEE) else UserRole.EMPLOYEE
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=role,
    )
    db.add(user)
    await db.flush()

    # Auto-create an Employee record for every employee-role user
    if role == UserRole.EMPLOYEE:
        employee = Employee(user_id=user.id)
        db.add(employee)
        await db.flush()

    await db.refresh(user)
    return user
