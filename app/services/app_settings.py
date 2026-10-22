"""Runtime-editable settings (super admin) with .env defaults."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.system import AppSetting

# key -> (type, default)
DEFINITIONS: dict[str, tuple[type, object]] = {
    "pro_plan_price_paise": (int, settings.pro_plan_price_paise),
    "pro_plan_days": (int, settings.pro_plan_days),
    "free_daily_ai_limit": (int, settings.free_daily_ai_limit),
    "registration_open": (bool, True),
    "maintenance_banner": (str, ""),
}


def _cast(kind: type, raw: str):
    if kind is bool:
        return raw.lower() in ("1", "true", "yes", "on")
    return kind(raw)


async def get_all(db: AsyncSession) -> dict:
    rows = (await db.execute(select(AppSetting))).scalars().all()
    stored = {r.key: r.value for r in rows}
    out = {}
    for key, (kind, default) in DEFINITIONS.items():
        out[key] = _cast(kind, stored[key]) if key in stored else default
    return out


async def get_value(db: AsyncSession, key: str):
    kind, default = DEFINITIONS[key]
    row = await db.get(AppSetting, key)
    return _cast(kind, row.value) if row else default


async def set_values(db: AsyncSession, values: dict) -> dict:
    for key, value in values.items():
        if key not in DEFINITIONS:
            continue
        kind, _ = DEFINITIONS[key]
        value = _cast(kind, str(value))  # validates type
        row = await db.get(AppSetting, key)
        if row:
            row.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value)))
    await db.flush()
    return await get_all(db)
