"""AI function calling tools — executed when the LLM requests them."""
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.scheduling.service import (
    SlotNotAvailableError,
    get_appointments,
    get_available_slots,
    get_available_slots_by_specialty,
    get_appointment_by_id,
    create_appointment,
    cancel_appointment,
    update_appointment,
    get_doctor_by_id,
)

logger = logging.getLogger(__name__)


def _parse_datetime_aware(value: str) -> datetime:
    """Parse ISO 8601 string. If naive, assume clinic timezone."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(settings.CLINIC_TIMEZONE))
    return dt

# OpenAI function definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Verifica horários disponíveis para agendamento. "
                "Use quando o paciente quer marcar consulta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty_id": {
                        "type": "string",
                        "description": "UUID da especialidade (opcional se doctor_id fornecido)",
                    },
                    "doctor_id": {
                        "type": "string",
                        "description": "UUID do médico específico (opcional)",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Data início (ISO 8601). Se não informado, usa hoje.",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Data fim (ISO 8601). Se não informado, usa 7 dias a partir de date_from.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "Agenda uma consulta para o paciente. "
                "SEMPRE confirme o horário com o paciente antes de chamar esta função."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {
                        "type": "string",
                        "description": "UUID do médico",
                    },
                    "starts_at": {
                        "type": "string",
                        "description": "Data/hora de início (ISO 8601)",
                    },
                    "patient_notes": {
                        "type": "string",
                        "description": "Observações do paciente (queixa principal, etc.)",
                    },
                },
                "required": ["doctor_id", "starts_at"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancela um agendamento existente do paciente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "UUID do agendamento a cancelar",
                    },
                },
                "required": ["appointment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Remarca um agendamento existente para novo horário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "UUID do agendamento a remarcar",
                    },
                    "new_starts_at": {
                        "type": "string",
                        "description": "Nova data/hora de início (ISO 8601)",
                    },
                },
                "required": ["appointment_id", "new_starts_at"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": "Lista os agendamentos do paciente atual.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Transfere a conversa para atendimento humano (secretária). "
                "Use quando não conseguir resolver o pedido do paciente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Motivo da escalação",
                    },
                },
                "required": ["reason"],
            },
        },
    },
]


async def execute_tool(
    tool_name: str,
    arguments: dict,
    db: AsyncSession,
    patient_id: uuid.UUID,
) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if tool_name == "check_availability":
            return await _check_availability(db, arguments)
        elif tool_name == "book_appointment":
            return await _book_appointment(db, patient_id, arguments)
        elif tool_name == "cancel_appointment":
            return await _cancel_appointment(db, arguments)
        elif tool_name == "reschedule_appointment":
            return await _reschedule_appointment(db, arguments)
        elif tool_name == "get_patient_appointments":
            return await _get_patient_appointments(db, patient_id)
        elif tool_name == "escalate_to_human":
            return await _escalate_to_human(db, patient_id, arguments)
        else:
            return json.dumps({"error": f"Tool desconhecida: {tool_name}"})
    except Exception as e:
        logger.exception("Tool execution error: %s", tool_name)
        return json.dumps({"error": str(e)})


async def _check_availability(db: AsyncSession, args: dict) -> str:
    now = datetime.now(timezone.utc)
    date_from = _parse_datetime_aware(args["date_from"]) if args.get("date_from") else now
    date_to = (
        _parse_datetime_aware(args["date_to"])
        if args.get("date_to")
        else date_from + timedelta(days=7)
    )

    if args.get("doctor_id"):
        slots = await get_available_slots(
            db, uuid.UUID(args["doctor_id"]), date_from, date_to
        )
    elif args.get("specialty_id"):
        slots = await get_available_slots_by_specialty(
            db, uuid.UUID(args["specialty_id"]), date_from, date_to
        )
    else:
        return json.dumps({"error": "Informe doctor_id ou specialty_id"})

    # Limit to 15 slots to avoid huge responses
    return json.dumps({"available_slots": slots[:15], "total": len(slots)})


async def _book_appointment(
    db: AsyncSession, patient_id: uuid.UUID, args: dict
) -> str:
    doctor_id = uuid.UUID(args["doctor_id"])
    starts_at = _parse_datetime_aware(args["starts_at"])

    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        return json.dumps({"error": "Médico não encontrado"})

    ends_at = starts_at + timedelta(minutes=doctor.slot_duration_minutes)

    try:
        appt = await create_appointment(
            db,
            patient_id=patient_id,
            doctor_id=doctor_id,
            starts_at=starts_at,
            ends_at=ends_at,
            specialty_id=doctor.specialty_id,
            source="ai_chat",
            notes=args.get("patient_notes"),
        )
        return json.dumps({
            "success": True,
            "appointment_id": str(appt.id),
            "doctor_name": doctor.full_name,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        })
    except SlotNotAvailableError as e:
        return json.dumps({"error": str(e), "slot_unavailable": True})
    except Exception as e:
        return json.dumps({"error": f"Não foi possível agendar: {e}"})


async def _cancel_appointment(db: AsyncSession, args: dict) -> str:
    appt_id = uuid.UUID(args["appointment_id"])
    appt = await get_appointment_by_id(db, appt_id)
    if not appt:
        return json.dumps({"error": "Agendamento não encontrado"})
    if appt.status == "cancelled":
        return json.dumps({"error": "Agendamento já foi cancelado"})

    await cancel_appointment(db, appt)
    return json.dumps({"success": True, "message": "Agendamento cancelado"})


async def _reschedule_appointment(db: AsyncSession, args: dict) -> str:
    appt_id = uuid.UUID(args["appointment_id"])
    new_starts_at = _parse_datetime_aware(args["new_starts_at"])

    appt = await get_appointment_by_id(db, appt_id)
    if not appt:
        return json.dumps({"error": "Agendamento não encontrado"})

    doctor = await get_doctor_by_id(db, appt.doctor_id)
    new_ends_at = new_starts_at + timedelta(minutes=doctor.slot_duration_minutes)

    await update_appointment(
        db, appt, starts_at=new_starts_at, ends_at=new_ends_at
    )
    return json.dumps({
        "success": True,
        "new_starts_at": new_starts_at.isoformat(),
        "new_ends_at": new_ends_at.isoformat(),
    })


async def _get_patient_appointments(db: AsyncSession, patient_id: uuid.UUID) -> str:
    appts = await get_appointments(db, patient_id=patient_id)
    active = [a for a in appts if a.status not in ("cancelled",)]
    result = []
    for a in active[:10]:
        result.append({
            "appointment_id": str(a.id),
            "doctor_name": a.doctor.full_name if a.doctor else "—",
            "specialty": a.specialty.name if a.specialty else "—",
            "starts_at": a.starts_at.isoformat(),
            "ends_at": a.ends_at.isoformat(),
            "status": a.status,
        })
    return json.dumps({"appointments": result})


async def _escalate_to_human(
    db: AsyncSession, patient_id: uuid.UUID, args: dict
) -> str:
    """Marca o paciente como escalonado, encerra sessão IA e notifica humano."""
    from sqlalchemy import select

    from app.modules.admin.models import SystemConfig
    from app.modules.ai.session import clear_session
    from app.modules.crm.models import Patient
    from app.modules.messaging.gateway import send_message

    reason = args.get("reason", "Paciente solicitou atendimento humano")

    # 1. Marca o paciente — usamos crm_status para indicar revisão humana
    patient = await db.get(Patient, patient_id)
    if patient:
        existing_notes = patient.notes or ""
        prefix = "[ESCALONADO PARA HUMANO] "
        if not existing_notes.startswith(prefix):
            patient.notes = f"{prefix}{reason}\n{existing_notes}".strip()
        await db.commit()

    # 2. Limpa sessão IA para que próximas mensagens não continuem o fluxo automatizado
    try:
        await clear_session(patient_id)
    except Exception:
        logger.exception("Failed to clear AI session for patient %s", patient_id)

    # 3. Notifica via Telegram (se configurado)
    try:
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == "notifications")
        )
        row = result.scalar_one_or_none()
        chat_id = (row.value or {}).get("escalation_telegram_chat_id") if row else ""
        if chat_id and patient:
            name = patient.full_name or patient.phone
            text = (
                f"🆘 *Atendimento humano solicitado*\n\n"
                f"Paciente: {name}\n"
                f"Canal: {patient.channel}\n"
                f"Motivo: {reason}"
            )
            await send_message("telegram", chat_id, text)
    except Exception:
        logger.exception("Failed to send escalation notification")

    return json.dumps({
        "escalated": True,
        "message": (
            "Conversa encaminhada para a secretária. "
            f"Motivo: {reason}. "
            "Em breve alguém entrará em contato."
        ),
    })
