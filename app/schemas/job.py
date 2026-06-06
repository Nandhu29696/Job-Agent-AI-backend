from datetime import datetime
from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    description: str | None = None
    requirements: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: str | None = None
    remote: bool = False
    url: str | None = None
    source: str | None = None


class JobCreate(JobBase):
    posted_at: datetime | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    requirements: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: str | None = None
    remote: bool | None = None
    url: str | None = None
    is_active: bool | None = None


class JobOut(JobBase):
    id: int
    is_active: bool
    posted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSearch(BaseModel):
    query: str | None = None
    location: str | None = None
    remote: bool | None = None
    job_type: str | None = None
    salary_min: float | None = None
    skip: int = 0
    limit: int = 20
