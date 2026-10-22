import json
import logging
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.payment import OrderItem, OrderStatus, PaymentOrder
from app.models.resume import ResumeTemplate, TemplatePurchase
from app.models.user import User, UserPlan
from app.services import app_settings, razorpay
from app.services.audit import audit
from app.services.entitlements import owned_template_ids

logger = logging.getLogger("job_agent.payments")
router = APIRouter()


class CreateOrderBody(BaseModel):
    item_type: Literal["template", "pro_plan"]
    item_id: int | None = None


class VerifyBody(BaseModel):
    razorpay_order_id: str = Field(..., max_length=64)
    razorpay_payment_id: str = Field(..., max_length=64)
    razorpay_signature: str = Field(..., max_length=256)


@router.get("/plans")
async def plans(db: AsyncSession = Depends(get_db)):
    return {
        "enabled": settings.razorpay_enabled,
        "key_id": settings.razorpay_key_id or None,
        "currency": settings.currency,
        "pro": {
            "price_paise": await app_settings.get_value(db, "pro_plan_price_paise"),
            "days": await app_settings.get_value(db, "pro_plan_days"),
            "features": ["All premium templates", "Unlimited AI enhancements & agent chats",
                         "Unlimited AI ATS tips", "Priority support"],
        },
        "free": {
            "daily_ai_limit": await app_settings.get_value(db, "free_daily_ai_limit"),
            "features": ["10 professional templates", "ATS score checker", "Country formats", "Job tracker"],
        },
    }


async def _fulfil(db: AsyncSession, order: PaymentOrder, payment_id: str | None) -> None:
    """Idempotently grant what the order paid for."""
    if order.status == OrderStatus.PAID:
        return
    order.status = OrderStatus.PAID
    order.razorpay_payment_id = payment_id or order.razorpay_payment_id
    order.paid_at = datetime.utcnow()
    user = await db.get(User, order.user_id)

    if order.item_type == OrderItem.TEMPLATE and order.item_id:
        exists = (await db.execute(select(TemplatePurchase).where(
            TemplatePurchase.user_id == order.user_id, TemplatePurchase.template_id == order.item_id))).first()
        if not exists:
            db.add(TemplatePurchase(user_id=order.user_id, template_id=order.item_id, order_id=order.id))
    elif order.item_type == OrderItem.PRO_PLAN and user:
        days = int((order.meta or {}).get("days") or await app_settings.get_value(db, "pro_plan_days"))
        now = datetime.utcnow()
        start = user.plan_expires_at if (user.plan == UserPlan.PRO and user.plan_expires_at
                                         and user.plan_expires_at > now) else now
        user.plan = UserPlan.PRO
        user.plan_expires_at = start + timedelta(days=days)
    await audit(db, "payment.paid", order.user_id, "order", order.id,
                {"item_type": order.item_type, "item_id": order.item_id, "amount": order.amount_paise})
    await db.flush()


@router.post("/orders")
async def create_order(body: CreateOrderBody, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    if body.item_type == OrderItem.TEMPLATE:
        template = await db.get(ResumeTemplate, body.item_id or 0)
        if not template or not template.is_active:
            raise HTTPException(status_code=404, detail="Template not found")
        if not template.is_premium or template.price_paise <= 0:
            raise HTTPException(status_code=400, detail="This template is free")
        if user.is_pro or template.id in await owned_template_ids(db, user):
            raise HTTPException(status_code=400, detail="You already have access to this template")
        amount, description, meta = template.price_paise, f"Template: {template.name}", {"slug": template.slug}
        item_id = template.id
    else:
        amount = await app_settings.get_value(db, "pro_plan_price_paise")
        days = await app_settings.get_value(db, "pro_plan_days")
        description, meta, item_id = f"JobAgent Pro — {days} days", {"days": days}, None

    rp = await razorpay.create_order(amount, f"u{user.id}-{int(datetime.utcnow().timestamp())}",
                                     {"user_id": str(user.id), "item_type": body.item_type,
                                      "item_id": str(item_id or "")})
    order = PaymentOrder(user_id=user.id, razorpay_order_id=rp["id"], amount_paise=amount,
                         currency=settings.currency, item_type=body.item_type, item_id=item_id,
                         description=description, meta=meta)
    db.add(order)
    await db.flush()
    return {
        "order_id": rp["id"], "amount": amount, "currency": settings.currency,
        "key_id": settings.razorpay_key_id, "name": "JobAgent AI", "description": description,
        "prefill": {"name": user.full_name or "", "email": user.email},
    }


@router.post("/verify")
async def verify_payment(body: VerifyBody, request: Request, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    # Row lock so a concurrent webhook can't fulfil the same order twice
    order = (await db.execute(select(PaymentOrder).where(
        PaymentOrder.razorpay_order_id == body.razorpay_order_id).with_for_update())).scalar_one_or_none()
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if not razorpay.verify_payment_signature(body.razorpay_order_id, body.razorpay_payment_id,
                                             body.razorpay_signature):
        order.status = OrderStatus.FAILED
        await audit(db, "payment.signature_failed", user.id, "order", order.id, request=request)
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment verification failed")
    await _fulfil(db, order, body.razorpay_payment_id)
    return {"status": "paid", "item_type": order.item_type, "item_id": order.item_id}


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Backup fulfilment if the browser closes before /verify. Configure in Razorpay Dashboard."""
    body = await request.body()
    if not razorpay.verify_webhook_signature(body, request.headers.get("X-Razorpay-Signature", "")):
        raise HTTPException(status_code=400, detail="Invalid signature")
    event = json.loads(body)
    if event.get("event") in ("payment.captured", "order.paid"):
        entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        order = (await db.execute(select(PaymentOrder).where(
            PaymentOrder.razorpay_order_id == order_id).with_for_update())).scalar_one_or_none()
        if order and entity.get("amount") == order.amount_paise:
            await _fulfil(db, order, entity.get("id"))
    return {"ok": True}


@router.get("/me")
async def my_payments(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    orders = (await db.execute(select(PaymentOrder).where(PaymentOrder.user_id == user.id)
                               .order_by(PaymentOrder.created_at.desc()).limit(50))).scalars().all()
    owned = await owned_template_ids(db, user)
    templates = (await db.execute(select(ResumeTemplate).where(ResumeTemplate.id.in_(owned)))).scalars().all() \
        if owned else []
    return {
        "plan": user.plan, "plan_expires_at": user.plan_expires_at, "is_pro": user.is_pro,
        "orders": [{"id": o.id, "order_id": o.razorpay_order_id, "description": o.description,
                    "amount_paise": o.amount_paise, "currency": o.currency, "status": o.status,
                    "created_at": o.created_at, "paid_at": o.paid_at} for o in orders],
        "templates": [{"id": t.id, "name": t.name, "slug": t.slug} for t in templates],
    }
