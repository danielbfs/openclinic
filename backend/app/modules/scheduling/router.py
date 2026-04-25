"""Doctor and scheduling API endpoints."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user, require_role
from app.database import get_db
from app.modules.auth.models import User
from app.modules.scheduling.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    DoctorCreate,
    DoctorResponse,
    DoctorScheduleResponse,
    DoctorScheduleSet,
    DoctorUpdate,
    ScheduleBlockCreate,
    ScheduleBlockResponse,
    TimeSlot,
)
from app.modules.scheduling.service import (
    cancel_appointment,
    create_appointment,
    create_doctor,
    create_schedule_block,
    delete_schedule_block,
    get_all_doctors,
    get_appointment_by_id,
    get_appointments,
    get_available_slots,
    get_available_slots_by_specialty,
    get_doctor_by_id,
    get_doctor_schedules,
    get_schedule_block_by_id,
    get_schedule_blocks,
    set_doctor_schedules,
    update_appointment,
    update_doctor,
)

router = APIRouter()


# --- Doctors ---

@router.get("/doctors", response_model=list[DoctorResponse])
async def list_doctors(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_doctors(db, active_only=active_only)


@router.post("/doctors", response_model=DoctorResponse, status_code=201)
async def create_new_doctor(
    body: DoctorCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    return await create_doctor(
        db,
        full_name=body.full_name,
        crm=body.crm,
        specialty_id=body.specialty_id,
        scheduling_provider=body.scheduling_provider,
        slot_duration_minutes=body.slot_duration_minutes,
    )


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_single_doctor(
    doctor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    return doctor


@router.patch("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_existing_doctor(
    doctor_id: uuid.UUID,
    body: DoctorUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    return await update_doctor(
        db, doctor,
        full_name=body.full_name,
        crm=body.crm,
        specialty_id=body.specialty_id,
        slot_duration_minutes=body.slot_duration_minutes,
        is_active=body.is_active,
    )


# --- Doctor Schedules ---

@router.get("/doctors/{doctor_id}/schedule", response_model=list[DoctorScheduleResponse])
async def get_doctor_schedule(
    doctor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    return await get_doctor_schedules(db, doctor_id)


@router.put("/doctors/{doctor_id}/schedule", response_model=list[DoctorScheduleResponse])
async def replace_doctor_schedule(
    doctor_id: uuid.UUID,
    body: DoctorScheduleSet,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    schedules_data = [item.model_dump() for item in body.schedules]
    return await set_doctor_schedules(db, doctor_id, schedules_data)


# --- Schedule Blocks ---

@router.get("/blocks", response_model=list[ScheduleBlockResponse])
async def list_schedule_blocks(
    doctor_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_schedule_blocks(db, doctor_id)


@router.post("/blocks", response_model=ScheduleBlockResponse, status_code=201)
async def create_new_block(
    body: ScheduleBlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_schedule_block(
        db,
        doctor_id=body.doctor_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        reason=body.reason,
        created_by=current_user.id,
    )


@router.delete("/blocks/{block_id}", status_code=204)
async def delete_existing_block(
    block_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    block = await get_schedule_block_by_id(db, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado.")
    await delete_schedule_block(db, block)


# --- Availability Slots ---

@router.get("/slots")
async def list_available_slots(
    doctor_id: uuid.UUID | None = None,
    specialty_id: uuid.UUID | None = None,
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if doctor_id:
        return await get_available_slots(db, doctor_id, date_from, date_to)
    if specialty_id:
        return await get_available_slots_by_specialty(db, specialty_id, date_from, date_to)
    raise HTTPException(status_code=400, detail="Informe doctor_id ou specialty_id.")


# --- Appointments ---

@router.get("/appointments", response_model=list[AppointmentResponse])
async def list_appointments(
    doctor_id: uuid.UUID | None = None,
    patient_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_appointments(db, doctor_id, patient_id, date_from, date_to, status)


@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def create_new_appointment(
    body: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_appointment(
        db,
        patient_id=body.patient_id,
        doctor_id=body.doctor_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        specialty_id=body.specialty_id,
        source=body.source,
        notes=body.notes,
        created_by_user=current_user.id,
    )


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_single_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return appt


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_existing_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return await update_appointment(db, appt, status=body.status, notes=body.notes)


@router.delete("/appointments/{appointment_id}", status_code=204)
async def cancel_existing_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    await cancel_appointment(db, appt)
