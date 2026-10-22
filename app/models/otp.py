from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OtpPurpose:
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"

    ALL = (VERIFY_EMAIL, RESET_PASSWORD)


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
