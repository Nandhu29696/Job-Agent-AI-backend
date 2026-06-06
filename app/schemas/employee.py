from datetime import datetime
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    resume_text: str | None = None
    skills: str | None = None          # comma-separated: "python,fastapi,react"
    experience_years: float | None = None
    education: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    emp_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
