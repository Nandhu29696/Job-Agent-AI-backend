"""
Country resume conventions and job-category section layouts.

These drive the resume editor (which personal fields to show, paper size,
section order), the ATS/compliance checker and the AI tailoring prompts.
"""

# Personal fields that may appear in `personal`:
# photo, date_of_birth, nationality, marital_status, gender, visa_status
COUNTRIES: dict[str, dict] = {
    "US": {
        "name": "United States", "document_name": "Resume", "paper": "letter",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "forbidden", "personal_allowed": [],
        "personal_forbidden": ["photo", "date_of_birth", "marital_status", "gender", "nationality"],
        "section_order": ["summary", "experience", "skills", "education", "projects", "certifications"],
        "tips": [
            "Keep it to 1 page under 10 years of experience, 2 pages max otherwise.",
            "Never include a photo, age, date of birth, or marital status (anti-discrimination laws).",
            "Lead bullets with strong action verbs and quantify results ($, %, time saved).",
            "Use US Letter paper size and American spelling.",
        ],
    },
    "CA": {
        "name": "Canada", "document_name": "Resume", "paper": "letter",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "forbidden", "personal_allowed": [],
        "personal_forbidden": ["photo", "date_of_birth", "marital_status", "gender"],
        "section_order": ["summary", "experience", "skills", "education", "certifications", "volunteer"],
        "tips": [
            "Similar to the US: no photo or personal details.",
            "Volunteer experience is valued — include it.",
            "Mention work authorisation status if you are not a citizen/PR.",
        ],
    },
    "UK": {
        "name": "United Kingdom", "document_name": "CV", "paper": "a4",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "discouraged", "personal_allowed": ["visa_status"],
        "personal_forbidden": ["photo", "date_of_birth", "marital_status", "gender"],
        "section_order": ["summary", "experience", "education", "skills", "certifications", "interests"],
        "tips": [
            "Call it a CV; 2 pages of A4 is the norm.",
            "Open with a 3-4 line personal statement.",
            "Do not include a photo or date of birth (Equality Act 2010).",
            "Use British spelling (e.g. 'organised', 'optimised').",
        ],
    },
    "DE": {
        "name": "Germany", "document_name": "Lebenslauf (CV)", "paper": "a4",
        "max_pages": 2, "date_format": "MM/YYYY",
        "photo": "common", "personal_allowed": ["photo", "date_of_birth", "nationality", "marital_status"],
        "personal_forbidden": [],
        "section_order": ["experience", "education", "skills", "languages", "certifications", "interests"],
        "tips": [
            "A professional photo is common (but optional since the AGG law).",
            "Tabular, strictly reverse-chronological layout with MM/YYYY dates.",
            "List language levels using CEFR (A1–C2).",
            "Traditionally ends with place, date and signature.",
        ],
    },
    "FR": {
        "name": "France", "document_name": "CV", "paper": "a4",
        "max_pages": 1, "date_format": "MM/YYYY",
        "photo": "common", "personal_allowed": ["photo", "date_of_birth", "nationality"],
        "personal_forbidden": [],
        "section_order": ["summary", "experience", "education", "skills", "languages", "interests"],
        "tips": [
            "One page is preferred, especially for junior profiles.",
            "A photo is common but optional.",
            "Include a short 'Centres d'intérêt' (interests) section.",
        ],
    },
    "NL": {
        "name": "Netherlands", "document_name": "CV", "paper": "a4",
        "max_pages": 2, "date_format": "MM/YYYY",
        "photo": "optional", "personal_allowed": ["photo", "date_of_birth", "nationality"],
        "personal_forbidden": [],
        "section_order": ["summary", "experience", "education", "skills", "languages"],
        "tips": ["Be direct and concise.", "Language skills are highly relevant."],
    },
    "EU": {
        "name": "Europass (EU)", "document_name": "Europass CV", "paper": "a4",
        "max_pages": 3, "date_format": "DD/MM/YYYY",
        "photo": "optional", "personal_allowed": ["photo", "date_of_birth", "nationality", "gender"],
        "personal_forbidden": [],
        "section_order": ["summary", "experience", "education", "languages", "skills", "certifications"],
        "tips": [
            "Use the Europass structure for EU institutions and cross-border applications.",
            "Self-assess languages with the CEFR grid.",
        ],
    },
    "IN": {
        "name": "India", "document_name": "CV / Resume", "paper": "a4",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "optional", "personal_allowed": ["photo", "date_of_birth", "nationality", "marital_status", "gender"],
        "personal_forbidden": [],
        "section_order": ["summary", "skills", "experience", "projects", "education", "certifications", "declaration"],
        "tips": [
            "Freshers should put Education and Projects before Experience.",
            "Personal details (DOB, nationality) are optional — omit for MNCs.",
            "A short declaration at the end is common for government/PSU roles.",
            "Mention notice period and current location.",
        ],
    },
    "AE": {
        "name": "UAE / Gulf (GCC)", "document_name": "CV", "paper": "a4",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "expected", "personal_allowed": ["photo", "date_of_birth", "nationality", "marital_status", "visa_status"],
        "personal_forbidden": [],
        "section_order": ["summary", "experience", "skills", "education", "certifications", "languages"],
        "tips": [
            "A professional photo is expected.",
            "State nationality and visa status (e.g. 'Visit visa', 'Employment visa — transferable').",
            "Mention driving licence and Gulf experience if any.",
        ],
    },
    "SA": {
        "name": "Saudi Arabia", "document_name": "CV", "paper": "a4",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "expected", "personal_allowed": ["photo", "date_of_birth", "nationality", "marital_status", "visa_status"],
        "personal_forbidden": [],
        "section_order": ["summary", "experience", "education", "skills", "certifications", "languages"],
        "tips": ["Photo and nationality are expected.", "Include Iqama/visa status if in-country."],
    },
    "AU": {
        "name": "Australia", "document_name": "Resume", "paper": "a4",
        "max_pages": 3, "date_format": "MMM YYYY",
        "photo": "forbidden", "personal_allowed": ["visa_status"],
        "personal_forbidden": ["photo", "date_of_birth", "marital_status", "gender"],
        "section_order": ["summary", "skills", "experience", "education", "certifications", "references"],
        "tips": [
            "2–3 pages is acceptable.",
            "Include work rights / visa status.",
            "Referees section (or 'available on request') is customary.",
        ],
    },
    "SG": {
        "name": "Singapore", "document_name": "Resume", "paper": "a4",
        "max_pages": 2, "date_format": "MMM YYYY",
        "photo": "optional", "personal_allowed": ["nationality", "visa_status"],
        "personal_forbidden": ["marital_status"],
        "section_order": ["summary", "experience", "skills", "education", "certifications"],
        "tips": ["State nationality / pass type (EP, S Pass, PR).", "Expected salary is often requested."],
    },
    "JP": {
        "name": "Japan", "document_name": "Rirekisho / Shokumu-keirekisho", "paper": "a4",
        "max_pages": 2, "date_format": "YYYY/MM",
        "photo": "expected", "personal_allowed": ["photo", "date_of_birth", "gender", "nationality"],
        "personal_forbidden": [],
        "section_order": ["education", "experience", "certifications", "skills", "summary"],
        "tips": [
            "A formal photo is expected on the rirekisho.",
            "Chronological order (oldest first) for education/work history is traditional.",
            "Include a self-PR (summary) and motivation.",
        ],
    },
}

CATEGORIES: dict[str, dict] = {
    "it": {
        "name": "IT & Software",
        "section_order": ["summary", "skills", "experience", "projects", "education", "certifications"],
        "extra_sections": ["projects", "certifications"],
        "keywords_hint": "programming languages, frameworks, cloud, CI/CD, system design",
    },
    "healthcare": {
        "name": "Doctor & Healthcare",
        "section_order": ["summary", "licenses", "experience", "education", "certifications", "publications", "awards"],
        "extra_sections": ["licenses", "publications", "awards"],
        "keywords_hint": "medical registration, specialty, clinical rotations, patient care, research",
    },
    "engineering": {
        "name": "Engineering (Mech / Civil / Electrical)",
        "section_order": ["summary", "skills", "experience", "projects", "education", "certifications", "licenses"],
        "extra_sections": ["projects", "licenses"],
        "keywords_hint": "CAD tools, standards (ISO/ASME), project scale, safety, PE/CEng licences",
    },
    "finance": {
        "name": "Finance & Accounting",
        "section_order": ["summary", "experience", "skills", "education", "certifications"],
        "extra_sections": ["certifications"],
        "keywords_hint": "CA/CPA/CFA, financial modelling, audit, IFRS/GAAP, ERP systems",
    },
    "education": {
        "name": "Teaching & Academia",
        "section_order": ["summary", "education", "experience", "publications", "awards", "skills"],
        "extra_sections": ["publications", "awards"],
        "keywords_hint": "curriculum, pedagogy, research, grants, student outcomes",
    },
    "sales": {
        "name": "Sales & Marketing",
        "section_order": ["summary", "experience", "skills", "awards", "education"],
        "extra_sections": ["awards"],
        "keywords_hint": "quota attainment, revenue growth, CRM, campaigns, ROI",
    },
    "creative": {
        "name": "Design & Creative",
        "section_order": ["summary", "projects", "experience", "skills", "education", "awards"],
        "extra_sections": ["projects", "awards"],
        "keywords_hint": "portfolio, tools (Figma, Adobe), brand, UX research",
    },
    "legal": {
        "name": "Legal",
        "section_order": ["summary", "licenses", "experience", "education", "publications", "skills"],
        "extra_sections": ["licenses", "publications"],
        "keywords_hint": "bar admission, practice areas, litigation, contracts, compliance",
    },
    "hospitality": {
        "name": "Hospitality & Retail",
        "section_order": ["summary", "experience", "skills", "languages", "education", "certifications"],
        "extra_sections": ["languages"],
        "keywords_hint": "guest experience, POS, inventory, food safety, team leadership",
    },
    "general": {
        "name": "General / Fresher",
        "section_order": ["summary", "education", "skills", "projects", "experience", "certifications"],
        "extra_sections": ["projects"],
        "keywords_hint": "transferable skills, internships, academic projects",
    },
}


def get_country(code: str | None) -> dict:
    return COUNTRIES.get((code or "US").upper(), COUNTRIES["US"])


def get_category(code: str | None) -> dict:
    return CATEGORIES.get((code or "general").lower(), CATEGORIES["general"])
