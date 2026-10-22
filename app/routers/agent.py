from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.rate_limit import ai_limiter
from app.database import get_db
from app.models.job import Job
from app.models.application import Application
from app.models.resume import Resume
from app.schemas.agent import AgentMessage, AgentResponse, MatchScoreRequest, MatchScoreResponse
from app.services.ai_agent import run_agent
from app.services.ats import resume_to_text
from app.services.resume_ai import generate_cover_letter, analyze_job_match
from app.services.usage import consume_ai_credit
from app.dependencies import get_current_user
from app.models.user import User
from app.models.employee import Employee

router = APIRouter(dependencies=[Depends(ai_limiter)])


async def _resume_text(db: AsyncSession, user: User) -> str:
    """Primary structured resume, falling back to the legacy profile resume_text."""
    resume = (await db.execute(
        select(Resume).where(Resume.user_id == user.id)
        .order_by(Resume.is_primary.desc(), Resume.updated_at.desc()).limit(1)
    )).scalar_one_or_none()
    if resume:
        text = resume_to_text(resume.data)
        if len(text) > 80:
            return text
    emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalar_one_or_none()
    if emp and emp.resume_text:
        return emp.resume_text
    raise HTTPException(status_code=400, detail="Please create a resume first")


async def _job(db: AsyncSession, job_id: int) -> Job:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    body: AgentMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await consume_ai_credit(db, current_user)
    return await run_agent(db, current_user, body.message, [t.model_dump() for t in body.history])


@router.post("/cover-letter/{job_id}")
async def generate_cover_letter_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_text = await _resume_text(db, current_user)
    job = await _job(db, job_id)
    await consume_ai_credit(db, current_user)
    cover_letter = await generate_cover_letter(
        job_title=job.title,
        company=job.company,
        job_description=f"{job.description or ''}\n{job.requirements or ''}",
        resume_text=resume_text,
        user_name=current_user.full_name or current_user.email,
    )
    app = (await db.execute(select(Application).where(
        Application.job_id == job_id, Application.user_id == current_user.id))).scalars().first()
    if app:
        app.cover_letter = cover_letter
    return {"cover_letter": cover_letter}


@router.post("/match-score", response_model=MatchScoreResponse)
async def get_match_score(
    body: MatchScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await consume_ai_credit(db, current_user)
    return await analyze_job_match(body.job_description, body.resume_text)


@router.post("/match-score/{job_id}", response_model=MatchScoreResponse)
async def get_match_score_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_text = await _resume_text(db, current_user)
    job = await _job(db, job_id)
    await consume_ai_credit(db, current_user)
    score_data = await analyze_job_match(
        job_description=f"{job.title}\n{job.description or ''}\n{job.requirements or ''}",
        resume_text=resume_text,
    )
    app = (await db.execute(select(Application).where(
        Application.job_id == job_id, Application.user_id == current_user.id))).scalars().first()
    if app:
        app.match_score = score_data["score"]
    return score_data
