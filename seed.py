"""
Seed script — populates the database with test data to verify all APIs.

Usage:
    python seed.py            # seed data
    python seed.py --clear    # wipe all data first, then seed
"""

import asyncio
import sys
import uuid
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, AsyncSessionLocal
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.services.auth import hash_password
from app.database import Base


# ── Test credentials (printed at the end) ──────────────────────────────────
TEST_USERS = [
    {
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice Johnson",
        "skills": "Python, FastAPI, PostgreSQL, React, Machine Learning",
        "resume_text": (
            "Alice Johnson | alice@example.com\n\n"
            "EXPERIENCE\n"
            "Senior Backend Engineer — TechCorp (2021–Present)\n"
            "  • Built REST APIs with FastAPI and PostgreSQL\n"
            "  • Deployed ML models to production using Docker & Kubernetes\n\n"
            "SKILLS\n"
            "Python, FastAPI, PostgreSQL, React, Docker, AWS, Machine Learning\n\n"
            "EDUCATION\n"
            "B.Sc. Computer Science — State University, 2018"
        ),
    },
    {
        "email": "bob@example.com",
        "password": "password123",
        "full_name": "Bob Smith",
        "skills": "JavaScript, React, Node.js, TypeScript",
        "resume_text": (
            "Bob Smith | bob@example.com\n\n"
            "EXPERIENCE\n"
            "Frontend Developer — WebAgency (2020–Present)\n"
            "  • Built SPAs with React and TypeScript\n"
            "  • Integrated REST and GraphQL APIs\n\n"
            "SKILLS\n"
            "JavaScript, TypeScript, React, Node.js, GraphQL, Tailwind CSS"
        ),
    },
]

TEST_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "DataFlow Inc.",
        "location": "San Francisco, CA",
        "description": (
            "We are looking for a Senior Python Developer to join our data platform team.\n\n"
            "You will design and build scalable data pipelines, REST APIs, and ML model integrations. "
            "You will collaborate closely with data scientists and frontend engineers."
        ),
        "requirements": (
            "• 4+ years of Python experience\n"
            "• Experience with FastAPI or Django REST Framework\n"
            "• Proficiency with PostgreSQL and Redis\n"
            "• Familiarity with Docker and Kubernetes\n"
            "• Strong understanding of async programming"
        ),
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
        "description": (
            "CloudSoft is hiring a React Frontend Engineer to build beautiful, "
            "performant user interfaces for our SaaS platform.\n\n"
            "You will work with a modern stack: React, TypeScript, Tailwind CSS, and Vite."
        ),
        "requirements": (
            "• 3+ years of React experience\n"
            "• TypeScript proficiency\n"
            "• Experience with REST API integration\n"
            "• Knowledge of CSS / Tailwind\n"
            "• Familiarity with testing (Jest, Vitest)"
        ),
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
        "description": (
            "AI Ventures is looking for an ML Engineer to develop, train, and deploy "
            "machine learning models at scale.\n\n"
            "You will own the full ML lifecycle from data exploration to production deployment."
        ),
        "requirements": (
            "• Strong Python skills (NumPy, Pandas, Scikit-learn)\n"
            "• Experience with PyTorch or TensorFlow\n"
            "• MLOps experience (MLflow, Airflow, or similar)\n"
            "• Cloud platform experience (AWS/GCP/Azure)\n"
            "• Statistics and linear algebra fundamentals"
        ),
        "salary_min": 140000,
        "salary_max": 190000,
        "job_type": "full-time",
        "remote": False,
        "url": "https://example.com/jobs/3",
        "source": "manual",
    },
    {
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "Remote",
        "description": (
            "Join our fast-growing startup as a Full Stack Developer. "
            "You will build features across our entire stack — Python backend, React frontend, "
            "and PostgreSQL database."
        ),
        "requirements": (
            "• 2+ years full stack experience\n"
            "• Python (FastAPI or Flask) backend skills\n"
            "• React / JavaScript frontend skills\n"
            "• SQL database knowledge\n"
            "• Git and CI/CD fundamentals"
        ),
        "salary_min": 90000,
        "salary_max": 120000,
        "job_type": "full-time",
        "remote": True,
        "url": "https://example.com/jobs/4",
        "source": "manual",
    },
    {
        "title": "DevOps Engineer",
        "company": "InfraCo",
        "location": "Chicago, IL",
        "description": (
            "InfraCo is hiring a DevOps Engineer to manage our cloud infrastructure, "
            "CI/CD pipelines, and observability stack."
        ),
        "requirements": (
            "• Experience with AWS or Azure\n"
            "• Kubernetes and Docker proficiency\n"
            "• Terraform or Pulumi IaC experience\n"
            "• CI/CD pipeline experience (GitHub Actions, Jenkins)\n"
            "• Linux administration skills"
        ),
        "salary_min": 110000,
        "salary_max": 150000,
        "job_type": "full-time",
        "remote": False,
        "url": "https://example.com/jobs/5",
        "source": "linkedin",
    },
    {
        "title": "Data Analyst (Contract)",
        "company": "Analytics Co.",
        "location": "Remote",
        "description": "Contract position for a Data Analyst to build dashboards and run ad-hoc analyses.",
        "requirements": (
            "• SQL proficiency\n"
            "• Python (Pandas) for data wrangling\n"
            "• Experience with BI tools (Tableau, Power BI, or Metabase)\n"
            "• Strong communication skills"
        ),
        "salary_min": 70000,
        "salary_max": 90000,
        "job_type": "contract",
        "remote": True,
        "url": "https://example.com/jobs/6",
        "source": "indeed",
    },
]


async def clear_data(db: AsyncSession):
    print("  Clearing existing data…")
    await db.execute(delete(Application))
    await db.execute(delete(Job))
    await db.execute(delete(User))
    await db.commit()
    print("  ✓ All tables cleared")


async def seed(clear: bool = False):
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        if clear:
            await clear_data(db)

        # ── Users ──────────────────────────────────────────────────────────
        print("\nSeeding users…")
        created_users = []
        for u in TEST_USERS:
            existing = await db.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.email == u["email"])
            )
            if existing.scalar_one_or_none():
                print(f"  ⚠  User {u['email']} already exists — skipping")
                result = await db.execute(
                    __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.email == u["email"])
                )
                created_users.append(result.scalar_one())
                continue

            user = User(
                id=uuid.uuid4(),
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                skills=u["skills"],
                resume_text=u["resume_text"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            created_users.append(user)
            print(f"  ✓ User: {u['email']}  (password: {u['password']})")

        await db.flush()

        # ── Jobs ───────────────────────────────────────────────────────────
        print("\nSeeding jobs…")
        created_jobs = []
        for j in TEST_JOBS:
            job = Job(
                id=uuid.uuid4(),
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
            created_jobs.append(job)
            print(f"  ✓ Job: {j['title']} @ {j['company']}")

        await db.flush()

        # ── Applications ───────────────────────────────────────────────────
        print("\nSeeding applications…")
        apps = [
            # Alice's applications
            {"user": created_users[0], "job": created_jobs[0], "status": "applied",      "match_score": 92.0, "notes": "Great match — strong Python skills"},
            {"user": created_users[0], "job": created_jobs[2], "status": "interviewing", "match_score": 85.0, "notes": "Phone screen done, technical next week"},
            {"user": created_users[0], "job": created_jobs[3], "status": "saved",        "match_score": 78.0, "notes": "Startup, consider after interviews"},
            {"user": created_users[0], "job": created_jobs[4], "status": "rejected",     "match_score": 45.0, "notes": "Missing Kubernetes experience"},
            # Bob's applications
            {"user": created_users[1], "job": created_jobs[1], "status": "offered",      "match_score": 95.0, "notes": "Offer received — $130k"},
            {"user": created_users[1], "job": created_jobs[3], "status": "applied",      "match_score": 80.0, "notes": "Applied via LinkedIn"},
        ]

        for a in apps:
            application = Application(
                id=uuid.uuid4(),
                user_id=a["user"].id,
                job_id=a["job"].id,
                status=a["status"],
                match_score=a["match_score"],
                notes=a["notes"],
                applied_at=datetime.utcnow() if a["status"] != "saved" else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(application)
            print(f"  ✓ Application: {a['user'].full_name} → {a['job'].title} [{a['status']}]")

        await db.commit()

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    print(f"\n  Users    : {len(TEST_USERS)}")
    print(f"  Jobs     : {len(TEST_JOBS)}")
    print(f"  Apps     : {len(apps)}")
    print("\n  ── Test Credentials ──────────────────────────────────────")
    for u in TEST_USERS:
        print(f"  Email   : {u['email']}")
        print(f"  Password: {u['password']}")
        print()
    print("  ── Quick API Test (after server starts) ──────────────────")
    print("  Swagger UI : http://localhost:8000/docs")
    print("  Health     : http://localhost:8000/health")
    print("  Jobs list  : http://localhost:8000/api/jobs")
    print("=" * 60)


if __name__ == "__main__":
    clear = "--clear" in sys.argv
    if clear:
        print("⚠  --clear flag detected: all existing data will be deleted first.")
    asyncio.run(seed(clear=clear))
