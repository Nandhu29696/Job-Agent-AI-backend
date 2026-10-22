from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AuditLog


def client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


async def audit(
    db: AsyncSession,
    action: str,
    user_id: int | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    detail: dict | None = None,
    request: Request | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            detail=detail,
            ip=client_ip(request),
        )
    )
    await db.flush()
