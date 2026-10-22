from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == current_user.id)
    )
    if status:
        stmt = stmt.where(Application.status == status)
    stmt = stmt.order_by(Application.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ApplicationOut, status_code=201)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == data.job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    duplicate = await db.execute(
        select(Application.id).where(
            Application.user_id == current_user.id, Application.job_id == data.job_id
        )
    )
    if duplicate.first():
        raise HTTPException(status_code=409, detail="This job is already in your applications")

    app = Application(user_id=current_user.id, **data.model_dump())
    db.add(app)
    await db.flush()

    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == app.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.patch("/{app_id}", response_model=ApplicationOut)
async def update_application(
    app_id: int,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == app_id, Application.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("status") == "applied" and not app.applied_at:
        update_data["applied_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(app, field, value)
    await db.flush()
    await db.refresh(app)
    return app


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Application).where(
            Application.id == app_id, Application.user_id == current_user.id
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
