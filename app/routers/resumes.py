import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import ai_limiter
from app.database import get_db
from app.dependencies import get_current_user
from app.models.employee import Employee
from app.models.resume import Resume, ResumeDownload, ResumeTemplate
from app.models.user import User
from app.schemas.resume import ResumeCreate, ResumeData, ResumeListItem, ResumeOut, ResumeUpdate
from app.services import ats, resume_ai
from app.services.entitlements import can_use_template
from app.services.file_text import extract_text
from app.services.resume_rules import COUNTRIES, CATEGORIES
from app.services.usage import consume_ai_credit

router = APIRouter()

MAX_RESUMES_PER_USER = 25


async def _get_owned(db: AsyncSession, resume_id: int, user: User) -> Resume:
    resume = await db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


async def _validate_meta(db: AsyncSession, country: str | None, category: str | None, template_id: int | None):
    if country is not None and country.upper() not in COUNTRIES:
        raise HTTPException(status_code=400, detail="Unsupported country")
    if category is not None and category.lower() not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Unsupported job category")
    if template_id is not None:
        t = await db.get(ResumeTemplate, template_id)
        if not t or not t.is_active:
            raise HTTPException(status_code=400, detail="Template not found")


async def _prefill(db: AsyncSession, user: User) -> dict:
    """Seed a new resume from the account + legacy employee profile."""
    data = ResumeData().model_dump()
    data["personal"]["full_name"] = user.full_name or ""
    data["personal"]["email"] = user.email
    emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalar_one_or_none()
    if emp:
        data["personal"]["phone"] = emp.phone or ""
        data["personal"]["linkedin"] = emp.linkedin_url or ""
        if emp.skills:
            data["skills"] = [{"id": uuid.uuid4().hex[:8], "name": "Skills",
                               "items": [s.strip() for s in emp.skills.split(",") if s.strip()]}]
        if emp.education:
            data["education"] = [{"id": uuid.uuid4().hex[:8], "degree": emp.education, "institution": "",
                                  "location": "", "start": "", "end": "", "grade": "", "details": ""}]
    return data


async def _count(db: AsyncSession, user: User) -> int:
    return len((await db.execute(select(Resume.id).where(Resume.user_id == user.id))).scalars().all())


@router.get("/", response_model=list[ResumeListItem])
async def list_resumes(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rows = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.updated_at.desc()))
    return rows.scalars().all()


@router.post("/", response_model=ResumeOut, status_code=201)
async def create_resume(body: ResumeCreate, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    if await _count(db, user) >= MAX_RESUMES_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum of {MAX_RESUMES_PER_USER} resumes reached")
    await _validate_meta(db, body.country, body.job_category, body.template_id)
    data = body.data.model_dump()
    if not data["personal"]["full_name"] and not data["experience"]:
        data = await _prefill(db, user)
    data = resume_ai.adapt_to_country(data, body.country, body.job_category)["data"] \
        if not data.get("section_order") else data
    is_first = await _count(db, user) == 0
    resume = Resume(
        user_id=user.id, title=body.title, template_id=body.template_id, country=body.country.upper(),
        job_category=body.job_category.lower(), target_job_title=body.target_job_title,
        target_job_description=body.target_job_description, data=data, is_primary=is_first,
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _get_owned(db, resume_id, user)


@router.patch("/{resume_id}", response_model=ResumeOut)
async def update_resume(resume_id: int, body: ResumeUpdate, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    resume = await _get_owned(db, resume_id, user)
    changes = body.model_dump(exclude_unset=True)
    await _validate_meta(db, changes.get("country"), changes.get("job_category"), changes.get("template_id"))
    if changes.get("is_primary"):
        await db.execute(update(Resume).where(Resume.user_id == user.id).values(is_primary=False))
    for field, value in changes.items():
        if field == "country" and value:
            value = value.upper()
        if field == "job_category" and value:
            value = value.lower()
        setattr(resume, field, value)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    resume = await _get_owned(db, resume_id, user)
    await db.delete(resume)


@router.post("/{resume_id}/duplicate", response_model=ResumeOut, status_code=201)
async def duplicate_resume(resume_id: int, db: AsyncSession = Depends(get_db),
                           user: User = Depends(get_current_user)):
    src = await _get_owned(db, resume_id, user)
    if await _count(db, user) >= MAX_RESUMES_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum of {MAX_RESUMES_PER_USER} resumes reached")
    copy = Resume(
        user_id=user.id, title=f"{src.title} (copy)"[:150], template_id=src.template_id, country=src.country,
        job_category=src.job_category, target_job_title=src.target_job_title,
        target_job_description=src.target_job_description, data=src.data,
    )
    db.add(copy)
    await db.flush()
    await db.refresh(copy)
    return copy


class AtsOptions(BaseModel):
    job_description: str | None = Field(None, max_length=15000)
    ai_tips: bool = False


@router.post("/{resume_id}/ats")
async def resume_ats(resume_id: int, body: AtsOptions, db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    resume = await _get_owned(db, resume_id, user)
    jd = body.job_description if body.job_description is not None else resume.target_job_description
    result = ats.analyze(data=resume.data, job_description=jd, country=resume.country)
    resume.ats_score = result["score"]
    if body.ai_tips:
        await consume_ai_credit(db, user)
        result["ai_tips"] = await resume_ai.ats_ai_tips(ats.resume_to_text(resume.data), jd, result)
    await db.flush()
    return result


class AdaptBody(BaseModel):
    country: str = Field(..., max_length=10)
    job_category: str | None = Field(None, max_length=40)


@router.post("/{resume_id}/adapt-country")
async def adapt_country(resume_id: int, body: AdaptBody, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """Preview a country-adapted version. The client saves it if the user accepts."""
    resume = await _get_owned(db, resume_id, user)
    await _validate_meta(db, body.country, body.job_category, None)
    return resume_ai.adapt_to_country(resume.data, body.country, body.job_category or resume.job_category)


@router.post("/{resume_id}/download")
async def authorize_download(resume_id: int, request: Request, db: AsyncSession = Depends(get_db),
                             user: User = Depends(get_current_user)):
    """Gate PDF export: free templates for all, premium ones need purchase or Pro."""
    resume = await _get_owned(db, resume_id, user)
    template = await db.get(ResumeTemplate, resume.template_id) if resume.template_id else None
    if not await can_use_template(db, user, template):
        raise HTTPException(
            status_code=402,
            detail={"message": f"'{template.name}' is a premium template. Purchase it or upgrade to Pro to download.",
                    "code": "TEMPLATE_LOCKED", "template_id": template.id, "price_paise": template.price_paise},
        )
    db.add(ResumeDownload(user_id=user.id, resume_id=resume.id, template_id=resume.template_id))
    await db.flush()
    return {"allowed": True}


@router.post("/import", response_model=ResumeOut, status_code=201, dependencies=[Depends(ai_limiter)])
async def import_resume(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    title: str = Form("Imported Resume"),
    country: str = Form("US"),
    job_category: str = Form("general"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload a PDF/DOCX/TXT (or paste text) and let AI convert it to an editable resume."""
    if await _count(db, user) >= MAX_RESUMES_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum of {MAX_RESUMES_PER_USER} resumes reached")
    await _validate_meta(db, country, job_category, None)
    if file is not None and file.filename:
        raw_text = await extract_text(file)
    elif text and len(text.strip()) >= 50:
        raw_text = text[:20000]
    else:
        raise HTTPException(status_code=400, detail="Upload a file or paste at least 50 characters of resume text")

    await consume_ai_credit(db, user)
    parsed = await resume_ai.parse_resume_text(raw_text)
    data = ResumeData.model_validate(parsed).model_dump()
    data = resume_ai.adapt_to_country(data, country, job_category)["data"]
    resume = Resume(user_id=user.id, title=title[:150] or "Imported Resume", country=country.upper(),
                    job_category=job_category.lower(), data=data)
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume
