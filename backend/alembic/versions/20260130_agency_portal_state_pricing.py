"""Add state, service_types (ambulance/fire/hems), and fair pricing to third_party_billing_agencies

Wisconsin-first, US-wide: state, service_types (JSON), base_charge_cents, per_call_cents, billing_interval.

Revision ID: 20260130_agency
Revises: 20260127_scheduling_module
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa


revision = "20260130_agency"
down_revision = "20260127_scheduling_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "third_party_billing_agencies",
        sa.Column("state", sa.String(2), nullable=True),
    )
    op.add_column(
        "third_party_billing_agencies",
        sa.Column("service_types", sa.JSON(), nullable=True),
    )
    op.add_column(
        "third_party_billing_agencies",
        sa.Column("base_charge_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "third_party_billing_agencies",
        sa.Column("per_call_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "third_party_billing_agencies",
        sa.Column("billing_interval", sa.String(20), nullable=True),
    )
    op.create_index(
        op.f("ix_third_party_billing_agencies_state"),
        "third_party_billing_agencies",
        ["state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_third_party_billing_agencies_state"),
        table_name="third_party_billing_agencies",
    )
    op.drop_column("third_party_billing_agencies", "billing_interval")
    op.drop_column("third_party_billing_agencies", "per_call_cents")
    op.drop_column("third_party_billing_agencies", "base_charge_cents")
    op.drop_column("third_party_billing_agencies", "service_types")
    op.drop_column("third_party_billing_agencies", "state")
