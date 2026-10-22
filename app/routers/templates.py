from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.resume import ResumeTemplate
from app.models.user import User
from app.schemas.resume import TemplateOut
from app.services.entitlements import owned_template_ids
from app.services.resume_rules import CATEGORIES, COUNTRIES

router = APIRouter()
meta_router = APIRouter()


def _out(t: ResumeTemplate, owned: set[int], user: User | None) -> TemplateOut:
    item = TemplateOut.model_validate(t)
    item.owned = (not t.is_premium) or (user is not None and (user.is_pro or t.id in owned))
    return item


@router.get("/", response_model=list[TemplateOut])
async def list_templates(
    category: str | None = None,
    style: str | None = None,
    premium: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stmt = select(ResumeTemplate).where(ResumeTemplate.is_active == True)  # noqa: E712
    if category:
        stmt = stmt.where(ResumeTemplate.category == category)
    if style:
        stmt = stmt.where(ResumeTemplate.style == style)
    if premium is not None:
        stmt = stmt.where(ResumeTemplate.is_premium == premium)
    stmt = stmt.order_by(ResumeTemplate.is_premium, ResumeTemplate.sort_order)
    templates = (await db.execute(stmt)).scalars().all()
    owned = await owned_template_ids(db, user) if user else set()
    return [_out(t, owned, user) for t in templates]


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db),
                       user: User | None = Depends(get_optional_user)):
    t = await db.get(ResumeTemplate, template_id)
    if not t or not t.is_active:
        raise HTTPException(status_code=404, detail="Template not found")
    owned = await owned_template_ids(db, user) if user else set()
    return _out(t, owned, user)


@meta_router.get("/countries")
async def countries():
    return [{"code": code, **rules} for code, rules in COUNTRIES.items()]


@meta_router.get("/categories")
async def categories():
    return [{"code": code, **cat} for code, cat in CATEGORIES.items()]
