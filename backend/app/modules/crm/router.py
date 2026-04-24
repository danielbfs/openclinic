"""Patient API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user
from app.database import get_db
from app.modules.auth.models import User
from app.modules.crm.schemas import PatientCreate, PatientResponse, PatientUpdate
from app.modules.crm.service import (
    create_patient,
    get_all_patients,
    get_patient_by_id,
    get_patient_by_phone,
    update_patient,
)

router = APIRouter()


@router.get("/", response_model=list[PatientResponse])
async def list_patients(
    status: str | None = None,
    search: str | None = Query(None, description="Buscar por nome, telefone ou email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_patients(db, status=status, search=search)


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_new_patient(
    body: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_patient_by_phone(db, body.phone)
    if existing:
        raise HTTPException(status_code=409, detail="Paciente com este telefone já existe.")

    return await create_patient(
        db,
        phone=body.phone,
        full_name=body.full_name,
        email=body.email,
        channel=body.channel,
        channel_id=body.channel_id,
        notes=body.notes,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_single_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_existing_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    if body.phone is not None:
        existing = await get_patient_by_phone(db, body.phone)
        if existing and existing.id != patient_id:
            raise HTTPException(status_code=409, detail="Telefone já cadastrado para outro paciente.")

    return await update_patient(
        db, patient,
        full_name=body.full_name,
        phone=body.phone,
        email=body.email,
        crm_status=body.crm_status,
        notes=body.notes,
    )
