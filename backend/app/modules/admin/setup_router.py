"""Admin setup endpoints — Telegram webhook, integrations status."""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.core.permissions import require_role
from app.modules.auth.models import User
from app.modules.messaging.adapters.telegram import set_telegram_webhook

logger = logging.getLogger(__name__)

router = APIRouter()


class SetupStatus(BaseModel):
    telegram_configured: bool
    openai_configured: bool
    local_llm_configured: bool
    domain: str


class TelegramWebhookResult(BaseModel):
    success: bool
    webhook_url: str


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
