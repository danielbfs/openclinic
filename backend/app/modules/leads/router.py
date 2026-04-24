"""Lead API endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.permissions import get_current_user, require_role
from app.database import get_db
from app.modules.auth.models import User
from app.modules.crm.service import get_patient_by_phone, create_patient
from app.modules.leads.schemas import (
    FunnelItem,
    InboundLeadWebhook,
    InteractionCreate,
    InteractionResponse,
    LeadAssignRequest,
    LeadContactRequest,
    LeadConvertRequest,
    LeadCreate,
    LeadLostRequest,
    LeadResponse,
    LeadsBySourceItem,
    LeadUpdate,
    SLAReport,
    TimelineItem,
)
from app.modules.leads.service import (
    convert_lead,
    create_interaction,
    create_lead,
    get_all_leads,
    get_funnel,
    get_lead_by_id,
    get_lead_interactions,
    get_leads_by_source,
    get_sla_report,
    get_timeline,
    mark_contacted,
    mark_lost,
    update_lead,
)

router = APIRouter()


# --- CRUD ---

@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    status: str | None = None,
    channel: str | None = None,
    assigned_to: uuid.UUID | None = None,
    is_overdue: bool | None = None,
    specialty_id: uuid.UUID | None = None,
    utm_campaign: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_leads(
        db,
        status=status,
        channel=channel,
        assigned_to=assigned_to,
        is_overdue=is_overdue,
        specialty_id=specialty_id,
        utm_campaign=utm_campaign,
        search=search,
    )


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_new_lead(
    body: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_lead(
        db,
        phone=body.phone,
        full_name=body.full_name,
        email=body.email,
        channel=body.channel,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
        utm_content=body.utm_content,
        utm_term=body.utm_term,
        specialty_id=body.specialty_id,
        description=body.description,
        quote_value=body.quote_value,
        assigned_to=body.assigned_to,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_single_lead(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_existing_lead(
    lead_id: uuid.UUID,
    body: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")
    return await update_lead(db, lead, **body.model_dump(exclude_unset=True))


# --- Pipeline actions ---

@router.post("/{lead_id}/contact", response_model=LeadResponse)
async def contact_lead(
    lead_id: uuid.UUID,
    body: LeadContactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    lead = await mark_contacted(db, lead, notes=body.notes)

    # Registra interação automática
    await create_interaction(
        db, lead_id=lead.id, user_id=current_user.id,
        type="nota", content=body.notes or "Primeiro contato realizado.",
    )
    return lead


@router.post("/{lead_id}/convert", response_model=LeadResponse)
async def convert_lead_to_patient(
    lead_id: uuid.UUID,
    body: LeadConvertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    # Cria ou recupera paciente pelo telefone
    patient = await get_patient_by_phone(db, lead.phone)
    if not patient:
        patient = await create_patient(
            db,
            phone=lead.phone,
            full_name=body.patient_name or lead.full_name,
            email=lead.email,
            channel=lead.channel if lead.channel in ("telegram", "whatsapp") else "whatsapp",
        )

    lead = await convert_lead(db, lead, converted_patient_id=patient.id)

    await create_interaction(
        db, lead_id=lead.id, user_id=current_user.id,
        type="nota", content=f"Lead convertido em paciente.",
    )
    return lead


@router.post("/{lead_id}/lost", response_model=LeadResponse)
async def mark_lead_lost(
    lead_id: uuid.UUID,
    body: LeadLostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    lead = await mark_lost(db, lead, lost_reason=body.lost_reason)

    await create_interaction(
        db, lead_id=lead.id, user_id=current_user.id,
        type="nota", content=f"Lead perdido: {body.lost_reason}",
    )
    return lead


@router.patch("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: uuid.UUID,
    body: LeadAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")
    return await update_lead(db, lead, assigned_to=body.assigned_to)


# --- Interactions ---

@router.get("/{lead_id}/interactions", response_model=list[InteractionResponse])
async def list_interactions(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")
    return await get_lead_interactions(db, lead_id)


@router.post("/{lead_id}/interactions", response_model=InteractionResponse, status_code=201)
async def create_new_interaction(
    lead_id: uuid.UUID,
    body: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    return await create_interaction(
        db,
        lead_id=lead_id,
        user_id=current_user.id,
        type=body.type,
        content=body.content,
        next_action=body.next_action,
    )


# --- Webhook inbound (leads externos) ---

@router.post("/webhook/inbound", response_model=LeadResponse, status_code=201)
async def inbound_lead_webhook(
    body: InboundLeadWebhook,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Recebe leads de fontes externas (Google Ads, Meta Ads, formulários)."""
    if x_api_key != settings.LEADS_WEBHOOK_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida.")

    # Determina canal pela UTM
    channel = "outro"
    if body.utm_source:
        source_lower = body.utm_source.lower()
        if "google" in source_lower:
            channel = "google_ads"
        elif "facebook" in source_lower or "meta" in source_lower or "instagram" in source_lower:
            channel = "meta_ads"

    return await create_lead(
        db,
        phone=body.phone,
        full_name=body.name,
        email=body.email,
        channel=channel,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
        utm_content=body.utm_content,
        utm_term=body.utm_term,
        description=body.message,
    )


# --- Reports ---

def _parse_period(period: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if period == "7d":
        return now - timedelta(days=7)
    elif period == "30d":
        return now - timedelta(days=30)
    elif period == "90d":
        return now - timedelta(days=90)
    return None


@router.get("/reports/funnel", response_model=list[FunnelItem])
async def report_funnel(
    period: str = Query("30d", description="7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_funnel(db, date_from=_parse_period(period))


@router.get("/reports/by-source", response_model=list[LeadsBySourceItem])
async def report_by_source(
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_leads_by_source(db, date_from=_parse_period(period))


@router.get("/reports/sla", response_model=SLAReport)
async def report_sla(
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_sla_report(db, date_from=_parse_period(period))


@router.get("/reports/timeline", response_model=list[TimelineItem])
async def report_timeline(
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_timeline(db, date_from=_parse_period(period))
