"""Patient business logic."""
import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Patient


async def get_all_patients(
    db: AsyncSession,
    status: str | None = None,
    search: str | None = None,
) -> list[Patient]:
    query = select(Patient).order_by(Patient.created_at.desc())
    if status:
        query = query.where(Patient.crm_status == status)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(pattern),
                Patient.phone.ilike(pattern),
                Patient.email.ilike(pattern),
            )
        )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_patient_by_id(db: AsyncSession, patient_id: uuid.UUID) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def get_patient_by_phone(db: AsyncSession, phone: str) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.phone == phone))
    return result.scalar_one_or_none()


async def create_patient(
    db: AsyncSession,
    phone: str,
    full_name: str | None = None,
    email: str | None = None,
    channel: str = "whatsapp",
    channel_id: str | None = None,
    notes: str | None = None,
) -> Patient:
    patient = Patient(
        full_name=full_name,
        phone=phone,
        email=email,
        channel=channel,
        channel_id=channel_id,
        notes=notes,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def update_patient(
    db: AsyncSession,
    patient: Patient,
    full_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    crm_status: str | None = None,
    notes: str | None = None,
) -> Patient:
    if full_name is not None:
        patient.full_name = full_name
    if phone is not None:
        patient.phone = phone
    if email is not None:
        patient.email = email
    if crm_status is not None:
        patient.crm_status = crm_status
    if notes is not None:
        patient.notes = notes
    await db.commit()
    await db.refresh(patient)
    return patient
