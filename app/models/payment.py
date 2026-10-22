from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OrderStatus:
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"


class OrderItem:
    TEMPLATE = "template"
    PRO_PLAN = "pro_plan"


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    razorpay_order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.CREATED, index=True)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
