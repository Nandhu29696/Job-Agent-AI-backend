from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import ResumeTemplate, TemplatePurchase
from app.models.user import User


async def owned_template_ids(db: AsyncSession, user: User) -> set[int]:
    rows = await db.execute(select(TemplatePurchase.template_id).where(TemplatePurchase.user_id == user.id))
    return set(rows.scalars().all())


async def can_use_template(db: AsyncSession, user: User, template: ResumeTemplate | None) -> bool:
    """Free templates: everyone. Premium: purchased, Pro plan, or staff."""
    if template is None or not template.is_premium or user.is_pro:
        return True
    return template.id in await owned_template_ids(db, user)
