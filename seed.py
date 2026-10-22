"""
Seed script to populate the database with test data.

Usage:
    python seed.py
    python seed.py --clear
"""

import asyncio
import sys
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, AsyncSessionLocal
from app.models.application import Application
from app.models.employee import Employee
from app.models.job import Job
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.db.migrate import sync_schema
import app.models  # noqa: F401

TEST_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": UserRole.SUPER_ADMIN,
    },
    {
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice Johnson",
        "role": UserRole.EMPLOYEE,
        "skills": "python,fastapi,postgresql,react,machine learning",
        "resume_text": (
            "Alice Johnson | alice@example.com\n\n"
            "EXPERIENCE\n"
            "Senior Backend Engineer - TechCorp (2021-Present)\n"
            "  - Built REST APIs with FastAPI and PostgreSQL\n"
            "  - Deployed ML models to production using Docker and Kubernetes\n\n"
            "SKILLS\n"
            "Python, FastAPI, PostgreSQL, React, Docker, Machine Learning\n"
        ),
        "experience_years": 5.0,
    },
    {
        "email": "bob@example.com",
        "password": "password123",
        "full_name": "Bob Smith",
        "role": UserRole.EMPLOYEE,
        "skills": "javascript,react,node.js,typescript",
        "resume_text": (
            "Bob Smith | bob@example.com\n\n"
            "EXPERIENCE\n"
            "Frontend Developer - WebAgency (2020-Present)\n"
            "  - Built SPAs with React and TypeScript\n"
            "  - Integrated REST APIs\n\n"
            "SKILLS\n"
            "JavaScript, TypeScript, React, Node.js\n"
        ),
        "experience_years": 4.0,
    },
]

TEST_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "DataFlow Inc.",
        "location": "San Francisco, CA",
        "description": "Build scalable APIs and data pipelines.",
        "requirements": "Python, FastAPI, PostgreSQL, Docker",
        "salary_min": 120000,
        "salary_max": 160000,
        "job_type": "full-time",
        "remote": True,
        "url": "https://example.com/jobs/1",
        "source": "linkedin",
    },
    {
        "title": "React Frontend Engineer",
        "company": "CloudSoft",
        "location": "Austin, TX",
        "description": "Build UI with React and TypeScript.",
        "requirements": "React, TypeScript, REST APIs",
        "salary_min": 100000,
        "salary_max": 140000,
        "job_type": "full-time",
        "remote": True,
        "url": "https://example.com/jobs/2",
        "source": "indeed",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Ventures",
        "location": "New York, NY",
        "description": "Train and deploy ML models.",
        "requirements": "Python, PyTorch or TensorFlow, MLOps",
        "salary_min": 140000,
        "salary_max": 190000,
        "job_type": "full-time",
        "remote": False,
        "url": "https://example.com/jobs/3",
        "source": "manual",
    },
]


async def clear_data(db: AsyncSession):
    print("Clearing existing data...")
    await db.execute(delete(Application))
    await db.execute(delete(Employee))
    await db.execute(delete(Job))
    await db.execute(delete(User))
    await db.commit()
    print("All tables cleared")


async def seed(clear: bool = False):
    async with engine.begin() as conn:
        await conn.run_sync(sync_schema)

    async with AsyncSessionLocal() as db:
        if clear:
            await clear_data(db)

        print("Seeding users and employees...")
        created_users: list[User] = []

        for u in TEST_USERS:
            existing_user_result = await db.execute(
                select(User).where(User.email == u["email"])
            )
            user = existing_user_result.scalar_one_or_none()

            if not user:
                user = User(
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(user)
                await db.flush()
                print(f"  created user: {u['email']}")
            else:
                print(f"  user exists: {u['email']}")

            if u["role"] == UserRole.EMPLOYEE:
                existing_emp_result = await db.execute(
                    select(Employee).where(Employee.user_id == user.id)
                )
                employee = existing_emp_result.scalar_one_or_none()
                if not employee:
                    employee = Employee(
                        user_id=user.id,
                        skills=u.get("skills"),
                        resume_text=u.get("resume_text"),
                        experience_years=u.get("experience_years"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(employee)
                    print(f"  created employee profile: {u['email']}")

            created_users.append(user)

        await db.flush()

        print("Seeding jobs...")
        created_jobs: list[Job] = []
        for j in TEST_JOBS:
            existing_job_result = await db.execute(
                select(Job).where(Job.title == j["title"], Job.company == j["company"])
            )
            job = existing_job_result.scalar_one_or_none()
            if not job:
                job = Job(
                    title=j["title"],
                    company=j["company"],
                    location=j["location"],
                    description=j["description"],
                    requirements=j["requirements"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    job_type=j["job_type"],
                    remote=j["remote"],
                    url=j["url"],
                    source=j["source"],
                    is_active=True,
                    posted_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
                db.add(job)
                await db.flush()
                print(f"  created job: {job.title} @ {job.company}")
            else:
                print(f"  job exists: {job.title} @ {job.company}")
            created_jobs.append(job)

        await db.flush()

        employee_users = [u for u in created_users if u.role == UserRole.EMPLOYEE]
        if len(employee_users) >= 2 and len(created_jobs) >= 3:
            app_specs = [
                {
                    "user": employee_users[0],
                    "job": created_jobs[0],
                    "status": "applied",
                    "match_score": 92.0,
                    "notes": "Great match",
                },
                {
                    "user": employee_users[1],
                    "job": created_jobs[1],
                    "status": "offered",
                    "match_score": 95.0,
                    "notes": "Offer received",
                },
                {
                    "user": employee_users[0],
                    "job": created_jobs[2],
                    "status": "saved",
                    "match_score": 80.0,
                    "notes": "Review later",
                },
            ]

            print("Seeding applications...")
            for spec in app_specs:
                existing_app_result = await db.execute(
                    select(Application).where(
                        Application.user_id == spec["user"].id,
                        Application.job_id == spec["job"].id,
                    )
                )
                existing_app = existing_app_result.scalars().first()
                if existing_app:
                    print(
                        f"  application exists: {spec['user'].email} -> {spec['job'].title}"
                    )
                    continue

                app = Application(
                    user_id=spec["user"].id,
                    job_id=spec["job"].id,
                    status=spec["status"],
                    match_score=spec["match_score"],
                    notes=spec["notes"],
                    applied_at=datetime.utcnow() if spec["status"] != "saved" else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(app)
                print(f"  created application: {spec['user'].email} -> {spec['job'].title}")

        await db.commit()

    print("\nSEED COMPLETE")
    print("Credentials:")
    for u in TEST_USERS:
        print(f"  [{u['role']}] {u['email']} / {u['password']}")


if __name__ == "__main__":
    clear_flag = "--clear" in sys.argv
    if clear_flag:
        print("--clear detected: existing rows will be deleted first")
    asyncio.run(seed(clear=clear_flag))
