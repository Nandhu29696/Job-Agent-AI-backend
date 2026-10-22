import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

import app.models  # noqa: F401 — registers every model before create_all
from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.db.migrate import sync_schema
from app.models.user import User, UserRole
from app.routers import (
    admin, agent, applications, auth, employees, jobs, payments, resume_ai, resumes, templates, users,
)
from app.services.template_catalog import seed_templates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("job_agent")


async def _bootstrap_super_admin() -> None:
    """Guarantee at least one super admin: SUPER_ADMIN_EMAIL, else the oldest admin."""
    async with AsyncSessionLocal() as db:
        exists = (await db.execute(select(User.id).where(User.role == UserRole.SUPER_ADMIN).limit(1))).first()
        if exists:
            return
        candidate = None
        if settings.super_admin_email:
            candidate = (await db.execute(
                select(User).where(User.email == settings.super_admin_email.lower()))).scalar_one_or_none()
        if not candidate:
            candidate = (await db.execute(select(User).where(User.role == UserRole.ADMIN)
                                          .order_by(User.id).limit(1))).scalar_one_or_none()
        if candidate:
            candidate.role = UserRole.SUPER_ADMIN
            candidate.token_version += 1
            await db.commit()
            logger.info("Promoted %s to super_admin", candidate.email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(sync_schema)
    async with AsyncSessionLocal() as db:
        added = await seed_templates(db)
        if added:
            logger.info("Seeded %s resume templates", added)
    await _bootstrap_super_admin()
    yield
    await engine.dispose()


app = FastAPI(
    title="Job Agent AI",
    description="AI-powered job search, resume builder and application assistant",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.cookie_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(auth.oauth_callback_router, prefix="/api/integrations/gmail", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(resume_ai.router, prefix="/api/resume-ai", tags=["Resume AI"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(templates.meta_router, prefix="/api/meta", tags=["Meta"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Super Admin"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Job Agent AI"}
