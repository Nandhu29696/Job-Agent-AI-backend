from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AiUsage
from app.models.user import User
from app.services import app_settings


async def get_usage(db: AsyncSession, user: User) -> dict:
    limit = await app_settings.get_value(db, "free_daily_ai_limit")
    row = (
        await db.execute(select(AiUsage).where(AiUsage.user_id == user.id, AiUsage.day == date.today()))
    ).scalar_one_or_none()
    used = row.count if row else 0
    return {
        "used_today": used,
        "daily_limit": None if user.is_pro else limit,
        "remaining": None if user.is_pro else max(0, limit - used),
        "unlimited": user.is_pro,
    }


async def consume_ai_credit(db: AsyncSession, user: User) -> None:
    """Count one AI call. Free users are capped per day; Pro & staff are unlimited."""
    today = date.today()
    row = (
        await db.execute(select(AiUsage).where(AiUsage.user_id == user.id, AiUsage.day == today))
    ).scalar_one_or_none()
    if not user.is_pro:
        limit = await app_settings.get_value(db, "free_daily_ai_limit")
        if row and row.count >= limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Daily free AI limit ({limit}) reached. Upgrade to Pro for unlimited AI.",
            )
    if row:
        row.count += 1
    else:
        db.add(AiUsage(user_id=user.id, day=today, count=1))
    await db.flush()
