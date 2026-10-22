"""
JobAgent AI — a tool-using career agent.

The LLM decides which tools to call (Ollama native tool calling); tools run
server-side against the *current user's* data only, and results are fed back
until the model produces a final answer (max MAX_STEPS rounds).
"""
import json
import logging
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume, ResumeTemplate
from app.models.user import User
from app.services import ats, llm
from app.services.resume_rules import COUNTRIES, get_country

logger = logging.getLogger("job_agent.agent")

MAX_STEPS = 5
APP_STATUSES = ("saved", "applied", "interviewing", "offered", "rejected")

SYSTEM_PROMPT = """You are JobAgent AI, an expert career agent inside a job-search and resume-building app.
You can take actions with tools: search jobs, read the user's resumes and applications, run ATS checks,
save jobs, update application status, recommend resume templates and explain country resume formats.

Rules:
- Use tools whenever the user asks about their own data, jobs, scores or wants an action done. Do not guess data.
- Only state facts returned by tools; never invent job listings, IDs or scores.
- After using tools, answer in a friendly, concise way with clear next steps. Use short markdown lists.
- For resume editing, point users to the Resume Builder where AI can rewrite sections.
- Today's date: {today}. User's name: {name}."""


def _tool(name: str, description: str, properties: dict | None = None, required: list | None = None) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {}, "required": required or []},
    }}


TOOLS = [
    _tool("search_jobs", "Search active job listings by keyword, location or remote.",
          {"query": {"type": "string", "description": "Keywords e.g. 'python developer'"},
           "location": {"type": "string"}, "remote": {"type": "boolean"}}),
    _tool("get_job_details", "Get full details of one job by its id.",
          {"job_id": {"type": "integer"}}, ["job_id"]),
    _tool("get_my_resumes", "List the user's resumes with ATS scores, country and category."),
    _tool("check_ats_score", "Run an ATS-friendliness check on a resume, optionally against a job.",
          {"resume_id": {"type": "integer", "description": "Omit to use the primary resume"},
           "job_id": {"type": "integer", "description": "Optional job to match keywords against"}}),
    _tool("get_my_applications", "List the user's job applications, optionally filtered by status.",
          {"status": {"type": "string", "enum": list(APP_STATUSES)}}),
    _tool("save_job", "Save a job to the user's applications pipeline.",
          {"job_id": {"type": "integer"}}, ["job_id"]),
    _tool("update_application_status", "Move an application to a new status.",
          {"application_id": {"type": "integer"}, "status": {"type": "string", "enum": list(APP_STATUSES)}},
          ["application_id", "status"]),
    _tool("recommend_templates", "Recommend resume templates for a job category and/or style.",
          {"category": {"type": "string", "description": "it, healthcare, engineering, finance, education, "
                                                           "sales, creative, legal, hospitality, general"},
           "style": {"type": "string", "description": "modern, professional, classic, minimal, creative, "
                                                        "executive, academic"}}),
    _tool("get_country_resume_guidelines", "Resume/CV conventions for a country (photo, length, personal details).",
          {"country": {"type": "string", "description": "ISO code: " + ", ".join(COUNTRIES)}}, ["country"]),
]


def _int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class AgentTools:
    def __init__(self, db: AsyncSession, user: User):
        self.db, self.user = db, user
        self.actions: list[dict] = []

    async def _primary_resume(self, resume_id: int | None) -> Resume | None:
        if resume_id:
            r = await self.db.get(Resume, resume_id)
            return r if r and r.user_id == self.user.id else None
        return (await self.db.execute(
            select(Resume).where(Resume.user_id == self.user.id)
            .order_by(Resume.is_primary.desc(), Resume.updated_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def search_jobs(self, query: str | None = None, location: str | None = None, remote=None):
        stmt = select(Job).where(Job.is_active == True)  # noqa: E712
        if query:
            terms = [t for t in str(query).split() if len(t) > 1][:5]
            for t in terms:
                stmt = stmt.where(or_(Job.title.ilike(f"%{t}%"), Job.description.ilike(f"%{t}%"),
                                      Job.requirements.ilike(f"%{t}%"), Job.company.ilike(f"%{t}%")))
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))
        if isinstance(remote, bool):
            stmt = stmt.where(Job.remote == remote)
        jobs = (await self.db.execute(stmt.order_by(Job.created_at.desc()).limit(6))).scalars().all()
        for j in jobs[:3]:
            self.actions.append({"type": "link", "label": f"View: {j.title}", "to": f"/jobs/{j.id}"})
        return {"count": len(jobs), "jobs": [
            {"id": j.id, "title": j.title, "company": j.company, "location": j.location, "remote": j.remote,
             "job_type": j.job_type, "salary": [j.salary_min, j.salary_max]} for j in jobs]}

    async def get_job_details(self, job_id=None):
        job = await self.db.get(Job, _int(job_id) or 0)
        if not job:
            return {"error": "Job not found"}
        self.actions.append({"type": "link", "label": f"Open {job.title}", "to": f"/jobs/{job.id}"})
        return {"id": job.id, "title": job.title, "company": job.company, "location": job.location,
                "remote": job.remote, "description": (job.description or "")[:1200],
                "requirements": (job.requirements or "")[:1000]}

    async def get_my_resumes(self):
        rows = (await self.db.execute(select(Resume).where(Resume.user_id == self.user.id)
                                      .order_by(Resume.updated_at.desc()))).scalars().all()
        if not rows:
            self.actions.append({"type": "link", "label": "Create a resume", "to": "/resumes"})
        return {"resumes": [{"id": r.id, "title": r.title, "country": r.country, "category": r.job_category,
                             "ats_score": r.ats_score, "primary": r.is_primary,
                             "target_job": r.target_job_title} for r in rows]}

    async def check_ats_score(self, resume_id=None, job_id=None):
        resume = await self._primary_resume(_int(resume_id))
        if not resume:
            self.actions.append({"type": "link", "label": "Create a resume", "to": "/resumes"})
            return {"error": "User has no resume yet"}
        jd = resume.target_job_description
        job = await self.db.get(Job, _int(job_id)) if _int(job_id) else None
        if job:
            jd = f"{job.title}\n{job.description or ''}\n{job.requirements or ''}"
        result = ats.analyze(data=resume.data, job_description=jd, country=resume.country)
        resume.ats_score = result["score"]
        self.actions.append({"type": "link", "label": f"Improve '{resume.title}'", "to": f"/resumes/{resume.id}"})
        return {"resume": resume.title, "score": result["score"], "grade": result["grade"],
                "breakdown": {b["label"]: f"{b['score']}/{b['max']}" for b in result["breakdown"]},
                "missing_keywords": result["keywords"]["missing"][:10],
                "top_suggestions": result["suggestions"][:5]}

    async def get_my_applications(self, status: str | None = None):
        stmt = (select(Application).options(selectinload(Application.job))
                .where(Application.user_id == self.user.id))
        if status in APP_STATUSES:
            stmt = stmt.where(Application.status == status)
        apps = (await self.db.execute(stmt.order_by(Application.updated_at.desc()).limit(20))).scalars().all()
        self.actions.append({"type": "link", "label": "Open applications board", "to": "/applications"})
        return {"applications": [{"id": a.id, "job_id": a.job_id, "job": a.job.title if a.job else None,
                                  "company": a.job.company if a.job else None, "status": a.status,
                                  "match_score": a.match_score} for a in apps]}

    async def save_job(self, job_id=None):
        jid = _int(job_id)
        job = await self.db.get(Job, jid or 0)
        if not job:
            return {"error": "Job not found"}
        existing = (await self.db.execute(select(Application).where(
            Application.user_id == self.user.id, Application.job_id == jid))).scalars().first()
        if existing:
            return {"ok": True, "message": f"Already in pipeline with status '{existing.status}'",
                    "application_id": existing.id}
        app = Application(user_id=self.user.id, job_id=jid, status="saved")
        self.db.add(app)
        await self.db.flush()
        self.actions.append({"type": "link", "label": "View pipeline", "to": "/applications"})
        return {"ok": True, "message": f"Saved '{job.title}' at {job.company}", "application_id": app.id}

    async def update_application_status(self, application_id=None, status=None):
        if status not in APP_STATUSES:
            return {"error": f"Invalid status. Use one of {APP_STATUSES}"}
        app = await self.db.get(Application, _int(application_id) or 0)
        if not app or app.user_id != self.user.id:
            return {"error": "Application not found"}
        app.status = status
        if status == "applied" and not app.applied_at:
            app.applied_at = datetime.utcnow()
        await self.db.flush()
        return {"ok": True, "application_id": app.id, "status": status}

    async def recommend_templates(self, category: str | None = None, style: str | None = None):
        stmt = select(ResumeTemplate).where(ResumeTemplate.is_active == True)  # noqa: E712
        if category:
            stmt = stmt.where(ResumeTemplate.category == str(category).lower())
        if style:
            stmt = stmt.where(ResumeTemplate.style == str(style).lower())
        rows = (await self.db.execute(stmt.order_by(ResumeTemplate.is_premium, ResumeTemplate.sort_order)
                                      .limit(6))).scalars().all()
        if not rows:  # fall back to free templates
            rows = (await self.db.execute(select(ResumeTemplate).where(
                ResumeTemplate.is_active == True, ResumeTemplate.is_premium == False).limit(5))).scalars().all()  # noqa: E712
        self.actions.append({"type": "link", "label": "Browse templates", "to": "/templates"})
        return {"templates": [{"name": t.name, "category": t.category, "style": t.style,
                               "premium": t.is_premium, "price_inr": t.price_paise / 100} for t in rows]}

    async def get_country_resume_guidelines(self, country: str | None = None):
        rules = get_country(country)
        return {k: rules[k] for k in ("name", "document_name", "paper", "max_pages", "photo",
                                      "date_format", "section_order", "tips")}

    async def run(self, name: str, args: dict) -> dict:
        fn = getattr(self, name, None)
        if name.startswith("_") or name == "run" or fn is None:
            return {"error": f"Unknown tool {name}"}
        try:
            return await fn(**{k: v for k, v in (args or {}).items() if v not in ("", None)})
        except TypeError as exc:
            return {"error": f"Bad arguments: {exc}"}


def _summarize(name: str, result: dict) -> str:
    if "error" in result:
        return result["error"]
    if name == "search_jobs":
        return f"Found {result['count']} job(s)"
    if name == "check_ats_score":
        return f"ATS score {result['score']}/100 ({result['grade']})"
    if name == "get_my_resumes":
        return f"{len(result['resumes'])} resume(s)"
    if name == "get_my_applications":
        return f"{len(result['applications'])} application(s)"
    if name == "recommend_templates":
        return f"{len(result['templates'])} template(s)"
    return result.get("message") or "Done"


async def run_agent(db: AsyncSession, user: User, message: str, history: list[dict]) -> dict:
    tools = AgentTools(db, user)
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(
        today=datetime.utcnow().strftime("%Y-%m-%d"), name=user.full_name or "there")}]
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])[:4000]})
    messages.append({"role": "user", "content": message})

    steps: list[dict] = []
    reply = ""
    for _ in range(MAX_STEPS):
        msg = await llm.chat(messages, tools=TOOLS, temperature=0.3)
        calls = msg.tool_calls or []
        if not calls:
            reply = (msg.content or "").strip()
            break
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [{"function": {"name": c.function.name,
                                                      "arguments": c.function.arguments}} for c in calls]})
        for call in calls[:4]:
            name, args = call.function.name, dict(call.function.arguments or {})
            result = await tools.run(name, args)
            steps.append({"tool": name, "args": args, "summary": _summarize(name, result)})
            messages.append({"role": "tool", "content": json.dumps(result, default=str)[:6000], "tool_name": name})
    else:
        # Out of steps: ask for a final answer without tools
        msg = await llm.chat(messages + [{"role": "user", "content": "Summarise what you found for me."}])
        reply = (msg.content or "").strip()

    # De-duplicate action links
    seen, actions = set(), []
    for a in tools.actions:
        if a["to"] not in seen:
            seen.add(a["to"])
            actions.append(a)
    return {"reply": reply or "I couldn't come up with an answer — could you rephrase?",
            "steps": steps, "actions": actions[:5]}
