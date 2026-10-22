from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.job import JobOut


AppStatus = Literal["saved", "applied", "interviewing", "offered", "rejected"]


class ApplicationBase(BaseModel):
    job_id: int
    status: AppStatus = "saved"
    cover_letter: str | None = Field(None, max_length=10000)
    notes: str | None = Field(None, max_length=5000)


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: AppStatus | None = None
    cover_letter: str | None = Field(None, max_length=10000)
    notes: str | None = Field(None, max_length=5000)
    applied_at: datetime | None = None


class ApplicationOut(ApplicationBase):
    status: str
    id: int
    user_id: int
    match_score: float | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    job: JobOut | None = None

    model_config = {"from_attributes": True}
