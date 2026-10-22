from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, text
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.employee import Employee


class UserRole:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EMPLOYEE = "employee"

    ALL = (SUPER_ADMIN, ADMIN, EMPLOYEE)
    STAFF = (SUPER_ADMIN, ADMIN)


class UserPlan:
    FREE = "free"
    PRO = "pro"


class AuthProvider:
    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Google-only accounts get an unusable "!"-prefixed value so the column stays NOT NULL
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Columns below were added after the first release; server_default lets the
    # startup schema sync add them to existing tables (existing users = verified).
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("true")
    )
    auth_provider: Mapped[str] = mapped_column(
        String(20), default=AuthProvider.LOCAL, server_default=AuthProvider.LOCAL
    )
    google_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Bumped on logout / password change to revoke every issued token
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    plan: Mapped[str] = mapped_column(String(20), default=UserPlan.FREE, server_default=UserPlan.FREE)
    plan_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    @property
    def is_staff(self) -> bool:
        return self.role in UserRole.STAFF

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_pro(self) -> bool:
        if self.is_staff:
            return True
        return self.plan == UserPlan.PRO and (
            self.plan_expires_at is None or self.plan_expires_at > datetime.utcnow()
        )

    @property
    def has_password(self) -> bool:
        return bool(self.hashed_password) and not self.hashed_password.startswith("!")
