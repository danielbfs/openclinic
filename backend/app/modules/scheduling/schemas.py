"""Pydantic schemas for doctors, schedules and appointments."""
import uuid
from datetime import datetime, time

from pydantic import BaseModel


# --- Doctor ---

class DoctorCreate(BaseModel):
    full_name: str
    crm: str | None = None
    specialty_id: uuid.UUID | None = None
    scheduling_provider: str = "local_db"
    slot_duration_minutes: int = 30


class DoctorUpdate(BaseModel):
    full_name: str | None = None
    crm: str | None = None
    specialty_id: uuid.UUID | None = None
    slot_duration_minutes: int | None = None
    is_active: bool | None = None


class DoctorScheduleItem(BaseModel):
    day_of_week: int  # 0=Mon ... 6=Sun
    start_time: str   # "08:00"
    end_time: str      # "12:00"


class DoctorScheduleSet(BaseModel):
    schedules: list[DoctorScheduleItem]


class DoctorScheduleResponse(BaseModel):
    id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    is_active: bool

    model_config = {"from_attributes": True}


class DoctorResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    crm: str | None
    specialty_id: uuid.UUID | None
    scheduling_provider: str
    slot_duration_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Schedule Block ---

class ScheduleBlockCreate(BaseModel):
    doctor_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None


class ScheduleBlockResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Appointment ---

class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    specialty_id: uuid.UUID | None = None
    starts_at: datetime
    ends_at: datetime
    notes: str | None = None
    source: str = "secretary"


class AppointmentUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    specialty_id: uuid.UUID | None
    starts_at: datetime
    ends_at: datetime
    status: str
    source: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Availability ---

class TimeSlot(BaseModel):
    starts_at: datetime
    ends_at: datetime
