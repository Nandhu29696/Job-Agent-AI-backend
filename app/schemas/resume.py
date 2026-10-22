from datetime import datetime
from pydantic import BaseModel, Field, field_validator

S = 200      # short text
M = 1000     # medium text
L = 5000     # long text
MAX_ITEMS = 40
MAX_BULLETS = 15


class Personal(BaseModel):
    full_name: str = Field("", max_length=S)
    headline: str = Field("", max_length=S)
    email: str = Field("", max_length=S)
    phone: str = Field("", max_length=60)
    location: str = Field("", max_length=S)
    website: str = Field("", max_length=300)
    linkedin: str = Field("", max_length=300)
    github: str = Field("", max_length=300)
    # data: URL, ~500KB max
    photo: str = Field("", max_length=700_000)
    date_of_birth: str = Field("", max_length=40)
    nationality: str = Field("", max_length=80)
    marital_status: str = Field("", max_length=40)
    gender: str = Field("", max_length=40)
    visa_status: str = Field("", max_length=120)

    @field_validator("photo")
    @classmethod
    def photo_is_image(cls, v: str) -> str:
        if v and not v.startswith(("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")):
            raise ValueError("Photo must be a PNG, JPEG or WebP image")
        return v


class Experience(BaseModel):
    id: str = Field("", max_length=40)
    title: str = Field("", max_length=S)
    company: str = Field("", max_length=S)
    location: str = Field("", max_length=S)
    start: str = Field("", max_length=30)
    end: str = Field("", max_length=30)
    current: bool = False
    bullets: list[str] = Field(default_factory=list, max_length=MAX_BULLETS)

    @field_validator("bullets")
    @classmethod
    def bullet_len(cls, v: list[str]) -> list[str]:
        return [b[:M] for b in v]


class Education(BaseModel):
    id: str = Field("", max_length=40)
    degree: str = Field("", max_length=S)
    institution: str = Field("", max_length=S)
    location: str = Field("", max_length=S)
    start: str = Field("", max_length=30)
    end: str = Field("", max_length=30)
    grade: str = Field("", max_length=60)
    details: str = Field("", max_length=M)


class SkillGroup(BaseModel):
    id: str = Field("", max_length=40)
    name: str = Field("", max_length=S)
    items: list[str] = Field(default_factory=list, max_length=60)


class Project(BaseModel):
    id: str = Field("", max_length=40)
    name: str = Field("", max_length=S)
    role: str = Field("", max_length=S)
    link: str = Field("", max_length=300)
    description: str = Field("", max_length=M)
    bullets: list[str] = Field(default_factory=list, max_length=MAX_BULLETS)


class SimpleItem(BaseModel):
    """Certifications, awards, publications, licences, volunteer work."""
    id: str = Field("", max_length=40)
    name: str = Field("", max_length=S)
    issuer: str = Field("", max_length=S)
    date: str = Field("", max_length=40)
    detail: str = Field("", max_length=M)
    link: str = Field("", max_length=300)


class Language(BaseModel):
    id: str = Field("", max_length=40)
    name: str = Field("", max_length=80)
    level: str = Field("", max_length=60)


class Reference(BaseModel):
    id: str = Field("", max_length=40)
    name: str = Field("", max_length=S)
    title: str = Field("", max_length=S)
    company: str = Field("", max_length=S)
    contact: str = Field("", max_length=S)


class CustomSection(BaseModel):
    id: str = Field("", max_length=40)
    title: str = Field("", max_length=S)
    items: list[str] = Field(default_factory=list, max_length=30)


class ResumeData(BaseModel):
    personal: Personal = Field(default_factory=Personal)
    summary: str = Field("", max_length=L)
    experience: list[Experience] = Field(default_factory=list, max_length=MAX_ITEMS)
    education: list[Education] = Field(default_factory=list, max_length=MAX_ITEMS)
    skills: list[SkillGroup] = Field(default_factory=list, max_length=20)
    projects: list[Project] = Field(default_factory=list, max_length=MAX_ITEMS)
    certifications: list[SimpleItem] = Field(default_factory=list, max_length=MAX_ITEMS)
    licenses: list[SimpleItem] = Field(default_factory=list, max_length=MAX_ITEMS)
    publications: list[SimpleItem] = Field(default_factory=list, max_length=MAX_ITEMS)
    awards: list[SimpleItem] = Field(default_factory=list, max_length=MAX_ITEMS)
    volunteer: list[SimpleItem] = Field(default_factory=list, max_length=MAX_ITEMS)
    languages: list[Language] = Field(default_factory=list, max_length=20)
    interests: list[str] = Field(default_factory=list, max_length=30)
    references: list[Reference] = Field(default_factory=list, max_length=10)
    declaration: str = Field("", max_length=M)
    custom_sections: list[CustomSection] = Field(default_factory=list, max_length=10)
    section_order: list[str] = Field(default_factory=list, max_length=30)
    hidden_sections: list[str] = Field(default_factory=list, max_length=30)

    model_config = {"extra": "ignore"}


class ResumeCreate(BaseModel):
    title: str = Field("My Resume", min_length=1, max_length=150)
    template_id: int | None = None
    country: str = Field("US", max_length=10)
    job_category: str = Field("general", max_length=40)
    target_job_title: str | None = Field(None, max_length=200)
    target_job_description: str | None = Field(None, max_length=15000)
    data: ResumeData = Field(default_factory=ResumeData)


class ResumeUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=150)
    template_id: int | None = None
    country: str | None = Field(None, max_length=10)
    job_category: str | None = Field(None, max_length=40)
    target_job_title: str | None = Field(None, max_length=200)
    target_job_description: str | None = Field(None, max_length=15000)
    data: ResumeData | None = None
    is_primary: bool | None = None


class TemplateOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    category: str
    style: str
    layout: dict
    is_premium: bool
    price_paise: int
    is_active: bool
    sort_order: int = 0
    owned: bool = False

    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    id: int
    user_id: int
    title: str
    template_id: int | None
    country: str
    job_category: str
    target_job_title: str | None
    target_job_description: str | None
    data: dict
    ats_score: float | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeListItem(BaseModel):
    id: int
    title: str
    template_id: int | None
    country: str
    job_category: str
    target_job_title: str | None
    ats_score: float | None
    is_primary: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
