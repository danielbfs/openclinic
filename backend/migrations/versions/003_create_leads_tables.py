"""create leads and lead_interactions tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Leads ---
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False, server_default="outro"),
        sa.Column("utm_source", sa.String(100), nullable=True),
        sa.Column("utm_medium", sa.String(100), nullable=True),
        sa.Column("utm_campaign", sa.String(255), nullable=True),
        sa.Column("utm_content", sa.String(255), nullable=True),
        sa.Column("utm_term", sa.String(255), nullable=True),
        sa.Column("specialty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specialties.id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quote_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="novo"),
        sa.Column("lost_reason", sa.String(255), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_followup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_channel", "leads", ["channel"])
    op.create_index("ix_leads_assigned", "leads", ["assigned_to"])
    op.create_index("ix_leads_created", "leads", ["created_at"])
    op.create_index("ix_leads_utm_campaign", "leads", ["utm_campaign"])

    # --- Lead Interactions ---
    op.create_table(
        "lead_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("interacted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_interactions_lead", "lead_interactions", ["lead_id", "interacted_at"])


def downgrade() -> None:
    op.drop_index("ix_lead_interactions_lead", table_name="lead_interactions")
    op.drop_table("lead_interactions")
    op.drop_index("ix_leads_utm_campaign", table_name="leads")
    op.drop_index("ix_leads_created", table_name="leads")
    op.drop_index("ix_leads_assigned", table_name="leads")
    op.drop_index("ix_leads_channel", table_name="leads")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_table("leads")
