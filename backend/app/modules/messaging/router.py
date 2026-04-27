"""Webhook endpoints for messaging channels."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.crm.models import Patient
from app.modules.messaging.gateway import gateway, send_message
from app.modules.messaging.service import messaging_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_or_create_patient(
    db: AsyncSession,
    channel: str,
    channel_user_id: str,
    user_name: str | None = None,
) -> Patient:
    """Find existing patient by channel_id or create a new one."""
    result = await db.execute(
        select(Patient).where(
            Patient.channel == channel,
            Patient.channel_id == channel_user_id,
        )
    )
    patient = result.scalar_one_or_none()

    if patient:
        if user_name and not patient.full_name:
            patient.full_name = user_name
            await db.commit()
            await db.refresh(patient)
        return patient

    # Create new patient — use channel_user_id as phone placeholder
    patient = Patient(
        full_name=user_name,
        phone=f"{channel}:{channel_user_id}",
        channel=channel,
        channel_id=channel_user_id,
        crm_status="new",
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def handle_incoming_message(
    request: Request,
    channel: str,
    db: AsyncSession,
) -> dict:
    """Common logic to process messages from any channel."""
    payload = await request.json()
    msg = gateway.parse_webhook(channel, payload)
    
    if not msg:
        return {"ok": True}

    # Resolve or create patient
    patient = await get_or_create_patient(
        db,
        channel=channel,
        channel_user_id=msg.channel_user_id,
        user_name=msg.user_name,
    )

    # Check conversation control
    from app.modules.messaging.models import Conversation
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.channel == channel, 
            Conversation.patient_id == patient.id,
            Conversation.status == "active"
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if conversation and conversation.control == "human":
        # Message is received but AI is disabled for this conversation
        return {"ok": True}

    # Process through AI engine
    try:
        from app.modules.ai.engine import process_message
        response_text = await process_message(db, patient, msg.text)
    except Exception:
        logger.exception("AI engine error for patient %s", patient.id)
        response_text = (
            "Desculpe, estou com dificuldades no momento. "
            "Por favor, tente novamente em alguns instantes."
        )

    # Send reply
    await send_message(channel, msg.channel_chat_id, response_text)
    return {"ok": True}


@router.post("/telegram/{bot_token}")
async def telegram_webhook(
    bot_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming Telegram messages."""
    if bot_token != settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bot token")

    return await handle_incoming_message(request, "telegram", db)


@router.post("/whatsapp/{token}")
async def whatsapp_webhook(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming WhatsApp messages via Evolution API."""
    # For Evolution API, we can use the token as a simple shared secret 
    # or implement HMAC validation if requested.
    if token != settings.EVOLUTION_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

    return await handle_incoming_message(request, "whatsapp", db)


@router.get("/conversations")
async def list_conversations(
    channel: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List active conversations for the Shared Inbox."""
    return await messaging_service.get_active_conversations(db, channel)


@router.patch("/conversations/{conversation_id}/control")
async def toggle_conversation_control(
    conversation_id: uuid.UUID,
    control: str,
    db: AsyncSession = Depends(get_db),
):
    """Toggle control between 'ai' and 'human'."""
    try:
        await messaging_service.toggle_control(db, conversation_id, control)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/conversations/{conversation_id}/send")
async def send_human_message(
    conversation_id: uuid.UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Send a message as a human operator."""
    text = payload.get("text")
    channel = payload.get("channel")
    chat_id = payload.get("chat_id")

    if not all([text, channel, chat_id]):
        raise HTTPException(status_code=400, detail="Missing text, channel, or chat_id")

    success = await messaging_service.send_human_message(
        db, conversation_id, text, channel, chat_id
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return {"ok": True}
