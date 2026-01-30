"""Create prior auth requests table

Revision ID: a0845a1c2b43
Revises: f7a8c9d0e1b2
Create Date: 2026-01-25 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a0845a1c2b43"
down_revision: Union[str, Sequence[str], None] = "f7a8c9d0e1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prior_auth_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(), nullable=True),
        sa.Column("training_mode", sa.Boolean(), nullable=True),
        sa.Column("epcr_patient_id", sa.Integer(), nullable=False),
        sa.Column("payer_id", sa.Integer(), nullable=True),
        sa.Column("procedure_code", sa.String(), nullable=False),
        sa.Column("auth_number", sa.String(), nullable=False),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default="requested"),
        sa.Column("notes", sa.String(), nullable=True, server_default=""),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["epcr_patient_id"], ["epcr_patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prior_auth_requests_id"), "prior_auth_requests", ["id"], unique=False)
    op.create_index(op.f("ix_prior_auth_requests_org_id"), "prior_auth_requests", ["org_id"], unique=False)
    op.create_index(op.f("ix_prior_auth_requests_epcr_patient_id"), "prior_auth_requests", ["epcr_patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prior_auth_requests_epcr_patient_id"), table_name="prior_auth_requests")
    op.drop_index(op.f("ix_prior_auth_requests_org_id"), table_name="prior_auth_requests")
    op.drop_index(op.f("ix_prior_auth_requests_id"), table_name="prior_auth_requests")
    op.drop_table("prior_auth_requests")
