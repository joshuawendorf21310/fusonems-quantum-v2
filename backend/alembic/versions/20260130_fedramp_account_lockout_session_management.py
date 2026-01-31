"""FedRAMP AC-7 Account Lockout and AC-11/AC-12 Session Management

Revision ID: 20260130_fedramp_auth
Revises: 20260130_cascade_indexes
Create Date: 2026-01-30

This migration implements:
1. Account lockout tables for FedRAMP AC-7 compliance:
   - account_lockouts: Tracks failed login attempts and lockout state
   - account_lockout_audits: Audit log for lockout events

2. Session management enhancements (AC-11/AC-12):
   - Uses existing auth_sessions table (no schema changes needed)
   - Session timeout and lifetime enforcement handled in application code
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_fedramp_auth"
down_revision: Union[str, Sequence[str], None] = "20260130_cascade_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create account_lockouts table (FedRAMP AC-7)
    op.create_table(
        "account_lockouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unlock_reason", sa.String(), nullable=True),
        sa.Column("last_failed_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_account_lockouts_id", "account_lockouts", ["id"], unique=False)
    op.create_index("ix_account_lockouts_user_id", "account_lockouts", ["user_id"], unique=True)
    op.create_index("ix_account_lockouts_locked_until", "account_lockouts", ["locked_until"], unique=False)

    # Create account_lockout_audits table (FedRAMP AC-7 audit requirement)
    op.create_table(
        "account_lockout_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_account_lockout_audits_id", "account_lockout_audits", ["id"], unique=False)
    op.create_index("ix_account_lockout_audits_user_id", "account_lockout_audits", ["user_id"], unique=False)
    op.create_index("ix_account_lockout_audits_created_at", "account_lockout_audits", ["created_at"], unique=False)


def downgrade() -> None:
    # Drop account lockout tables
    op.drop_index("ix_account_lockout_audits_created_at", table_name="account_lockout_audits")
    op.drop_index("ix_account_lockout_audits_user_id", table_name="account_lockout_audits")
    op.drop_index("ix_account_lockout_audits_id", table_name="account_lockout_audits")
    op.drop_table("account_lockout_audits")
    
    op.drop_index("ix_account_lockouts_locked_until", table_name="account_lockouts")
    op.drop_index("ix_account_lockouts_user_id", table_name="account_lockouts")
    op.drop_index("ix_account_lockouts_id", table_name="account_lockouts")
    op.drop_table("account_lockouts")
