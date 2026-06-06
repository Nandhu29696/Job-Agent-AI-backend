from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.job import Job
from app.models.application import Application
from app.schemas.agent import (
    AgentMessage,
    AgentResponse,
    MatchScoreRequest,
    MatchScoreResponse,
)
from app.services.ai_agent import chat_with_agent, generate_cover_letter, analyze_job_match
from app.dependencies import get_current_user
from app.models.user import User
from app.models.employee import Employee

router = APIRouter()


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    body: AgentMessage,
    current_user: User = Depends(get_current_user),
):
    result = await chat_with_agent(body.message, body.context)
    return result


@router.post("/cover-letter/{job_id}")
async def generate_cover_letter_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp_result = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
    employee = emp_result.scalar_one_or_none()
    if not employee or not employee.resume_text:
        raise HTTPException(status_code=400, detail="Please add your resume first")

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cover_letter = await generate_cover_letter(
        job_title=job.title,
        company=job.company,
        job_description=job.description or "",
        resume_text=employee.resume_text,
        user_name=current_user.full_name or current_user.email,
    )
    return {"cover_letter": cover_letter}


@router.post("/match-score", response_model=MatchScoreResponse)
async def get_match_score(
    body: MatchScoreRequest,
    _: User = Depends(get_current_user),
):
    result = await analyze_job_match(body.job_description, body.resume_text)
    return result


@router.post("/match-score/{job_id}", response_model=MatchScoreResponse)
async def get_match_score_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp_result = await db.execute(select(Employee).where(Employee.user_id == current_user.id))
    employee = emp_result.scalar_one_or_none()
    if not employee or not employee.resume_text:
        raise HTTPException(status_code=400, detail="Please add your resume first")

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    score_data = await analyze_job_match(
        job_description=f"{job.title}\n{job.description or ''}\n{job.requirements or ''}",
        resume_text=employee.resume_text,
    )

    # Persist score on matching application if exists
    app_result = await db.execute(
        select(Application).where(
            Application.job_id == job_id, Application.user_id == current_user.id
        )
    )
    app = app_result.scalars().first()
    if app:
        app.match_score = score_data["score"]
        await db.flush()

    return score_data
