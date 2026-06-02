"""
Seed script â€” populates the database with test data to verify all APIs.

Usage:
    python seed.py            # seed data
    python seed.py --clear    # wipe all data first, then seed
"""

import asyncio
import sys
import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.job import Job
from app.models.application import Application
from app.services.auth import hash_password
from app.database import Base


# â”€â”€ Test credentials (printed at the end) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TEST_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
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
            "Senior Backend Engineer â€” TechCorp (2021â€“Present)\n"
            "  â€¢ Built REST APIs with FastAPI and PostgreSQL\n"
            "  â€¢ Deployed ML models to production using Docker & Kubernetes\n\n"
            "SKILLS\n"
            "Python, FastAPI, PostgreSQL, React, Docker, AWS, Machine Learning\n\n"
            "EDUCATION\n"
            "B.Sc. Computer Science â€” State University, 2018"
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
            "Frontend Developer â€” WebAgency (2020â€“Present)\n"
            "  â€¢ Built SPAs with React and TypeScript\n"
            "  â€¢ Integrated REST and GraphQL APIs\n\n"
            "SKILLS\n"
            "JavaScript, TypeScript, React, Node.js, GraphQL, Tailwind CSS"
        ),
        "experience_years": 4.0,
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
            "â€¢ 4+ years of Python experience\n"
            "â€¢ Experience with FastAPI or Django REST Framework\n"
            "â€¢ Proficiency with PostgreSQL and Redis\n"
            "â€¢ Familiarity with Docker and Kubernetes\n"
            "â€¢ Strong understanding of async programming"
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
            "â€¢ 3+ years of React experience\n"
            "â€¢ TypeScript proficiency\n"
            "â€¢ Experience with REST API integration\n"
            "â€¢ Knowledge of CSS / Tailwind\n"
            "â€¢ Familiarity with testing (Jest, Vitest)"
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
            "â€¢ Strong Python skills (NumPy, Pandas, Scikit-learn)\n"
            "â€¢ Experience with PyTorch or TensorFlow\n"
            "â€¢ MLOps experience (MLflow, Airflow, or similar)\n"
            "â€¢ Cloud platform experience (AWS/GCP/Azure)\n"
            "â€¢ Statistics and linear algebra fundamentals"
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
            "You will build features across our entire stack â€” Python backend, React frontend, "
            "and PostgreSQL database."
        ),
        "requirements": (
            "â€¢ 2+ years full stack experience\n"
            "â€¢ Python (FastAPI or Flask) backend skills\n"
            "â€¢ React / JavaScript frontend skills\n"
            "â€¢ SQL database knowledge\n"
            "â€¢ Git and CI/CD fundamentals"
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
            "â€¢ Experience with AWS or Azure\n"
            "â€¢ Kubernetes and Docker proficiency\n"
            "â€¢ Terraform or Pulumi IaC experience\n"
            "â€¢ CI/CD pipeline experience (GitHub Actions, Jenkins)\n"
            "â€¢ Linux administration skills"
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
            "â€¢ SQL proficiency\n"
            "â€¢ Python (Pandas) for data wrangling\n"
            "â€¢ Experience with BI tools (Tableau, Power BI, or Metabase)\n"
            "â€¢ Strong communication skills"
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
    print("  Clearing existing dataâ€¦")
    await db.execute(delete(Application))
    await db.execute(delete(Employee))
    await db.execute(delete(Job))
    await db.execute(delete(User))
    await db.commit()
    print("  âœ“ All tables cleared")


async def seed(clear: bool = False):
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        if clear:
            await clear_data(db)

        # â”€â”€ Users + Employees â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("\nSeeding usersâ€¦")
        created_users = []
        for u in TEST_USERS:
            existing = await db.execute(select(User).where(User.email == u["email"]))
            if existing.scalar_one_or_none():
                print(f"  âš   User {u['email']} already exists â€” skipping")
                result = await db.execute(select(User).where(User.email == u["email"]))
                created_users.append(result.scalar_one())
                continue

            user = User(
                id=uuid.uuid4(),
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            await db.flush()

            # Auto-create Employee record for employee-role users
            if u["role"] == UserRole.EMPLOYEE:
                employee = Employee(
                    emp_id=uuid.uuid4(),
                    user_id=user.id,
                    skills=u.get("skills"),
                    resume_text=u.get("resume_text"),
                    experience_years=u.get("experience_years"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(employee)
                print(f"  âœ“ Employee: {u['email']}  (skills: {u.get('skills', 'none')})")
            else:
                print(f"  âœ“ Admin: {u['email']}")

            created_users.append(user)

        await db.flush()

        # â”€â”€ Jobs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("\nSeeding jobsâ€¦")
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
            print(f"  âœ“ Job: {j['title']} @ {j['company']}")

        await db.flush()

        # Get employee users only (skip admin at index 0)
        employee_users = [u for u in created_users if u.role == UserRole.EMPLOYEE]

        # â”€â”€ Applications â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("\nSeeding applicationsâ€¦")
        apps = []
        if len(employee_users) >= 2:
            apps = [
                # Alice's applications
                {"user": employee_users[0], "job": created_jobs[0], "status": "applied",      "match_score": 92.0, "notes": "Great match â€” strong Python skills"},
                {"user": employee_users[0], "job": created_jobs[2], "status": "interviewing", "match_score": 85.0, "notes": "Phone screen done, technical next week"},
                {"user": employee_users[0], "job": created_jobs[3], "status": "saved",        "match_score": 78.0, "notes": "Startup, consider after interviews"},
                {"user": employee_users[0], "job": created_jobs[4], "status": "rejected",     "match_score": 45.0, "notes": "Missing Kubernetes experience"},
                # Bob's applications
                {"user": employee_users[1], "job": created_jobs[1], "status": "offered",      "match_score": 95.0, "notes": "Offer received â€” $130k"},
                {"user": employee_users[1], "job": created_jobs[3], "status": "applied",      "match_score": 80.0, "notes": "Applied via LinkedIn"},
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
            print(f"  âœ“ Application: {a['user'].full_name} â†’ {a['job'].title} [{a['status']}]")

        await db.commit()

    # â”€â”€ Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n" + "=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    print(f"\n  Users    : {len(TEST_USERS)}")
    print(f"  Jobs     : {len(TEST_JOBS)}")
    print(f"  Apps     : {len(apps)}")
    print("\n  â”€â”€ Test Credentials â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    for u in TEST_USERS:
        print(f"  [{u['role'].upper()}]  {u['email']}  /  {u['password']}")
    print()
    print("  â”€â”€ Quick API Test (after server starts) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    print("  Swagger UI : http://localhost:8000/docs")
    print("  Health     : http://localhost:8000/health")
    print("  Jobs list  : http://localhost:8000/api/jobs")
    print("=" * 60)


if __name__ == "__main__":
    clear = "--clear" in sys.argv
    if clear:
        print("âš   --clear flag detected: all existing data will be deleted first.")
    asyncio.run(seed(clear=clear))
