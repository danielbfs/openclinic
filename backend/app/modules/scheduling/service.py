"""Doctor and scheduling business logic."""
import logging
import uuid
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.scheduling.models import (
    Appointment,
    Doctor,
    DoctorSchedule,
    ScheduleBlock,
)

logger = logging.getLogger(__name__)


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


# --- Availability Calculation ---

async def get_available_slots(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
) -> list[dict]:
    """Calculate available time slots for a doctor in a date range."""
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        return []

    slot_duration = timedelta(minutes=doctor.slot_duration_minutes)

    # 1. Get recurring schedule rules
    schedules = await get_doctor_schedules(db, doctor_id)

    # 2. Get blocks in this period
    blocks = await get_schedule_blocks(db, doctor_id, date_from, date_to)

    # 3. Get existing appointments (non-cancelled)
    result = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.starts_at < date_to,
                Appointment.ends_at > date_from,
                Appointment.status.notin_(["cancelled"]),
            )
        )
    )
    booked = list(result.scalars().all())

    # 4. Generate slots day by day — schedules are in clinic local time
    clinic_tz = ZoneInfo(settings.CLINIC_TIMEZONE)
    available = []
    current_date = date_from.date() if hasattr(date_from, "date") else date_from
    end_date = date_to.date() if hasattr(date_to, "date") else date_to
    now = datetime.now(timezone.utc)

    while current_date <= end_date:
        day_of_week = current_date.weekday()  # 0=Mon

        for sched in schedules:
            if sched.day_of_week != day_of_week or not sched.is_active:
                continue

            # Combine local date + local time, then convert to UTC for comparisons
            slot_start_local = datetime.combine(
                current_date, sched.start_time, tzinfo=clinic_tz
            )
            slot_end_local = datetime.combine(
                current_date, sched.end_time, tzinfo=clinic_tz
            )
            slot_start_dt = slot_start_local.astimezone(timezone.utc)
            slot_end_limit = slot_end_local.astimezone(timezone.utc)

            while slot_start_dt + slot_duration <= slot_end_limit:
                slot_end_dt = slot_start_dt + slot_duration

                # Skip past slots
                if slot_start_dt < now:
                    slot_start_dt = slot_end_dt
                    continue

                # Check blocks
                blocked = any(
                    b.starts_at < slot_end_dt and b.ends_at > slot_start_dt
                    for b in blocks
                )
                if blocked:
                    slot_start_dt = slot_end_dt
                    continue

                # Check booked appointments
                conflict = any(
                    a.starts_at < slot_end_dt and a.ends_at > slot_start_dt
                    for a in booked
                )
                if conflict:
                    slot_start_dt = slot_end_dt
                    continue

                available.append({
                    "starts_at": slot_start_dt.isoformat(),
                    "ends_at": slot_end_dt.isoformat(),
                })
                slot_start_dt = slot_end_dt

        current_date += timedelta(days=1)

    return available


async def get_available_slots_by_specialty(
    db: AsyncSession,
    specialty_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
) -> list[dict]:
    """Get available slots across all active doctors of a specialty."""
    result = await db.execute(
        select(Doctor).where(
            and_(Doctor.specialty_id == specialty_id, Doctor.is_active == True)
        )
    )
    doctors = list(result.scalars().unique().all())

    all_slots = []
    for doctor in doctors:
        slots = await get_available_slots(db, doctor.id, date_from, date_to)
        for slot in slots:
            slot["doctor_id"] = str(doctor.id)
            slot["doctor_name"] = doctor.full_name
        all_slots.extend(slots)

    all_slots.sort(key=lambda s: s["starts_at"])
    return all_slots


# --- Appointments ---

async def get_appointments(
    db: AsyncSession,
    doctor_id: uuid.UUID | None = None,
    patient_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: str | None = None,
) -> list[Appointment]:
    query = select(Appointment).order_by(Appointment.starts_at.desc())
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if date_from:
        query = query.where(Appointment.starts_at >= date_from)
    if date_to:
        query = query.where(Appointment.starts_at <= date_to)
    if status:
        query = query.where(Appointment.status == status)
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_appointment_by_id(db: AsyncSession, appointment_id: uuid.UUID) -> Appointment | None:
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    return result.scalar_one_or_none()


class SlotNotAvailableError(Exception):
    """Slot ocupado por outro agendamento (corrida ou booking duplo)."""


async def create_appointment(
    db: AsyncSession,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    specialty_id: uuid.UUID | None = None,
    source: str = "secretary",
    notes: str | None = None,
    created_by_user: uuid.UUID | None = None,
) -> Appointment:
    # Optimistic lock: verifica conflito com SELECT FOR UPDATE para serializar
    # tentativas concorrentes. A constraint EXCLUDE no DB é o backstop final.
    conflict_q = (
        select(Appointment.id)
        .where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.starts_at < ends_at,
                Appointment.ends_at > starts_at,
                Appointment.status.notin_(["cancelled"]),
            )
        )
        .with_for_update()
    )
    existing = await db.execute(conflict_q)
    if existing.scalar() is not None:
        raise SlotNotAvailableError(
            "O horário selecionado não está mais disponível."
        )

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        specialty_id=specialty_id,
        starts_at=starts_at,
        ends_at=ends_at,
        source=source,
        notes=notes,
        created_by_user=created_by_user,
    )
    db.add(appointment)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        # IntegrityError disparado pela EXCLUDE constraint — converte em erro amigável
        if "no_doctor_overlap" in str(exc) or "exclusion" in str(exc).lower():
            raise SlotNotAvailableError(
                "O horário selecionado acabou de ser ocupado por outro agendamento."
            ) from exc
        raise
    await db.refresh(appointment)

    # Schedule follow-up jobs based on active rules — best-effort
    try:
        from app.modules.followup.service import schedule_followups_for_appointment
        await schedule_followups_for_appointment(db, appointment)
    except Exception:
        logger.exception(
            "Failed to schedule follow-ups for appointment %s", appointment.id
        )

    return appointment


async def update_appointment(
    db: AsyncSession,
    appointment: Appointment,
    status: str | None = None,
    notes: str | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> Appointment:
    if status is not None:
        appointment.status = status
    if notes is not None:
        appointment.notes = notes
    if starts_at is not None:
        appointment.starts_at = starts_at
    if ends_at is not None:
        appointment.ends_at = ends_at
    await db.commit()
    await db.refresh(appointment)
    return appointment


async def cancel_appointment(db: AsyncSession, appointment: Appointment) -> Appointment:
    appointment.status = "cancelled"
    await db.commit()
    await db.refresh(appointment)
    return appointment
