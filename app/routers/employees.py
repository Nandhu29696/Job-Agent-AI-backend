import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeOut, EmployeeUpdate
from app.dependencies import get_current_user, require_admin

router = APIRouter()


@router.get("/me", response_model=EmployeeOut)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee: get own profile."""
    result = await db.execute(
        select(Employee).where(Employee.user_id == current_user.id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return employee


@router.patch("/me", response_model=EmployeeOut)
async def update_my_profile(
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee: update own skills / resume."""
    result = await db.execute(
        select(Employee).where(Employee.user_id == current_user.id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    await db.flush()
    await db.refresh(employee)
    return employee


# ── Admin-only endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=list[EmployeeOut])
async def list_employees(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: list all employee profiles."""
    result = await db.execute(select(Employee).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{emp_id}", response_model=EmployeeOut)
async def get_employee(
    emp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: get any employee profile by emp_id."""
    result = await db.execute(select(Employee).where(Employee.emp_id == emp_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.delete("/{emp_id}", status_code=204)
async def delete_employee(
    emp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: delete employee profile."""
    result = await db.execute(select(Employee).where(Employee.emp_id == emp_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    await db.delete(employee)
