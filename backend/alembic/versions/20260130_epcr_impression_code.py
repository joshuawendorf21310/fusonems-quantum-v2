"""Add impression_code (ICD-10) to epcr_assessments for NEMSIS-constrained impressions

Revision ID: 20260130_imp
Revises: 20260130_term
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_imp"
down_revision: Union[str, Sequence[str], None] = "20260130_term"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "epcr_assessments",
        sa.Column("impression_code", sa.String(32), nullable=True, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("epcr_assessments", "impression_code")
