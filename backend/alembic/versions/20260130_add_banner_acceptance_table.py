"""Add banner acceptance table for FedRAMP AC-8 compliance

Revision ID: 20260130_banner_acceptance
Revises: 20260130_account_lifecycle
Create Date: 2026-01-30

This migration creates the banner_acceptances table to track user acceptance
of the system use notification banner as required by FedRAMP AC-8.

FedRAMP AC-8 requires:
- Display system use notification before granting access
- Track user acceptance with timestamp, IP, and banner version
- Retain consent records for compliance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260130_banner_acceptance"
down_revision: Union[str, Sequence[str], None] = "20260130_account_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create banner_acceptances table
    op.create_table(
        "banner_acceptances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("banner_version", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create indexes for efficient queries
    op.create_index("ix_banner_acceptances_user_id", "banner_acceptances", ["user_id"], unique=False)
    op.create_index("ix_banner_acceptances_banner_version", "banner_acceptances", ["banner_version"], unique=False)
    op.create_index("ix_banner_acceptances_accepted_at", "banner_acceptances", ["accepted_at"], unique=False)
    
    # Composite index for checking if user has accepted current banner version
    op.create_index(
        "idx_banner_user_version",
        "banner_acceptances",
        ["user_id", "banner_version"],
        unique=False,
    )
    
    # Index for compliance reporting
    op.create_index(
        "idx_banner_acceptance_date",
        "banner_acceptances",
        ["accepted_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_banner_acceptance_date", table_name="banner_acceptances")
    op.drop_index("idx_banner_user_version", table_name="banner_acceptances")
    op.drop_index("ix_banner_acceptances_accepted_at", table_name="banner_acceptances")
    op.drop_index("ix_banner_acceptances_banner_version", table_name="banner_acceptances")
    op.drop_index("ix_banner_acceptances_user_id", table_name="banner_acceptances")
    
    # Drop table
    op.drop_table("banner_acceptances")
