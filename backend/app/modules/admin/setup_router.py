"""Admin setup endpoints — clinic settings, Telegram webhook, integrations status."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.permissions import require_role
from app.database import get_db
from app.modules.admin.models import SystemConfig
from app.modules.auth.models import User
from app.modules.messaging.adapters.telegram import set_telegram_webhook

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class SetupStatus(BaseModel):
    telegram_configured: bool
    openai_configured: bool
    local_llm_configured: bool
    domain: str


class TelegramWebhookResult(BaseModel):
    success: bool
    webhook_url: str


class ClinicSettings(BaseModel):
    name: str = "Minha Clínica"
    timezone: str = "America/Sao_Paulo"
    phone: str = ""
    address: str = ""


class SLASettings(BaseModel):
    hours: int = 2


class AISettings(BaseModel):
    type: str = "openai"
    model: str = "gpt-4o-mini"


class AllSettings(BaseModel):
    clinic: ClinicSettings
    sla: SLASettings
    ai: AISettings


# --- Helpers ---


async def _get_config(db: AsyncSession, key: str) -> dict:
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else {}


async def _set_config(db: AsyncSession, key: str, value: dict, user_id=None) -> None:
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
        row.updated_by = user_id
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(SystemConfig(key=key, value=value, updated_by=user_id))
    await db.commit()


# --- Endpoints ---


@router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status(
    current_user: User = Depends(require_role("admin")),
):
    return SetupStatus(
        telegram_configured=bool(settings.TELEGRAM_BOT_TOKEN),
        openai_configured=bool(settings.OPENAI_API_KEY),
        local_llm_configured=bool(settings.LOCAL_LLM_BASE_URL),
        domain=settings.DOMAIN,
    )


@router.post("/setup/telegram-webhook", response_model=TelegramWebhookResult)
async def setup_telegram_webhook(
    current_user: User = Depends(require_role("admin")),
):
    """Register the Telegram webhook URL with Telegram's API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return TelegramWebhookResult(success=False, webhook_url="")

    scheme = "https" if settings.ENVIRONMENT == "production" else "http"
    webhook_url = (
        f"{scheme}://{settings.DOMAIN}/webhooks/telegram/{settings.TELEGRAM_BOT_TOKEN}"
    )

    success = await set_telegram_webhook(webhook_url)
    return TelegramWebhookResult(success=success, webhook_url=webhook_url)


@router.get("/settings", response_model=AllSettings)
async def get_all_settings(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    clinic_raw = await _get_config(db, "clinic_info")
    sla_raw = await _get_config(db, "sla")
    ai_raw = await _get_config(db, "ai_provider")

    return AllSettings(
        clinic=ClinicSettings(**clinic_raw) if clinic_raw else ClinicSettings(),
        sla=SLASettings(**sla_raw) if sla_raw else SLASettings(),
        ai=AISettings(**ai_raw) if ai_raw else AISettings(),
    )


@router.patch("/settings/clinic", response_model=ClinicSettings)
async def update_clinic_settings(
    payload: ClinicSettings,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "clinic_info", data, current_user.id)
    return payload


@router.patch("/settings/sla", response_model=SLASettings)
async def update_sla_settings(
    payload: SLASettings,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "sla", data, current_user.id)
    return payload


@router.patch("/settings/ai", response_model=AISettings)
async def update_ai_settings(
    payload: AISettings,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "ai_provider", data, current_user.id)
    return payload
