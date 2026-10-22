from datetime import datetime, timedelta, date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import cast, Date, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin, require_super_admin
from app.models.application import Application
from app.models.job import Job
from app.models.payment import OrderStatus, PaymentOrder
from app.models.resume import Resume, ResumeDownload, ResumeTemplate, TemplatePurchase
from app.models.system import AiUsage, AuditLog
from app.models.user import User, UserRole, UserPlan
from app.schemas.resume import TemplateOut
from app.schemas.user import UserOut
from app.services import app_settings
from app.services.audit import audit

router = APIRouter()


def _page(page: int, size: int) -> tuple[int, int]:
    return (page - 1) * size, size


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    now = datetime.utcnow()
    since_14 = now - timedelta(days=13)
    count = lambda stmt: db.scalar(stmt)  # noqa: E731

    signups = (await db.execute(
        select(cast(User.created_at, Date), func.count(User.id))
        .where(User.created_at >= since_14.replace(hour=0, minute=0, second=0))
        .group_by(cast(User.created_at, Date))
    )).all()
    revenue_daily = (await db.execute(
        select(cast(PaymentOrder.paid_at, Date), func.coalesce(func.sum(PaymentOrder.amount_paise), 0))
        .where(PaymentOrder.status == OrderStatus.PAID,
               PaymentOrder.paid_at >= since_14.replace(hour=0, minute=0, second=0))
        .group_by(cast(PaymentOrder.paid_at, Date))
    )).all()
    days = [(since_14 + timedelta(days=i)).date() for i in range(14)]
    signup_map = {str(d): c for d, c in signups}
    revenue_map = {str(d): int(v) for d, v in revenue_daily}

    top_templates = (await db.execute(
        select(ResumeTemplate.name, func.count(ResumeDownload.id).label("n"))
        .join(ResumeDownload, ResumeDownload.template_id == ResumeTemplate.id)
        .group_by(ResumeTemplate.name).order_by(func.count(ResumeDownload.id).desc()).limit(5)
    )).all()

    return {
        "users": {
            "total": await count(select(func.count(User.id))),
            "verified": await count(select(func.count(User.id)).where(User.is_verified == True)),  # noqa: E712
            "active": await count(select(func.count(User.id)).where(User.is_active == True)),  # noqa: E712
            "pro": await count(select(func.count(User.id)).where(
                User.plan == UserPlan.PRO, or_(User.plan_expires_at.is_(None), User.plan_expires_at > now))),
            "new_7d": await count(select(func.count(User.id)).where(User.created_at >= now - timedelta(days=7))),
        },
        "revenue": {
            "total_paise": int(await count(select(func.coalesce(func.sum(PaymentOrder.amount_paise), 0))
                                           .where(PaymentOrder.status == OrderStatus.PAID)) or 0),
            "last_30d_paise": int(await count(select(func.coalesce(func.sum(PaymentOrder.amount_paise), 0)).where(
                PaymentOrder.status == OrderStatus.PAID, PaymentOrder.paid_at >= now - timedelta(days=30))) or 0),
            "paid_orders": await count(select(func.count(PaymentOrder.id))
                                       .where(PaymentOrder.status == OrderStatus.PAID)),
        },
        "content": {
            "resumes": await count(select(func.count(Resume.id))),
            "downloads": await count(select(func.count(ResumeDownload.id))),
            "jobs_active": await count(select(func.count(Job.id)).where(Job.is_active == True)),  # noqa: E712
            "applications": await count(select(func.count(Application.id))),
            "ai_calls_today": int(await count(select(func.coalesce(func.sum(AiUsage.count), 0))
                                              .where(AiUsage.day == date.today())) or 0),
        },
        "series": [{"day": str(d), "signups": signup_map.get(str(d), 0),
                    "revenue_paise": revenue_map.get(str(d), 0)} for d in days],
        "top_templates": [{"name": n, "downloads": c} for n, c in top_templates],
    }


# ── Users ────────────────────────────────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    role: Literal["super_admin", "admin", "employee"] | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    plan: Literal["free", "pro"] | None = None
    plan_expires_at: datetime | None = None


@router.get("/users")
async def list_users(
    q: str | None = None,
    role: str | None = None,
    status: Literal["active", "disabled", "unverified"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    stmt = select(User)
    if q:
        stmt = stmt.where(or_(User.email.ilike(f"%{q}%"), User.full_name.ilike(f"%{q}%")))
    if role:
        stmt = stmt.where(User.role == role)
    if status == "active":
        stmt = stmt.where(User.is_active == True)  # noqa: E712
    elif status == "disabled":
        stmt = stmt.where(User.is_active == False)  # noqa: E712
    elif status == "unverified":
        stmt = stmt.where(User.is_verified == False)  # noqa: E712
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    offset, limit = _page(page, page_size)
    users = (await db.execute(stmt.order_by(User.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [UserOut.model_validate(u) for u in users]}


async def _target_user(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, body: AdminUserUpdate, request: Request,
                      db: AsyncSession = Depends(get_db), admin: User = Depends(require_super_admin)):
    user = await _target_user(db, user_id)
    changes = body.model_dump(exclude_unset=True)
    if user.id == admin.id and (changes.get("role", admin.role) != admin.role or changes.get("is_active") is False):
        raise HTTPException(status_code=400, detail="You cannot demote or disable your own account")
    if user.role == UserRole.SUPER_ADMIN and changes.get("role") not in (None, UserRole.SUPER_ADMIN):
        remaining = await db.scalar(select(func.count(User.id)).where(
            User.role == UserRole.SUPER_ADMIN, User.id != user.id, User.is_active == True))  # noqa: E712
        if not remaining:
            raise HTTPException(status_code=400, detail="At least one active super admin is required")
    for field, value in changes.items():
        setattr(user, field, value)
    if changes.get("is_active") is False or "role" in changes:
        user.token_version += 1  # force re-login with new permissions
    await audit(db, "admin.user_update", admin.id, "user", user.id,
                {k: str(v) for k, v in changes.items()}, request)
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db),
                      admin: User = Depends(require_super_admin)):
    user = await _target_user(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Demote this super admin before deleting")
    await audit(db, "admin.user_delete", admin.id, "user", user.id, {"email": user.email}, request)
    await db.delete(user)


@router.post("/users/{user_id}/force-logout")
async def force_logout(user_id: int, request: Request, db: AsyncSession = Depends(get_db),
                       admin: User = Depends(require_super_admin)):
    user = await _target_user(db, user_id)
    user.token_version += 1
    await audit(db, "admin.force_logout", admin.id, "user", user.id, request=request)
    return {"message": "User signed out from all devices"}


class GrantTemplate(BaseModel):
    template_id: int


@router.post("/users/{user_id}/grant-template")
async def grant_template(user_id: int, body: GrantTemplate, request: Request, db: AsyncSession = Depends(get_db),
                         admin: User = Depends(require_super_admin)):
    user = await _target_user(db, user_id)
    if not await db.get(ResumeTemplate, body.template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    exists = (await db.execute(select(TemplatePurchase).where(
        TemplatePurchase.user_id == user.id, TemplatePurchase.template_id == body.template_id))).first()
    if not exists:
        db.add(TemplatePurchase(user_id=user.id, template_id=body.template_id, granted_by_admin=True))
    await audit(db, "admin.grant_template", admin.id, "user", user.id, {"template_id": body.template_id}, request)
    return {"message": "Template granted"}


# ── Templates ────────────────────────────────────────────────────────────────

class AdminTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, max_length=40)
    style: str | None = Field(None, max_length=40)
    layout: dict | None = None
    is_premium: bool | None = None
    price_paise: int | None = Field(None, ge=0, le=10_000_000)
    is_active: bool | None = None
    sort_order: int | None = None


@router.get("/templates", response_model=list[TemplateOut])
async def admin_templates(db: AsyncSession = Depends(get_db), _: User = Depends(require_super_admin)):
    rows = (await db.execute(select(ResumeTemplate).order_by(ResumeTemplate.is_premium,
                                                             ResumeTemplate.sort_order))).scalars().all()
    return [TemplateOut.model_validate(t) for t in rows]


@router.patch("/templates/{template_id}", response_model=TemplateOut)
async def update_template(template_id: int, body: AdminTemplateUpdate, request: Request,
                          db: AsyncSession = Depends(get_db), admin: User = Depends(require_super_admin)):
    t = await db.get(ResumeTemplate, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    changes = body.model_dump(exclude_unset=True)
    if changes.get("is_premium") and (changes.get("price_paise", t.price_paise) or 0) <= 0:
        raise HTTPException(status_code=400, detail="Premium templates need a price")
    for field, value in changes.items():
        setattr(t, field, value)
    await audit(db, "admin.template_update", admin.id, "template", t.id,
                {k: str(v) for k, v in changes.items() if k != "layout"}, request)
    await db.flush()
    await db.refresh(t)
    return TemplateOut.model_validate(t)


# ── Payments, audit logs, settings ───────────────────────────────────────────

@router.get("/payments")
async def admin_payments(status: str | None = None, page: int = Query(1, ge=1),
                         page_size: int = Query(25, ge=1, le=100),
                         db: AsyncSession = Depends(get_db), _: User = Depends(require_super_admin)):
    stmt = select(PaymentOrder, User.email).join(User, User.id == PaymentOrder.user_id)
    if status:
        stmt = stmt.where(PaymentOrder.status == status)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    offset, limit = _page(page, page_size)
    rows = (await db.execute(stmt.order_by(PaymentOrder.created_at.desc()).offset(offset).limit(limit))).all()
    return {"total": total, "items": [{
        "id": o.id, "user_email": email, "order_id": o.razorpay_order_id, "payment_id": o.razorpay_payment_id,
        "description": o.description, "item_type": o.item_type, "amount_paise": o.amount_paise,
        "status": o.status, "created_at": o.created_at, "paid_at": o.paid_at} for o, email in rows]}


@router.get("/audit-logs")
async def audit_logs(action: str | None = None, page: int = Query(1, ge=1),
                     page_size: int = Query(50, ge=1, le=200),
                     db: AsyncSession = Depends(get_db), _: User = Depends(require_super_admin)):
    stmt = select(AuditLog, User.email).outerjoin(User, User.id == AuditLog.user_id)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"{action}%"))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    offset, limit = _page(page, page_size)
    rows = (await db.execute(stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit))).all()
    return {"total": total, "items": [{
        "id": a.id, "user_email": email, "action": a.action, "target_type": a.target_type,
        "target_id": a.target_id, "detail": a.detail, "ip": a.ip, "created_at": a.created_at} for a, email in rows]}


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), _: User = Depends(require_super_admin)):
    return await app_settings.get_all(db)


@router.put("/settings")
async def put_settings(values: dict, request: Request, db: AsyncSession = Depends(get_db),
                       admin: User = Depends(require_super_admin)):
    try:
        result = await app_settings.set_values(db, values)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid setting value")
    await audit(db, "admin.settings_update", admin.id, detail={k: str(v) for k, v in values.items()},
                request=request)
    return result
