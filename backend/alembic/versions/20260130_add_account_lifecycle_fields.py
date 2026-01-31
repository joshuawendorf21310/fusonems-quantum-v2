"""Add account lifecycle management fields for FedRAMP AC-2(2), AC-2(3)

Revision ID: 20260130_account_lifecycle
Revises: 20260130_cascade_indexes
Create Date: 2026-01-30

This migration adds fields for automated account management:
- last_activity_at: Track user activity for inactivity detection
- account_status: Track account state (active, inactive, disabled, terminated)
- deactivation_reason: Reason for account deactivation
- deactivation_scheduled_at: Scheduled deactivation date
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_account_lifecycle"
down_revision: Union[str, Sequence[str], None] = "20260130_cascade_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add account lifecycle management fields
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("account_status", sa.String(), nullable=False, server_default="active"))
        batch_op.add_column(sa.Column("deactivation_reason", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("deactivation_scheduled_at", sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for efficient queries
    op.create_index("ix_users_last_activity_at", "users", ["last_activity_at"], unique=False)
    op.create_index("ix_users_account_status", "users", ["account_status"], unique=False)
    op.create_index("ix_users_deactivation_scheduled_at", "users", ["deactivation_scheduled_at"], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index("ix_users_deactivation_scheduled_at", table_name="users")
    op.drop_index("ix_users_account_status", table_name="users")
    op.drop_index("ix_users_last_activity_at", table_name="users")
    
    # Remove columns
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("deactivation_scheduled_at")
        batch_op.drop_column("deactivation_reason")
        batch_op.drop_column("account_status")
        batch_op.drop_column("last_activity_at")
