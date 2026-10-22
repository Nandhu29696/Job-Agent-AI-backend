from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import ai_limiter
from app.database import get_db
from app.dependencies import get_current_user
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeData
from app.services import ats, resume_ai
from app.services.file_text import extract_text
from app.services.usage import consume_ai_credit

router = APIRouter(dependencies=[Depends(ai_limiter)])


class AiContext(BaseModel):
    country: str | None = Field(None, max_length=10)
    job_category: str | None = Field(None, max_length=40)
    job_description: str | None = Field(None, max_length=15000)
    target_job_title: str | None = Field(None, max_length=200)


class SummaryBody(AiContext):
    data: ResumeData


class BulletsBody(AiContext):
    title: str = Field("", max_length=200)
    company: str = Field("", max_length=200)
    bullets: list[str] = Field(default_factory=list, max_length=15)


class TailorBody(BaseModel):
    resume_id: int
    job_id: int | None = None
    job_description: str | None = Field(None, max_length=15000)


class AtsCheckBody(BaseModel):
    text: str | None = Field(None, max_length=30000)
    data: ResumeData | None = None
    job_description: str | None = Field(None, max_length=15000)
    country: str | None = Field(None, max_length=10)
    ai_tips: bool = False


class CoverLetterBody(BaseModel):
    resume_id: int | None = None
    job_id: int | None = None
    job_title: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    job_description: str | None = Field(None, max_length=15000)
    tone: str = Field("professional", pattern="^(professional|enthusiastic|concise|formal)$")


async def _resume(db: AsyncSession, user: User, resume_id: int | None) -> Resume | None:
    if resume_id is None:
        return (await db.execute(
            select(Resume).where(Resume.user_id == user.id)
            .order_by(Resume.is_primary.desc(), Resume.updated_at.desc()).limit(1)
        )).scalar_one_or_none()
    resume = await db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/enhance-summary")
async def enhance_summary(body: SummaryBody, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    await consume_ai_credit(db, user)
    return await resume_ai.enhance_summary(body.data.model_dump(), body.country, body.job_category,
                                           body.job_description, body.target_job_title)


@router.post("/enhance-bullets")
async def enhance_bullets(body: BulletsBody, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    await consume_ai_credit(db, user)
    return await resume_ai.enhance_bullets(body.title, body.company, body.bullets, body.country,
                                           body.job_category, body.job_description, body.target_job_title)


@router.post("/suggest-skills")
async def suggest_skills(body: SummaryBody, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    await consume_ai_credit(db, user)
    return await resume_ai.suggest_skills(body.data.model_dump(), body.country, body.job_category,
                                          body.job_description, body.target_job_title)


@router.post("/tailor")
async def tailor(body: TailorBody, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Tailor a resume to a job. Returns a preview; nothing is saved."""
    resume = await _resume(db, user, body.resume_id)
    jd, title = body.job_description, resume.target_job_title
    if body.job_id:
        job = await db.get(Job, body.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        jd = f"{job.title} at {job.company}\n{job.description or ''}\n{job.requirements or ''}"
        title = job.title
    jd = jd or resume.target_job_description
    if not jd or len(jd.strip()) < 30:
        raise HTTPException(status_code=400, detail="Provide a job description (or pick a job) to tailor against")
    await consume_ai_credit(db, user)
    result = await resume_ai.tailor_resume(resume.data, jd, resume.country, resume.job_category, title)
    before = ats.analyze(data=resume.data, job_description=jd, country=resume.country)["score"]
    after = ats.analyze(data=result["data"], job_description=jd, country=resume.country)["score"]
    return {**result, "ats_before": before, "ats_after": after, "job_description": jd}


@router.post("/ats-check")
async def ats_check(body: AtsCheckBody, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Standalone ATS check for pasted text or structured data."""
    if body.data is None and not (body.text and body.text.strip()):
        raise HTTPException(status_code=400, detail="Provide resume text or data")
    data = body.data.model_dump() if body.data else None
    result = ats.analyze(data=data, text=None if data else body.text, job_description=body.job_description,
                         country=body.country)
    if body.ai_tips:
        await consume_ai_credit(db, user)
        text = ats.resume_to_text(data) if data else body.text
        result["ai_tips"] = await resume_ai.ats_ai_tips(text, body.job_description, result)
    return result


@router.post("/ats-check/file")
async def ats_check_file(
    file: UploadFile = File(...),
    job_description: str | None = Form(None),
    country: str | None = Form(None),
    ai_tips: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    text = await extract_text(file)
    result = ats.analyze(text=text, job_description=job_description, country=country)
    if ai_tips:
        await consume_ai_credit(db, user)
        result["ai_tips"] = await resume_ai.ats_ai_tips(text, job_description, result)
    result["extracted_chars"] = len(text)
    return result


@router.post("/cover-letter")
async def cover_letter(body: CoverLetterBody, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    resume = await _resume(db, user, body.resume_id)
    if not resume:
        raise HTTPException(status_code=400, detail="Create a resume first")
    title, company, jd = body.job_title or "", body.company or "", body.job_description or ""
    job = None
    if body.job_id:
        job = await db.get(Job, body.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        title, company = job.title, job.company
        jd = f"{job.description or ''}\n{job.requirements or ''}"
    if not title or not company:
        raise HTTPException(status_code=400, detail="Provide a job (or job title and company)")
    await consume_ai_credit(db, user)
    letter = await resume_ai.generate_cover_letter(
        title, company, jd, ats.resume_to_text(resume.data),
        resume.data.get("personal", {}).get("full_name") or user.full_name or user.email,
        resume.country, body.tone,
    )
    if job:  # persist onto the user's application for this job, if any
        app = (await db.execute(select(Application).where(
            Application.job_id == job.id, Application.user_id == user.id))).scalars().first()
        if app:
            app.cover_letter = letter
    return {"cover_letter": letter}
