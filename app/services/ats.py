"""
Deterministic ATS (Applicant Tracking System) friendliness scoring.

Scores a structured resume (or plain text) out of 100 across weighted checks,
optionally against a job description for keyword coverage, and against the
target country's conventions. Pure Python — fast, explainable and consistent,
so it works well even when the local LLM is small.
"""
import re
from collections import Counter

from app.services.resume_rules import get_country

ACTION_VERBS = {
    "achieved", "accelerated", "administered", "analyzed", "analysed", "architected", "automated",
    "built", "collaborated", "configured", "consolidated", "coordinated", "created", "cut", "decreased",
    "delivered", "deployed", "designed", "developed", "diagnosed", "directed", "drove", "enabled",
    "engineered", "established", "executed", "expanded", "facilitated", "generated", "grew", "guided",
    "headed", "implemented", "improved", "increased", "initiated", "integrated", "introduced", "launched",
    "led", "maintained", "managed", "mentored", "migrated", "modernized", "monitored", "negotiated",
    "optimized", "optimised", "orchestrated", "organized", "organised", "oversaw", "performed", "pioneered",
    "planned", "presented", "produced", "published", "reduced", "redesigned", "refactored", "resolved",
    "restructured", "revamped", "saved", "scaled", "secured", "simplified", "spearheaded", "streamlined",
    "supervised", "taught", "tested", "trained", "transformed", "treated", "won", "wrote", "conducted",
    "assessed", "authored", "championed", "closed", "earned", "exceeded", "founded", "handled", "boosted",
}

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included", "tasked with",
    "involved in", "assisted with", "in charge of", "participated in",
]

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each etc few for from further had has have
having he her here hers herself him himself his how i if in into is it its itself just let me more most
must my myself no nor not now of off on once only or other our ours ourselves out over own per same she
should so some such than that the their theirs them themselves then there these they this those through
to too under until up upon us very via was we were what when where which while who whom why will with
within without would you your yours yourself yourselves
""".split())

GENERIC_JOB_WORDS = set("""
ability able work working team teams job role candidate candidates experience experienced year years
strong excellent good great skills skill knowledge required requirements preferred plus including include
responsibilities responsible looking join company opportunity environment using use based new etc
well within across ensure provide support help day days time full part position apply applicants must
minimum least ideal ideally will would like we our you your us they best high highly level levels other
related relevant equivalent understanding demonstrated proven track record familiarity hands
senior junior need needs haves mid entry
""".split())

NUMBER_RE = re.compile(r"(\d+[\d,.]*\s?(%|\+|x|k|m|b|cr|lakh|lakhs|crore)?|\$\s?\d|₹\s?\d|€\s?\d|£\s?\d)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#./-]*[a-zA-Z0-9+#]|[a-zA-Z]")


# ── Text helpers ─────────────────────────────────────────────────────────────

def resume_to_text(data: dict) -> str:
    """Flatten structured resume JSON into plain text (what an ATS would read)."""
    p = data.get("personal") or {}
    parts = [p.get("full_name", ""), p.get("headline", ""), p.get("email", ""), p.get("phone", ""),
             p.get("location", ""), p.get("linkedin", ""), p.get("website", ""), p.get("github", "")]
    if data.get("summary"):
        parts += ["SUMMARY", data["summary"]]
    if data.get("experience"):
        parts.append("EXPERIENCE")
        for e in data["experience"]:
            parts.append(f"{e.get('title', '')} {e.get('company', '')} {e.get('location', '')} "
                         f"{e.get('start', '')} {e.get('end', '') or ('Present' if e.get('current') else '')}")
            parts += e.get("bullets") or []
    if data.get("education"):
        parts.append("EDUCATION")
        for ed in data["education"]:
            parts.append(f"{ed.get('degree', '')} {ed.get('institution', '')} {ed.get('end', '')} "
                         f"{ed.get('grade', '')} {ed.get('details', '')}")
    if data.get("skills"):
        parts.append("SKILLS")
        for g in data["skills"]:
            parts.append(f"{g.get('name', '')}: {', '.join(g.get('items') or [])}")
    if data.get("projects"):
        parts.append("PROJECTS")
        for pr in data["projects"]:
            parts.append(f"{pr.get('name', '')} {pr.get('role', '')} {pr.get('description', '')}")
            parts += pr.get("bullets") or []
    for key in ("certifications", "licenses", "publications", "awards", "volunteer"):
        if data.get(key):
            parts.append(key.upper())
            for it in data[key]:
                parts.append(f"{it.get('name', '')} {it.get('issuer', '')} {it.get('date', '')} {it.get('detail', '')}")
    if data.get("languages"):
        parts.append("LANGUAGES")
        parts.append(", ".join(f"{lang.get('name', '')} {lang.get('level', '')}" for lang in data["languages"]))
    for cs in data.get("custom_sections") or []:
        parts.append(cs.get("title", "").upper())
        parts += cs.get("items") or []
    return "\n".join(x for x in parts if x and x.strip())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def extract_keywords(job_description: str, limit: int = 30) -> list[str]:
    """Pick the most significant single words and two-word phrases from a JD."""
    text = job_description or ""
    tokens = [t.lower().strip("./-") for t in TOKEN_RE.findall(text)]
    tokens = [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]

    uni = Counter(t for t in tokens if t not in GENERIC_JOB_WORDS and not t.isdigit())
    bi = Counter(
        f"{a} {b}" for a, b in zip(tokens, tokens[1:])
        if a not in GENERIC_JOB_WORDS and b not in GENERIC_JOB_WORDS
    )
    # Tech-looking tokens (c++, node.js, c#) and Capitalised terms get a boost
    caps = {m.lower() for m in re.findall(r"\b[A-Z][A-Za-z0-9+#.]{1,}\b", text)}
    scored: dict[str, float] = {}
    for word, count in uni.items():
        boost = 1.5 if (word in caps or re.search(r"[+#.]", word)) else 1.0
        if len(word) <= 2 and word not in caps:
            continue
        scored[word] = count * boost
    for phrase, count in bi.items():
        if count >= 2:
            scored[phrase] = count * 1.8

    ranked = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    keywords: list[str] = []
    for word, _ in ranked:
        # Skip unigrams already covered by a chosen phrase
        if any(word in k.split() for k in keywords if " " in k):
            continue
        keywords.append(word)
        if len(keywords) >= limit:
            break
    return keywords


def _contains(haystack: str, needle: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) is not None


def _bullets(data: dict) -> list[str]:
    out: list[str] = []
    for e in data.get("experience") or []:
        out += [b for b in (e.get("bullets") or []) if b.strip()]
    for p in data.get("projects") or []:
        out += [b for b in (p.get("bullets") or []) if b.strip()]
    return out


def _bullets_from_text(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    return [re.sub(r"^[-•*▪●◦·]\s*", "", ln) for ln in lines if re.match(r"^[-•*▪●◦·]\s+", ln)]


def _status(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0
    return "good" if ratio >= 0.8 else "warn" if ratio >= 0.5 else "bad"


# ── Main analysis ────────────────────────────────────────────────────────────

def analyze(data: dict | None = None, text: str | None = None, job_description: str | None = None,
            country: str | None = None) -> dict:
    structured = data is not None
    data = data or {}
    text = text if text is not None else resume_to_text(data)
    low = _norm(text)
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    bullets = _bullets(data) if structured else _bullets_from_text(text)
    rules = get_country(country)
    breakdown = []
    suggestions: list[str] = []

    # 1. Contact information (10)
    p = data.get("personal") or {}
    findings = []
    has_name = bool(p.get("full_name")) if structured else bool(text.strip())
    has_email = bool(p.get("email")) if structured else bool(EMAIL_RE.search(text))
    has_phone = bool(p.get("phone")) if structured else bool(PHONE_RE.search(text))
    has_location = bool(p.get("location")) if structured else True
    has_link = bool(p.get("linkedin") or p.get("website") or p.get("github")) if structured else (
        "linkedin" in low or "github" in low or "http" in low)
    score = (2 * has_name + 3 * has_email + 3 * has_phone + 1 * has_location + 1 * has_link)
    for ok, msg in [(has_name, "Add your full name"), (has_email, "Add a professional email address"),
                    (has_phone, "Add a phone number with country code"),
                    (has_location, "Add your city/country"), (has_link, "Add a LinkedIn or portfolio link")]:
        if not ok:
            findings.append(msg)
    breakdown.append({"key": "contact", "label": "Contact information", "score": score, "max": 10,
                      "status": _status(score, 10), "findings": findings or ["All key contact details present"]})

    # 2. Standard sections (15)
    findings = []
    if structured:
        present = {
            "summary": bool((data.get("summary") or "").strip()),
            "experience": bool(data.get("experience")),
            "education": bool(data.get("education")),
            "skills": any(g.get("items") for g in data.get("skills") or []),
        }
    else:
        present = {
            "summary": bool(re.search(r"\b(summary|profile|objective|about me)\b", low)),
            "experience": bool(re.search(r"\b(experience|employment|work history)\b", low)),
            "education": bool(re.search(r"\b(education|qualifications?|academic)\b", low)),
            "skills": bool(re.search(r"\b(skills|competencies|technologies)\b", low)),
        }
    weights = {"summary": 3, "experience": 5, "education": 3, "skills": 4}
    score = sum(weights[k] for k, v in present.items() if v)
    for k, v in present.items():
        if not v:
            findings.append(f"Missing a '{k.title()}' section — ATS parsers look for standard headings")
    breakdown.append({"key": "sections", "label": "Standard sections", "score": score, "max": 15,
                      "status": _status(score, 15), "findings": findings or ["All standard sections found"]})

    # 3. Keyword match (30)
    keywords = {"matched": [], "missing": [], "coverage": None}
    findings = []
    if job_description and job_description.strip():
        kws = extract_keywords(job_description)
        matched = [k for k in kws if _contains(low, k)]
        missing = [k for k in kws if k not in matched]
        coverage = len(matched) / len(kws) if kws else 0
        score = round(min(30, coverage * 30 / 0.75), 1)  # 75% coverage = full marks
        keywords = {"matched": matched, "missing": missing, "coverage": round(coverage * 100)}
        findings.append(f"{len(matched)} of {len(kws)} job keywords found ({round(coverage * 100)}%)")
        if missing:
            findings.append("Consider adding (if true): " + ", ".join(missing[:10]))
            suggestions.append("Mirror the job description's wording for skills you genuinely have — "
                               "ATS keyword matching is usually literal.")
    else:
        skill_count = sum(len(g.get("items") or []) for g in data.get("skills") or []) if structured else \
            len(re.findall(r",", text)) // 2
        score = round(min(30, 12 + skill_count * 1.2), 1)
        findings.append("No job description provided — paste one to get a keyword match score")
        if skill_count < 8:
            findings.append("List at least 8–15 relevant hard skills")
    breakdown.append({"key": "keywords", "label": "Keyword match", "score": score, "max": 30,
                      "status": _status(score, 30), "findings": findings})

    # 4. Impact & achievements (15)
    findings = []
    if bullets:
        quantified = sum(1 for b in bullets if NUMBER_RE.search(b))
        action = sum(1 for b in bullets if b.split()[0].lower().strip(",.") in ACTION_VERBS) if bullets else 0
        weak = [b for b in bullets if any(w in b.lower() for w in WEAK_PHRASES)]
        q_ratio, a_ratio = quantified / len(bullets), action / len(bullets)
        score = round(min(8, q_ratio * 8 / 0.5) + min(7, a_ratio * 7 / 0.7) - min(3, len(weak)), 1)
        score = max(0, score)
        findings.append(f"{round(q_ratio * 100)}% of bullets contain numbers (aim for 50%+)")
        findings.append(f"{round(a_ratio * 100)}% of bullets start with a strong action verb (aim for 70%+)")
        if weak:
            findings.append(f"{len(weak)} bullet(s) use weak phrasing like 'responsible for' / 'worked on'")
            suggestions.append("Replace 'responsible for…' with what you achieved: 'Led…', 'Reduced…', 'Built…'.")
        if q_ratio < 0.5:
            suggestions.append("Quantify impact: team size, % improvement, revenue, time saved, patients treated.")
    else:
        score = 0
        findings.append("No bullet points found — describe each role with 3–6 achievement bullets")
        quantified = 0
    breakdown.append({"key": "impact", "label": "Impact & achievements", "score": score, "max": 15,
                      "status": _status(score, 15), "findings": findings})

    # 5. Length & readability (10)
    findings = []
    est_pages = round(max(1, word_count / 450), 1)
    score = 10.0
    if word_count < 250:
        score -= 5
        findings.append(f"Only {word_count} words — too thin; expand on achievements")
    elif est_pages > rules["max_pages"] + 0.3:
        score -= 3
        findings.append(f"~{est_pages} pages — {rules['name']} norm is max {rules['max_pages']}")
    long_bullets = [b for b in bullets if len(b.split()) > 35]
    short_bullets = [b for b in bullets if len(b.split()) < 5]
    if long_bullets:
        score -= min(3, len(long_bullets))
        findings.append(f"{len(long_bullets)} bullet(s) over 35 words — split or tighten them")
    if short_bullets:
        score -= min(2, len(short_bullets))
        findings.append(f"{len(short_bullets)} bullet(s) under 5 words — add context and results")
    summary = (data.get("summary") or "") if structured else ""
    if structured and summary and not (25 <= len(summary.split()) <= 110):
        score -= 1
        findings.append("Keep the summary between ~30 and 100 words")
    score = max(0, score)
    breakdown.append({"key": "readability", "label": "Length & readability", "score": score, "max": 10,
                      "status": _status(score, 10),
                      "findings": findings or [f"{word_count} words (~{est_pages} page(s)) — good length"]})

    # 6. ATS parsing safety (10)
    findings = []
    score = 10.0
    if structured:
        undated = [e for e in data.get("experience") or [] if not e.get("start")]
        if undated:
            score -= 3
            findings.append(f"{len(undated)} role(s) missing dates — ATS uses dates to compute experience")
        no_title = [e for e in data.get("experience") or [] if not e.get("title") or not e.get("company")]
        if no_title:
            score -= 3
            findings.append("Every role needs a job title and company name")
        for cs in data.get("custom_sections") or []:
            if re.search(r"[^\w\s&/-]", cs.get("title", "")):
                score -= 1
                findings.append(f"Use plain heading text for '{cs.get('title')}' (avoid symbols/emoji)")
    else:
        if re.search(r"[☀-➿\U0001F300-\U0001FAFF]", text):
            score -= 3
            findings.append("Emoji/icons detected — many ATS parsers drop or garble them")
        if text.count("|") > 15:
            score -= 2
            findings.append("Heavy use of '|' suggests tables/columns, which can scramble parsing")
    if re.search(r"\b(references available upon request)\b", low):
        score -= 1
        findings.append("Drop 'References available upon request' — it wastes space")
    score = max(0, score)
    breakdown.append({"key": "parsing", "label": "ATS parsing safety", "score": score, "max": 10,
                      "status": _status(score, 10), "findings": findings or ["Structure is parser-friendly"]})

    # 7. Country compliance (10)
    findings = []
    score = 10.0
    if structured:
        for field in rules["personal_forbidden"]:
            if p.get(field):
                score -= 3 if field == "photo" else 2
                findings.append(f"Remove {field.replace('_', ' ')} — not expected/recommended in {rules['name']}")
        if rules["photo"] == "expected" and not p.get("photo"):
            score -= 2
            findings.append(f"A professional photo is expected in {rules['name']}")
        if "visa_status" in rules["personal_allowed"] and not p.get("visa_status"):
            findings.append("Consider stating your work authorisation / visa status")
            score -= 1
    score = max(0, score)
    breakdown.append({"key": "country", "label": f"{rules['name']} conventions", "score": score, "max": 10,
                      "status": _status(score, 10),
                      "findings": findings or [f"Follows {rules['name']} conventions"]})

    total = round(sum(b["score"] for b in breakdown))
    grade = "Excellent" if total >= 85 else "Good" if total >= 70 else "Fair" if total >= 50 else "Needs work"

    # Suggestions from the weakest areas first
    for b in sorted(breakdown, key=lambda x: x["score"] / x["max"]):
        if b["status"] != "good":
            for f in b["findings"]:
                if f not in suggestions and not f.endswith("present") and "found (" not in f:
                    suggestions.append(f)
    return {
        "score": total,
        "grade": grade,
        "breakdown": breakdown,
        "keywords": keywords,
        "suggestions": suggestions[:10],
        "stats": {
            "word_count": word_count,
            "bullet_count": len(bullets),
            "quantified_bullets": quantified,
            "estimated_pages": est_pages,
        },
        "country_tips": rules["tips"],
    }
