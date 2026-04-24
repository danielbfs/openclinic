"""Doctor and scheduling business logic."""
import uuid
from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models import Doctor, DoctorSchedule, ScheduleBlock


# --- Doctors ---

async def get_all_doctors(db: AsyncSession, active_only: bool = False) -> list[Doctor]:
    query = select(Doctor).order_by(Doctor.full_name)
    if active_only:
        query = query.where(Doctor.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_doctor_by_id(db: AsyncSession, doctor_id: uuid.UUID) -> Doctor | None:
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    return result.scalar_one_or_none()


async def create_doctor(
    db: AsyncSession,
    full_name: str,
    crm: str | None = None,
    specialty_id: uuid.UUID | None = None,
    scheduling_provider: str = "local_db",
    slot_duration_minutes: int = 30,
) -> Doctor:
    doctor = Doctor(
        full_name=full_name,
        crm=crm,
        specialty_id=specialty_id,
        scheduling_provider=scheduling_provider,
        slot_duration_minutes=slot_duration_minutes,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


async def update_doctor(
    db: AsyncSession,
    doctor: Doctor,
    full_name: str | None = None,
    crm: str | None = None,
    specialty_id: uuid.UUID | None = None,
    slot_duration_minutes: int | None = None,
    is_active: bool | None = None,
) -> Doctor:
    if full_name is not None:
        doctor.full_name = full_name
    if crm is not None:
        doctor.crm = crm
    if specialty_id is not None:
        doctor.specialty_id = specialty_id
    if slot_duration_minutes is not None:
        doctor.slot_duration_minutes = slot_duration_minutes
    if is_active is not None:
        doctor.is_active = is_active
    await db.commit()
    await db.refresh(doctor)
    return doctor


# --- Doctor Schedules ---

async def get_doctor_schedules(db: AsyncSession, doctor_id: uuid.UUID) -> list[DoctorSchedule]:
    result = await db.execute(
        select(DoctorSchedule)
        .where(DoctorSchedule.doctor_id == doctor_id)
        .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
    )
    return list(result.scalars().all())


async def set_doctor_schedules(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    schedules: list[dict],
) -> list[DoctorSchedule]:
    """Replace all schedules for a doctor."""
    # Remove existing
    existing = await db.execute(
        select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
    )
    for sched in existing.scalars().all():
        await db.delete(sched)

    # Create new
    new_schedules = []
    for item in schedules:
        h_start, m_start = map(int, item["start_time"].split(":"))
        h_end, m_end = map(int, item["end_time"].split(":"))
        sched = DoctorSchedule(
            doctor_id=doctor_id,
            day_of_week=item["day_of_week"],
            start_time=time(h_start, m_start),
            end_time=time(h_end, m_end),
        )
        db.add(sched)
        new_schedules.append(sched)

    await db.commit()
    for s in new_schedules:
        await db.refresh(s)
    return new_schedules


# --- Schedule Blocks ---

async def get_schedule_blocks(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[ScheduleBlock]:
    query = select(ScheduleBlock).where(ScheduleBlock.doctor_id == doctor_id)
    if date_from:
        query = query.where(ScheduleBlock.ends_at >= date_from)
    if date_to:
        query = query.where(ScheduleBlock.starts_at <= date_to)
    query = query.order_by(ScheduleBlock.starts_at)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_schedule_block(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    reason: str | None = None,
    created_by: uuid.UUID | None = None,
) -> ScheduleBlock:
    block = ScheduleBlock(
        doctor_id=doctor_id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=reason,
        created_by=created_by,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def delete_schedule_block(db: AsyncSession, block: ScheduleBlock) -> None:
    await db.delete(block)
    await db.commit()


async def get_schedule_block_by_id(db: AsyncSession, block_id: uuid.UUID) -> ScheduleBlock | None:
    result = await db.execute(select(ScheduleBlock).where(ScheduleBlock.id == block_id))
    return result.scalar_one_or_none()
