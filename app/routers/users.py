from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserOut, UserUpdate
from app.dependencies import get_current_user
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.services.usage import get_usage

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.get("/me/usage")
async def my_usage(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_usage(db, current_user)


@router.get("/me/dashboard")
async def my_dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_jobs = await db.scalar(select(func.count(Job.id)).where(Job.is_active == True))  # noqa: E712
    status_rows = await db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    )
    resumes = (await db.execute(
        select(Resume.id, Resume.title, Resume.ats_score, Resume.updated_at)
        .where(Resume.user_id == current_user.id).order_by(Resume.updated_at.desc()).limit(5)
    )).all()
    return {
        "total_jobs": total_jobs or 0,
        "applications_by_status": {status: count for status, count in status_rows.all()},
        "resumes": [{"id": r.id, "title": r.title, "ats_score": r.ats_score, "updated_at": r.updated_at}
                    for r in resumes],
        "usage": await get_usage(db, current_user),
    }
