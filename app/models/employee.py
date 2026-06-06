from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Employee(Base):
    __tablename__ = "employees"

    emp_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    resume_text: Mapped[str] = mapped_column(Text, nullable=True)
    # Comma-separated skill list, e.g. "python,fastapi,react"
    skills: Mapped[str] = mapped_column(Text, nullable=True)
    experience_years: Mapped[float] = mapped_column(Float, nullable=True)
    education: Mapped[str] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="employee")
