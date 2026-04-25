"""create followup_rules and followup_jobs tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "followup_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("trigger_event", sa.String(50), nullable=False),
        sa.Column("offset_minutes", sa.Integer, nullable=False),
        sa.Column("message_template", sa.Text, nullable=False),
        sa.Column("channel", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "followup_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_id", UUID(as_uuid=True), sa.ForeignKey("followup_rules.id"), nullable=False),
        sa.Column("appointment_id", UUID(as_uuid=True), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default=sa.text("'pending'")),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("idx_followup_jobs_scheduled", "followup_jobs", ["scheduled_for", "status"])


def downgrade() -> None:
    op.drop_index("idx_followup_jobs_scheduled", table_name="followup_jobs")
    op.drop_table("followup_jobs")
    op.drop_table("followup_rules")
