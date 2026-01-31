"""Add encryption_keys table for FIPS 140-2 key management

Revision ID: 20260130_encryption_keys
Revises: 20260130_comprehensive_audit
Create Date: 2026-01-30

This migration creates the encryption_keys table for FedRAMP SC-12 and SC-13 compliance.
The table stores encrypted cryptographic keys with lifecycle management:
- Key generation and rotation
- Key escrow for recovery
- HSM integration support
- FIPS 140-2 compliance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_encryption_keys"
down_revision: Union[str, Sequence[str], None] = "20260130_comprehensive_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create encryption_keys table for key management"""
    
    op.create_table(
        "encryption_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("key_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("rotation_interval_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("hsm_backed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escrowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escrow_location", sa.String(length=256), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    
    # Create indexes for efficient queries
    op.create_index("ix_encryption_keys_key_id", "encryption_keys", ["key_id"], unique=True)
    op.create_index("ix_encryption_keys_key_type", "encryption_keys", ["key_type"])
    op.create_index("ix_encryption_keys_status", "encryption_keys", ["status"])
    op.create_index("ix_encryption_keys_expires_at", "encryption_keys", ["expires_at"])
    op.create_index("ix_encryption_keys_created_at", "encryption_keys", ["created_at"])


def downgrade() -> None:
    """Drop encryption_keys table"""
    op.drop_index("ix_encryption_keys_created_at", table_name="encryption_keys")
    op.drop_index("ix_encryption_keys_expires_at", table_name="encryption_keys")
    op.drop_index("ix_encryption_keys_status", table_name="encryption_keys")
    op.drop_index("ix_encryption_keys_key_type", table_name="encryption_keys")
    op.drop_index("ix_encryption_keys_key_id", table_name="encryption_keys")
    op.drop_table("encryption_keys")
