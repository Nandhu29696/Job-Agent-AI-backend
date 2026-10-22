"""AI-powered resume features built on the local LLM."""
import copy
import re
import uuid

from app.services import llm
from app.services.ats import resume_to_text
from app.services.resume_rules import get_category, get_country

WRITER_SYSTEM = (
    "You are an expert resume writer and certified professional career coach. "
    "You write concise, achievement-focused, ATS-friendly content. "
    "Never invent employers, degrees, certifications or numbers that are not implied by the input; "
    "when a metric is unknown use a placeholder like [X%] so the user can fill it in."
)

STR_LIST = {"type": "array", "items": {"type": "string"}}


def _clip(text: str | None, n: int) -> str:
    return (text or "")[:n]


def _context(country: str | None, category: str | None, jd: str | None, target_title: str | None) -> str:
    c, cat = get_country(country), get_category(category)
    lines = [f"Target country: {c['name']} ({c['document_name']}).",
             f"Industry: {cat['name']} — relevant keywords: {cat['keywords_hint']}."]
    if target_title:
        lines.append(f"Target job title: {target_title}.")
    if jd:
        lines.append(f"Job description:\n{_clip(jd, 2500)}")
    if country and country.upper() == "UK":
        lines.append("Use British spelling.")
    return "\n".join(lines)


# ── Section enhancement ──────────────────────────────────────────────────────

async def enhance_summary(data: dict, country=None, category=None, jd=None, target_title=None) -> dict:
    prompt = (
        f"{_context(country, category, jd, target_title)}\n\n"
        f"Candidate resume:\n{_clip(resume_to_text(data), 3500)}\n\n"
        "Write 3 alternative professional summaries (each 45-80 words, third person implied, no 'I'). "
        "Each should state role/seniority, years of experience if known, top 3-4 skills and 1 standout achievement. "
        "Also suggest a short headline (max 10 words)."
    )
    schema = {"type": "object", "properties": {"headline": {"type": "string"}, "summaries": STR_LIST},
              "required": ["headline", "summaries"]}
    out = await llm.complete_json(WRITER_SYSTEM, prompt, schema, temperature=0.6)
    return {"headline": str(out.get("headline", ""))[:200],
            "summaries": [str(s) for s in out.get("summaries", []) if s][:3]}


async def enhance_bullets(title: str, company: str, bullets: list[str], country=None, category=None,
                          jd=None, target_title=None) -> dict:
    existing = "\n".join(f"- {b}" for b in bullets if b.strip()) or "(no bullets yet)"
    count = min(6, max(4, len([b for b in bullets if b.strip()])))
    prompt = (
        f"{_context(country, category, jd, target_title)}\n\n"
        f"Role: {title} at {company}\nCurrent bullets:\n{_clip(existing, 3000)}\n\n"
        f"Rewrite these into {count} strong resume bullets. Each bullet is one full sentence that starts with a "
        "past-tense action verb, is 15-28 words long, shows impact with a metric (use [X] placeholders if unknown), "
        "and naturally includes relevant keywords from the job description. If there were no bullets, draft "
        "typical achievements for this role.\n"
        "Output ONLY the bullets, one per line, each line starting with '- '. No intro, no headings."
    )
    # Plain-text lines are far more reliable than JSON arrays on small local models
    clean: list[str] = []
    for _ in range(2):
        raw = await llm.complete(WRITER_SYSTEM, prompt, temperature=0.5)
        clean = [re.sub(r"^\s*(?:[-•*▪]|\d+[.)])\s*", "", ln).strip().strip('"')
                 for ln in raw.splitlines()]
        clean = [b for b in clean if len(b.split()) >= 6 and not b.endswith(":")]
        if len(clean) >= 2:
            break
    return {"bullets": clean[:8], "tips": []}


async def suggest_skills(data: dict, country=None, category=None, jd=None, target_title=None) -> dict:
    current = ", ".join(i for g in data.get("skills") or [] for i in g.get("items") or [])
    prompt = (
        f"{_context(country, category, jd, target_title)}\n\n"
        f"Current skills: {current or '(none)'}\n"
        f"Experience summary:\n{_clip(resume_to_text(data), 2000)}\n\n"
        "Suggest skills grouped into 2-4 groups (e.g. 'Technical', 'Tools', 'Soft skills', 'Clinical'). "
        "Prioritise skills that appear in the job description and are plausible for this candidate. "
        "Max 10 items per group."
    )
    schema = {"type": "object", "properties": {"groups": {"type": "array", "items": {
        "type": "object", "properties": {"name": {"type": "string"}, "items": STR_LIST},
        "required": ["name", "items"]}}}, "required": ["groups"]}
    out = await llm.complete_json(WRITER_SYSTEM, prompt, schema)
    groups = []
    for g in out.get("groups", [])[:4]:
        if isinstance(g, dict) and g.get("items"):
            groups.append({"name": str(g.get("name", "Skills"))[:60],
                           "items": [str(i)[:60] for i in g["items"]][:12]})
    return {"groups": groups}


async def tailor_resume(data: dict, jd: str, country=None, category=None, target_title=None) -> dict:
    """Return a tailored copy of the resume plus a change log. Caller decides whether to save."""
    summary = await enhance_summary(data, country, category, jd, target_title)
    tailored = copy.deepcopy(data)
    changes = []
    if summary["summaries"]:
        tailored["summary"] = summary["summaries"][0]
        changes.append("Rewrote the professional summary for this job")
    if summary["headline"]:
        tailored.setdefault("personal", {})["headline"] = summary["headline"]
        changes.append("Updated headline")

    # Rewrite bullets of the 2 most recent roles (keeps latency reasonable on local models)
    for idx, exp in enumerate((tailored.get("experience") or [])[:2]):
        res = await enhance_bullets(exp.get("title", ""), exp.get("company", ""), exp.get("bullets") or [],
                                    country, category, jd, target_title)
        if res["bullets"]:
            exp["bullets"] = res["bullets"]
            changes.append(f"Rewrote bullets for {exp.get('title') or 'role'} at {exp.get('company') or 'company'}")

    skills = await suggest_skills(tailored, country, category, jd, target_title)
    if skills["groups"]:
        existing = {i.lower() for g in tailored.get("skills") or [] for i in g.get("items") or []}
        added = []
        for g in skills["groups"]:
            new_items = [i for i in g["items"] if i.lower() not in existing]
            if not new_items:
                continue
            target = next((x for x in tailored.setdefault("skills", []) if x.get("name", "").lower() == g["name"].lower()), None)
            if target:
                target["items"] = (target.get("items") or []) + new_items
            else:
                tailored["skills"].append({"id": uuid.uuid4().hex[:8], "name": g["name"], "items": new_items})
            added += new_items
            existing.update(i.lower() for i in new_items)
        if added:
            changes.append("Suggested skills to add (verify you have them): " + ", ".join(added[:12]))
    return {"data": tailored, "changes": changes}


# ── Country format adaptation (deterministic) ───────────────────────────────

def adapt_to_country(data: dict, country: str, category: str | None = None) -> dict:
    rules, cat = get_country(country), get_category(category)
    adapted = copy.deepcopy(data)
    personal = adapted.setdefault("personal", {})
    changes = []
    for field in rules["personal_forbidden"]:
        if personal.get(field):
            personal[field] = ""
            changes.append(f"Removed {field.replace('_', ' ')} (not appropriate for {rules['name']})")

    # Country order first, then category-specific extras, then anything else the user had
    order: list[str] = []
    for key in rules["section_order"] + cat["section_order"] + (adapted.get("section_order") or []):
        if key not in order:
            order.append(key)
    if order != (adapted.get("section_order") or []):
        adapted["section_order"] = order
        changes.append(f"Reordered sections to {rules['name']} / {cat['name']} conventions")

    if country.upper() == "IN" and not adapted.get("declaration"):
        adapted["declaration"] = ("I hereby declare that the information furnished above is true "
                                  "to the best of my knowledge and belief.")
        changes.append("Added a declaration (customary in India — remove for MNC applications)")
    if country.upper() != "IN" and adapted.get("declaration"):
        adapted["declaration"] = ""
        changes.append("Removed declaration (not used outside India)")

    tips = list(rules["tips"])
    if rules["photo"] == "expected" and not personal.get("photo"):
        tips.insert(0, "Add a professional headshot — it is expected here.")
    return {"data": adapted, "changes": changes, "tips": tips, "rules": rules}


# ── Import: plain text → structured resume ──────────────────────────────────
#
# Hybrid parser: headings, contact details, skills and lists are extracted
# deterministically; the LLM only structures one section at a time (experience,
# education, projects), which small local models handle far more reliably.

SECTION_HEADINGS = {
    "summary": r"summary|professional summary|profile|professional profile|objective|career objective|about me|personal statement",
    "experience": r"experience|work experience|professional experience|employment|employment history|work history|career history",
    "education": r"education|academic background|academics|qualifications|educational qualifications",
    "skills": r"skills|technical skills|key skills|core competencies|competencies|technologies|tech stack",
    "projects": r"projects|academic projects|personal projects|key projects",
    "certifications": r"certifications|certificates|licenses|licences|licenses & certifications",
    "languages": r"languages",
    "awards": r"awards|honors|honours|achievements",
    "interests": r"interests|hobbies",
}
HEADING_RE = {k: re.compile(rf"^\s*({v})\s*:?\s*$", re.I) for k, v in SECTION_HEADINGS.items()}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
URL_RE = re.compile(r"(https?://)?(www\.)?(linkedin\.com/in/[\w-]+|github\.com/[\w-]+)/?", re.I)

DEGREE_RE = re.compile(
    r"\b(b\.?\s?s\.?c?|b\.?\s?a|b\.?\s?tech|b\.?\s?e|m\.?\s?s\.?c?|m\.?\s?a|m\.?\s?tech|mba|mbbs|md|ph\.?\s?d|"
    r"bachelor|master|diploma|degree|doctor of|associate of|high school|hsc|ssc)(\b|\.)", re.I)

EXPERIENCE_SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {
    "type": "object", "properties": {
        "title": {"type": "string"}, "company": {"type": "string"}, "location": {"type": "string"},
        "start": {"type": "string"}, "end": {"type": "string"}, "bullets": STR_LIST},
    "required": ["title", "company", "start", "end", "bullets"]}}}, "required": ["items"]}
EDUCATION_SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {
    "type": "object", "properties": {
        "degree": {"type": "string"}, "institution": {"type": "string"},
        "start": {"type": "string"}, "end": {"type": "string"}, "grade": {"type": "string"}},
    "required": ["degree", "institution", "end"]}}}, "required": ["items"]}
PROJECT_SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {
    "type": "object", "properties": {
        "name": {"type": "string"}, "description": {"type": "string"}, "bullets": STR_LIST},
    "required": ["name", "bullets"]}}}, "required": ["items"]}


def _sid() -> str:
    return uuid.uuid4().hex[:8]


def split_sections(text: str) -> tuple[list[str], dict[str, str]]:
    """Return (header lines before the first heading, {section: body})."""
    header: list[str] = []
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        matched = next((k for k, rx in HEADING_RE.items() if len(stripped) < 45 and rx.match(stripped)), None)
        if matched:
            current = matched
            sections.setdefault(current, [])
            continue
        if current is None:
            header.append(line)
        else:
            sections[current].append(line)
    return header, {k: "\n".join(v).strip() for k, v in sections.items()}


def _list_items(body: str) -> list[str]:
    parts = re.split(r"[,;•|\n]", body)
    return [re.sub(r"^\s*[-*▪●]\s*", "", p).strip() for p in parts if p.strip() and len(p.strip()) < 80]


def _contact(header: list[str], text: str) -> dict:
    top = "\n".join(header) if header else "\n".join(text.splitlines()[:6])
    personal = {k: "" for k in ("full_name", "headline", "email", "phone", "location", "linkedin", "website", "github")}
    if m := EMAIL_RE.search(top) or EMAIL_RE.search(text):
        personal["email"] = m.group(0)
    if m := PHONE_RE.search(top):
        personal["phone"] = m.group(0).strip()
    for m in URL_RE.finditer(text):
        key = "linkedin" if "linkedin" in m.group(0).lower() else "github"
        personal[key] = personal[key] or m.group(0)
    lines = [ln.strip() for ln in top.splitlines() if ln.strip()]
    if lines:
        first = re.split(r"[|,]", lines[0])[0].strip()
        if not EMAIL_RE.search(first) and len(first.split()) <= 5:
            personal["full_name"] = first
    # Location: a short chunk on a contact line that isn't email/phone/url
    for ln in lines[:4]:
        for chunk in re.split(r"[|•·]", ln):
            chunk = chunk.strip()
            if (chunk and chunk != personal["full_name"] and not EMAIL_RE.search(chunk)
                    and not PHONE_RE.search(chunk) and "http" not in chunk and "linkedin" not in chunk.lower()
                    and len(chunk.split()) <= 4 and len(lines) > 1):
                personal["location"] = personal["location"] or chunk
    if len(lines) > 1 and not EMAIL_RE.search(lines[1]) and not PHONE_RE.search(lines[1]) and len(lines[1].split()) <= 10:
        personal["headline"] = lines[1]
        if personal["location"] == lines[1]:
            personal["location"] = ""
    return personal


async def _llm_items(section: str, body: str, schema: dict, hint: str) -> list[dict]:
    if not body.strip():
        return []
    prompt = (f"Here is the {section.upper()} section of a resume. {hint} Copy text faithfully; "
              f"do not invent anything. Use 'Present' for current roles.\n\"\"\"\n{_clip(body, 4000)}\n\"\"\"")
    try:
        out = await llm.complete_json("You are a precise resume parser that outputs JSON only.", prompt, schema,
                                      temperature=0)
    except Exception:  # noqa: BLE001 — fall back to whatever we can keep
        return []
    return [i for i in out.get("items") or [] if isinstance(i, dict)]


async def parse_resume_text(text: str) -> dict:
    header, sections = split_sections(text)
    if len(sections) < 2:
        # No recognisable headings: treat the whole document as experience + education
        sections = {"experience": text, "education": text}

    personal = _contact(header, text)
    exp_items = await _llm_items("experience", sections.get("experience", ""), EXPERIENCE_SCHEMA,
                                 "List each job with title, company, location, start, end and bullet points.")
    edu_items = await _llm_items("education", sections.get("education", ""), EDUCATION_SCHEMA,
                                 "List each degree with institution, start, end and grade.")
    proj_items = await _llm_items("projects", sections.get("projects", ""), PROJECT_SCHEMA,
                                  "List each project with a name, short description and bullet points.")

    experience = []
    for e in exp_items:
        end = str(e.get("end", ""))
        experience.append({
            "id": _sid(), "title": str(e.get("title", "")), "company": str(e.get("company", "")),
            "location": str(e.get("location", "")), "start": str(e.get("start", "")),
            "end": "" if end.lower() == "present" else end, "current": end.lower() == "present",
            "bullets": [str(b).lstrip("-•* ") for b in e.get("bullets") or []][:15],
        })
    education = [{"id": _sid(), "degree": str(e.get("degree", "")), "institution": str(e.get("institution", "")),
                  "location": "", "start": str(e.get("start", "")), "end": str(e.get("end", "")),
                  "grade": str(e.get("grade", "")), "details": ""}
                 for e in edu_items if e.get("degree") or e.get("institution")]
    # Small models sometimes file degrees under experience — move them back
    for e in list(experience):
        if DEGREE_RE.search(e["title"]) and not e["bullets"]:
            experience.remove(e)
            if not any(ed["degree"] == e["title"] for ed in education):
                education.append({"id": _sid(), "degree": e["title"], "institution": e["company"], "location": "",
                                  "start": "", "end": e["end"] or e["start"], "grade": "", "details": ""})

    skills = _list_items(sections.get("skills", ""))
    return {
        "personal": personal,
        "summary": re.sub(r"\s+", " ", sections.get("summary", "")).strip()[:3000],
        "experience": experience,
        "education": education,
        "skills": [{"id": _sid(), "name": "Skills", "items": skills[:40]}] if skills else [],
        "projects": [{"id": _sid(), "name": str(p.get("name", "")), "role": "", "link": "",
                      "description": str(p.get("description", "")),
                      "bullets": [str(b) for b in p.get("bullets") or []][:10]} for p in proj_items],
        "certifications": [{"id": _sid(), "name": c, "issuer": "", "date": "", "detail": "", "link": ""}
                           for c in _list_items(sections.get("certifications", ""))[:20]],
        "awards": [{"id": _sid(), "name": c, "issuer": "", "date": "", "detail": "", "link": ""}
                   for c in _list_items(sections.get("awards", ""))[:20]],
        "languages": [{"id": _sid(), "name": lang, "level": ""}
                      for lang in _list_items(sections.get("languages", ""))[:10]],
        "interests": _list_items(sections.get("interests", ""))[:15],
    }


# ── ATS AI tips, cover letter, match analysis ───────────────────────────────

async def ats_ai_tips(resume_text: str, jd: str | None, ats_result: dict) -> list[str]:
    weak = [f"{b['label']}: {'; '.join(b['findings'][:2])}" for b in ats_result["breakdown"] if b["status"] != "good"]
    prompt = (
        f"ATS scan score: {ats_result['score']}/100. Weak areas:\n" + "\n".join(weak[:6]) +
        (f"\n\nJob description:\n{_clip(jd, 1500)}" if jd else "") +
        f"\n\nResume:\n{_clip(resume_text, 2500)}\n\n"
        "Give 3-5 specific, actionable improvements (each one sentence, reference actual content from the resume)."
    )
    schema = {"type": "object", "properties": {"tips": STR_LIST}, "required": ["tips"]}
    out = await llm.complete_json(WRITER_SYSTEM, prompt, schema, temperature=0.4)
    return [str(t) for t in out.get("tips", []) if t][:5]


async def generate_cover_letter(job_title: str, company: str, job_description: str, resume_text: str,
                                user_name: str, country: str | None = None, tone: str = "professional") -> str:
    rules = get_country(country)
    prompt = (
        f"Write a {tone} cover letter for {user_name} applying to '{job_title}' at {company}.\n"
        f"Country conventions: {rules['name']}.\n\nJob description:\n{_clip(job_description, 2500)}\n\n"
        f"Candidate background:\n{_clip(resume_text, 2500)}\n\n"
        "3-4 short paragraphs, under 350 words: a specific hook, 2-3 achievements mapped to the job's needs, "
        "why this company, and a confident call to action. No placeholders for the address block. "
        "Return only the letter text."
    )
    return await llm.complete("You are an expert cover letter writer.", prompt, temperature=0.6)


async def analyze_job_match(job_description: str, resume_text: str) -> dict:
    prompt = (
        f"Job Description:\n{_clip(job_description, 2500)}\n\nResume:\n{_clip(resume_text, 2500)}\n\n"
        "Assess how well the resume matches the job. Score 0-100, list 3-5 strengths, 2-4 gaps "
        "and 2-3 actionable suggestions."
    )
    schema = {"type": "object", "properties": {"score": {"type": "number"}, "strengths": STR_LIST,
                                                "gaps": STR_LIST, "suggestions": STR_LIST},
              "required": ["score", "strengths", "gaps", "suggestions"]}
    out = await llm.complete_json("You are a professional recruiter and career coach.", prompt, schema)
    try:
        score = float(out.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0
    return {
        "score": max(0.0, min(100.0, score)),
        "strengths": [str(s) for s in out.get("strengths", [])][:5],
        "gaps": [str(s) for s in out.get("gaps", [])][:4],
        "suggestions": [str(s) for s in out.get("suggestions", [])][:3],
    }
