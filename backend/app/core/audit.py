"""Audit log helper — registra ações sensíveis para conformidade."""
import logging
import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AuditLog

logger = logging.getLogger(__name__)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def log_action(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    payload: dict | None = None,
    request: Request | None = None,
) -> None:
    """Best-effort audit log entry. Errors são logados mas nunca propagam."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=_client_ip(request),
        )
        db.add(entry)
        await db.commit()
    except Exception:
        logger.exception("Failed to write audit log: %s", action)
        try:
            await db.rollback()
        except Exception:
            pass
