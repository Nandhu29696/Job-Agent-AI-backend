import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.job import JobOut


class ApplicationBase(BaseModel):
    job_id: uuid.UUID
    status: str = "saved"
    cover_letter: str | None = None
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: str | None = None
    cover_letter: str | None = None
    notes: str | None = None
    applied_at: datetime | None = None


class ApplicationOut(ApplicationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    match_score: float | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    job: JobOut | None = None

    model_config = {"from_attributes": True}
