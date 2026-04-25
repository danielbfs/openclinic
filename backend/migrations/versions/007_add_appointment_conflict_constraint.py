"""add appointment overlap exclusion constraint

Revision ID: 007
Revises: 006
Create Date: 2026-04-25
"""
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable btree_gist extension required for EXCLUDE with non-btree operators
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Add exclusion constraint to prevent overlapping appointments for the same doctor
    # Only applies to non-cancelled appointments
    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT no_doctor_overlap
        EXCLUDE USING gist (
            doctor_id WITH =,
            tstzrange(starts_at, ends_at) WITH &&
        )
        WHERE (status NOT IN ('cancelled'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_doctor_overlap")
