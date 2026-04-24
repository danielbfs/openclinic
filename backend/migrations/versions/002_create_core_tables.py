"""create specialties, doctors, patients, schedules, appointments tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Specialties ---
    op.create_table(
        "specialties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- Patients ---
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False, server_default="whatsapp"),
        sa.Column("channel_id", sa.String(100), nullable=True),
        sa.Column("crm_status", sa.String(30), nullable=False, server_default="new"),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_patients_phone", "patients", ["phone"], unique=True)

    # --- Doctors ---
    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("crm", sa.String(50), nullable=True),
        sa.Column("specialty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specialties.id"), nullable=True),
        sa.Column("scheduling_provider", sa.String(50), nullable=False, server_default="local_db"),
        sa.Column("provider_config", postgresql.JSONB(), nullable=True),
        sa.Column("slot_duration_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- Doctor Schedules ---
    op.create_table(
        "doctor_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    # --- Schedule Blocks ---
    op.create_table(
        "schedule_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # --- Appointments ---
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("specialty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specialties.id"), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="scheduled", nullable=False),
        sa.Column("source", sa.String(30), nullable=True),
        sa.Column("external_event_id", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_appointments_doctor_starts", "appointments", ["doctor_id", "starts_at"])
    op.create_index("ix_appointments_patient", "appointments", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_appointments_patient", table_name="appointments")
    op.drop_index("ix_appointments_doctor_starts", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("schedule_blocks")
    op.drop_table("doctor_schedules")
    op.drop_table("doctors")
    op.drop_index("ix_patients_phone", table_name="patients")
    op.drop_table("patients")
    op.drop_table("specialties")
