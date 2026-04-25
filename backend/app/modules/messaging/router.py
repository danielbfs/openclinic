"""Webhook endpoints for messaging channels."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.crm.models import Patient
from app.modules.messaging.adapters.telegram import parse_telegram_update
from app.modules.messaging.gateway import send_message

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


@router.post("/telegram/{bot_token}")
async def telegram_webhook(
    bot_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming Telegram messages."""
    if bot_token != settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bot token")

    payload = await request.json()
    msg = parse_telegram_update(payload)
    if not msg:
        return {"ok": True}

    # Resolve or create patient
    patient = await get_or_create_patient(
        db,
        channel="telegram",
        channel_user_id=msg.channel_user_id,
        user_name=msg.user_name,
    )

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
    await send_message("telegram", msg.channel_chat_id, response_text)
    return {"ok": True}
