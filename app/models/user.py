import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UserRole:
    ADMIN = "admin"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="user", cascade="all, delete-orphan"
    )
