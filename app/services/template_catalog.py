"""
Built-in resume template catalog. Seeded on startup (insert-only by slug, so
super admin edits to price/premium/active are never overwritten).

`layout` is consumed by the frontend renderer:
  layout:   classic | minimal | band | sidebar | split | executive | compact | timeline | academic | creative
  primary:  main colour, accent: secondary colour
  font:     sans | serif | mono-accent
  photo:    whether the layout reserves a photo slot
  heading:  underline | caps | bar | pill
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import ResumeTemplate


def _t(slug, name, category, style, layout, primary, accent, font="sans", photo=False,
       heading="underline", premium=False, price=0, description=""):
    return {
        "slug": slug, "name": name, "category": category, "style": style,
        "description": description, "is_premium": premium, "price_paise": price * 100,
        "layout": {"layout": layout, "primary": primary, "accent": accent,
                   "font": font, "photo": photo, "heading": heading},
    }


CATALOG = [
    # ── 10 FREE common templates (ATS-safe) ─────────────────────────────────
    _t("ats-classic", "ATS Classic", "general", "classic", "classic", "#111827", "#374151",
       font="serif", heading="underline",
       description="Single-column, parser-friendly layout that works for any industry."),
    _t("clean-minimal", "Clean Minimal", "general", "minimal", "minimal", "#0f172a", "#64748b",
       heading="caps", description="Lots of whitespace and crisp typography."),
    _t("modern-blue", "Modern Blue", "it", "modern", "band", "#1d4ed8", "#3b82f6",
       heading="bar", description="Bold colour header — popular for tech roles."),
    _t("professional-navy", "Professional Navy", "finance", "professional", "executive", "#1e3a5f", "#c9a227",
       heading="underline", description="Conservative and polished for corporate roles."),
    _t("tech-sidebar", "Tech Sidebar", "it", "modern", "sidebar", "#0f766e", "#14b8a6",
       heading="caps", description="Skills sidebar to surface your tech stack."),
    _t("medical-cv", "Medical CV", "healthcare", "academic", "academic", "#0e7490", "#0891b2",
       font="serif", heading="underline", description="Structured CV for doctors, nurses and clinicians."),
    _t("engineer-pro", "Engineer Pro", "engineering", "professional", "split", "#334155", "#f59e0b",
       heading="bar", description="Two-column layout highlighting projects and tools."),
    _t("fresher-start", "Fresher Start", "general", "modern", "compact", "#7c3aed", "#a78bfa",
       heading="pill", description="Education-first layout for students and graduates."),
    _t("educator", "Educator", "education", "classic", "classic", "#14532d", "#16a34a",
       font="serif", heading="caps", description="Clean classic layout for teachers and trainers."),
    _t("sales-impact", "Sales Impact", "sales", "modern", "band", "#b91c1c", "#ef4444",
       heading="bar", description="Make your numbers pop for sales & marketing."),

    # ── PREMIUM templates ───────────────────────────────────────────────────
    _t("executive-gold", "Executive Gold", "finance", "executive", "executive", "#111827", "#b8860b",
       font="serif", heading="caps", premium=True, price=149,
       description="Boardroom-ready design for senior leaders."),
    _t("doctor-elite", "Doctor Elite", "healthcare", "professional", "sidebar", "#075985", "#38bdf8",
       photo=True, heading="caps", premium=True, price=99,
       description="Photo sidebar with licences & registrations up front."),
    _t("senior-consultant", "Senior Consultant", "healthcare", "academic", "academic", "#4c1d95", "#7c3aed",
       font="serif", heading="underline", premium=True, price=99,
       description="Detailed CV for consultants with publications & research."),
    _t("dev-timeline", "Developer Timeline", "it", "modern", "timeline", "#0f172a", "#22d3ee",
       heading="bar", premium=True, price=79, description="Career timeline with tech-stack chips."),
    _t("cloud-architect", "Cloud Architect", "it", "professional", "split", "#1e293b", "#6366f1",
       heading="pill", premium=True, price=99, description="Dark-accent two-column for senior engineers."),
    _t("creative-studio", "Creative Studio", "creative", "creative", "creative", "#be185d", "#f472b6",
       photo=True, heading="pill", premium=True, price=129, description="Expressive layout for designers."),
    _t("designer-portfolio", "Designer Portfolio", "creative", "modern", "sidebar", "#18181b", "#f97316",
       photo=True, heading="caps", premium=True, price=99, description="Portfolio links and projects first."),
    _t("structural", "Structural", "engineering", "modern", "timeline", "#78350f", "#f59e0b",
       heading="bar", premium=True, price=79, description="Timeline layout for civil & mechanical engineers."),
    _t("legal-counsel", "Legal Counsel", "legal", "executive", "executive", "#1c1917", "#78716c",
       font="serif", heading="underline", premium=True, price=99,
       description="Refined serif design for lawyers."),
    _t("gulf-pro", "Gulf Pro", "general", "professional", "sidebar", "#14532d", "#ca8a04",
       photo=True, heading="caps", premium=True, price=79,
       description="Photo + nationality/visa fields for GCC applications."),
    _t("euro-modern", "Euro Modern", "general", "modern", "band", "#1e40af", "#facc15",
       photo=True, heading="bar", premium=True, price=79, description="Europe-style CV with photo header."),
    _t("hospitality-star", "Hospitality Star", "hospitality", "creative", "creative", "#9a3412", "#fb923c",
       photo=True, heading="pill", premium=True, price=49, description="Warm, friendly layout for service roles."),
    _t("professor-cv", "Professor CV", "education", "academic", "academic", "#312e81", "#6366f1",
       font="serif", heading="caps", premium=True, price=79,
       description="Academic CV with publications, grants and teaching."),
    _t("marketing-bold", "Marketing Bold", "sales", "creative", "creative", "#5b21b6", "#22c55e",
       heading="pill", premium=True, price=99, description="High-contrast layout for growth marketers."),
]


async def seed_templates(db: AsyncSession) -> int:
    existing = set((await db.execute(select(ResumeTemplate.slug))).scalars().all())
    added = 0
    for order, item in enumerate(CATALOG):
        if item["slug"] in existing:
            continue
        db.add(ResumeTemplate(**item, sort_order=order, is_active=True))
        added += 1
    if added:
        await db.commit()
    return added
