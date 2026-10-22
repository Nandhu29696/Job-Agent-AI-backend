from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, Float, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResumeTemplate(Base):
    __tablename__ = "resume_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # it, healthcare, engineering, finance, education, sales, creative, legal, hospitality, general
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    # modern, professional, classic, minimal, creative, executive, academic
    style: Mapped[str] = mapped_column(String(40), nullable=False)
    # Rendering config consumed by the frontend (layout, colours, fonts, section order)
    layout: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    price_paise: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False, default="My Resume")
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True
    )
    country: Mapped[str] = mapped_column(String(10), default="US")
    job_category: Mapped[str] = mapped_column(String(40), default="general")
    target_job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    template: Mapped["ResumeTemplate | None"] = relationship("ResumeTemplate", lazy="selectin")


class TemplatePurchase(Base):
    __tablename__ = "template_purchases"
    __table_args__ = (UniqueConstraint("user_id", "template_id", name="uq_user_template"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resume_templates.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("payment_orders.id", ondelete="SET NULL"), nullable=True
    )
    granted_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResumeDownload(Base):
    __tablename__ = "resume_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
