"""Admin setup endpoints — clinic settings, Telegram webhook, integrations status."""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.audit import log_action
from app.core.permissions import require_role
from app.database import get_db
from app.modules.admin.models import AuditLog, SystemConfig
from app.modules.auth.models import User
from app.modules.messaging.adapters.telegram import TelegramAdapter

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class SetupStatus(BaseModel):
    telegram_configured: bool
    openai_configured: bool
    local_llm_configured: bool
    whatsapp_configured: bool
    domain: str


class TelegramWebhookResult(BaseModel):
    success: bool
    webhook_url: str


class WhatsAppWebhookResult(BaseModel):
    success: bool
    webhook_url: str


class ClinicSettings(BaseModel):
    name: str = "Minha Clínica"
    timezone: str = "America/Sao_Paulo"
    phone: str = ""
    address: str = ""
    logo_url: str = ""


class SLASettings(BaseModel):
    hours: int = 2


class AISettings(BaseModel):
    type: str = "openai"
    model: str = "gpt-4o-mini"
    use_local_llm: bool = False
    local_llm_url: str = ""
    local_llm_model: str = ""


class ChatbotSettings(BaseModel):
    system_prompt: str = ""
    max_tool_calls: int = 3
    temperature: float = 0.3


class NotificationsSettings(BaseModel):
    sla_telegram_chat_id: str = ""
    escalation_telegram_chat_id: str = ""


class AllSettings(BaseModel):
    clinic: ClinicSettings
    sla: SLASettings
    ai: AISettings
    chatbot: ChatbotSettings
    notifications: NotificationsSettings


class TestChatRequest(BaseModel):
    message: str
    session_id: str  # UUID string — identifica a sessão de teste no Redis


class AuditLogResponse(BaseModel):
    id: int
    user_id: uuid.UUID | None
    action: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    payload: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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


@router.get("/branding")
async def get_branding(db: AsyncSession = Depends(get_db)):
    """Endpoint público — retorna nome e logo da clínica para exibição no header."""
    clinic_raw = await _get_config(db, "clinic_info")
    name = clinic_raw.get("name", "Open Clinic AI") if clinic_raw else "Open Clinic AI"
    logo_url = clinic_raw.get("logo_url", "") if clinic_raw else ""
    return {"name": name, "logo_url": logo_url}


@router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status(
    current_user: User = Depends(require_role("admin")),
):
    return SetupStatus(
        telegram_configured=bool(settings.TELEGRAM_BOT_TOKEN),
        openai_configured=bool(settings.OPENAI_API_KEY),
        local_llm_configured=bool(settings.LOCAL_LLM_BASE_URL),
        whatsapp_configured=bool(settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY and settings.EVOLUTION_INSTANCE_NAME),
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

    success = await TelegramAdapter().set_webhook(webhook_url)
    return TelegramWebhookResult(success=success, webhook_url=webhook_url)


@router.post("/setup/whatsapp-webhook", response_model=WhatsAppWebhookResult)
async def setup_whatsapp_webhook(
    current_user: User = Depends(require_role("admin")),
):
    """Register the WhatsApp webhook URL with Evolution API."""
    if not (settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY and settings.EVOLUTION_INSTANCE_NAME):
        return WhatsAppWebhookResult(success=False, webhook_url="")

    scheme = "https" if settings.ENVIRONMENT == "production" else "http"
    webhook_url = f"{scheme}://{settings.DOMAIN}/webhooks/whatsapp/{settings.EVOLUTION_API_KEY}"

    import httpx
    url = f"{settings.EVOLUTION_API_URL.rstrip('/')}/webhook/set/{settings.EVOLUTION_INSTANCE_NAME}"
    headers = {"apikey": settings.EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {
        "webhook": {
            "enabled": True,
            "url": webhook_url,
            "webhookByEvents": False,
            "webhookBase64": False,
            "events": ["MESSAGES_UPSERT"],
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(url, json=payload, headers=headers)
            success = resp.status_code in (200, 201)
            if not success:
                logger.error("Evolution API webhook registration failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.exception("Error registering Evolution API webhook: %s", e)
        success = False

    return WhatsAppWebhookResult(success=success, webhook_url=webhook_url)


@router.get("/settings", response_model=AllSettings)
async def get_all_settings(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    clinic_raw = await _get_config(db, "clinic_info")
    sla_raw = await _get_config(db, "sla")
    ai_raw = await _get_config(db, "ai_provider")
    chatbot_raw = await _get_config(db, "chatbot")
    notif_raw = await _get_config(db, "notifications")

    return AllSettings(
        clinic=ClinicSettings(**clinic_raw) if clinic_raw else ClinicSettings(),
        sla=SLASettings(**sla_raw) if sla_raw else SLASettings(),
        ai=AISettings(**ai_raw) if ai_raw else AISettings(),
        chatbot=ChatbotSettings(**chatbot_raw) if chatbot_raw else ChatbotSettings(),
        notifications=(
            NotificationsSettings(**notif_raw) if notif_raw else NotificationsSettings()
        ),
    )


@router.patch("/settings/clinic", response_model=ClinicSettings)
async def update_clinic_settings(
    payload: ClinicSettings,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "clinic_info", data, current_user.id)
    await log_action(
        db,
        action="settings.clinic.update",
        user_id=current_user.id,
        entity_type="system_config",
        payload=data,
        request=request,
    )
    return payload


@router.patch("/settings/sla", response_model=SLASettings)
async def update_sla_settings(
    payload: SLASettings,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "sla", data, current_user.id)
    await log_action(
        db,
        action="settings.sla.update",
        user_id=current_user.id,
        entity_type="system_config",
        payload=data,
        request=request,
    )
    return payload


@router.patch("/settings/ai", response_model=AISettings)
async def update_ai_settings(
    payload: AISettings,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "ai_provider", data, current_user.id)
    await log_action(
        db,
        action="settings.ai.update",
        user_id=current_user.id,
        entity_type="system_config",
        payload=data,
        request=request,
    )
    return payload


@router.patch("/settings/chatbot", response_model=ChatbotSettings)
async def update_chatbot_settings(
    payload: ChatbotSettings,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "chatbot", data, current_user.id)
    await log_action(
        db,
        action="settings.chatbot.update",
        user_id=current_user.id,
        entity_type="system_config",
        payload=data,
        request=request,
    )
    return payload


@router.patch("/settings/notifications", response_model=NotificationsSettings)
async def update_notifications_settings(
    payload: NotificationsSettings,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    await _set_config(db, "notifications", data, current_user.id)
    await log_action(
        db,
        action="settings.notifications.update",
        user_id=current_user.id,
        entity_type="system_config",
        payload=data,
        request=request,
    )
    return payload


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    result = await db.execute(query)
    return list(result.scalars().all())


# ── Test chat ─────────────────────────────────────────────────────────────────

@dataclass
class _TestPatient:
    """Paciente virtual para sessões de teste. Não é persistido no banco."""
    id: uuid.UUID
    full_name: str = "Admin (Teste)"


@router.post("/chat/test")
async def test_chat(
    body: TestChatRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Envia uma mensagem para a IA usando o mesmo engine do Telegram/WhatsApp.
    A sessão é armazenada no Redis com TTL de 24h e não cria pacientes reais.
    """
    from app.modules.ai.engine import process_message

    try:
        session_uuid = uuid.UUID(body.session_id)
    except ValueError:
        session_uuid = uuid.uuid4()

    patient = _TestPatient(id=session_uuid)
    response = await process_message(db, patient, body.message)  # type: ignore[arg-type]
    return {"response": response, "session_id": str(session_uuid)}


@router.delete("/chat/test/{session_id}", status_code=204)
async def clear_test_chat(
    session_id: str,
    current_user: User = Depends(require_role("admin")),
):
    """Apaga o histórico da sessão de teste no Redis."""
    from app.modules.ai.session import clear_session

    try:
        await clear_session(uuid.UUID(session_id))
    except Exception:
        pass
