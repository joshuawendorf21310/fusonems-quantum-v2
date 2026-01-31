"""Add encryption at rest metadata table for SC-28 compliance

Revision ID: 20260130_encryption_at_rest_metadata
Revises: 20260130_encryption_keys
Create Date: 2026-01-30

This migration creates the encryption_metadata table for tracking encrypted fields:
- Field-level encryption tracking
- Key rotation support
- Backward compatibility metadata
- Migration status tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_encryption_at_rest_metadata"
down_revision: Union[str, Sequence[str], None] = "20260130_encryption_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create encryption_metadata table for tracking encrypted fields"""
    
    op.create_table(
        "encryption_metadata",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("table_name", sa.String(length=128), nullable=False),
        sa.Column("column_name", sa.String(length=128), nullable=False),
        sa.Column("key_id", sa.String(length=64), nullable=True),
        sa.Column("encryption_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("encrypted_at", sa.DateTime(), nullable=True),
        sa.Column("migration_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("backward_compatible", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    
    # Create indexes
    op.create_index(
        "ix_encryption_metadata_table_column",
        "encryption_metadata",
        ["table_name", "column_name"],
        unique=True
    )
    op.create_index(
        "ix_encryption_metadata_table",
        "encryption_metadata",
        ["table_name"]
    )
    op.create_index(
        "ix_encryption_metadata_key_id",
        "encryption_metadata",
        ["key_id"]
    )
    op.create_index(
        "ix_encryption_metadata_status",
        "encryption_metadata",
        ["migration_status"]
    )
    
    # Insert initial metadata for known sensitive fields
    # This tracks which fields should be encrypted
    encryption_metadata = sa.table(
        "encryption_metadata",
        sa.column("table_name", sa.String),
        sa.column("column_name", sa.String),
        sa.column("encryption_enabled", sa.Boolean),
        sa.column("migration_status", sa.String),
        sa.column("backward_compatible", sa.Boolean),
    )
    
    # PHI fields in Patient model
    op.bulk_insert(encryption_metadata, [
        {"table_name": "epcr_patients", "column_name": "first_name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "middle_name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "last_name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "date_of_birth", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "phone", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "address", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "epcr_patients", "column_name": "mrn", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
    ])
    
    # PHI fields in TelehealthPatient
    op.bulk_insert(encryption_metadata, [
        {"table_name": "telehealth.telehealth_patients", "column_name": "name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "telehealth.telehealth_patients", "column_name": "email", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "telehealth.telehealth_patients", "column_name": "phone", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "telehealth.telehealth_patients", "column_name": "address", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "telehealth.telehealth_patients", "column_name": "insurance_policy_number", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "telehealth.telehealth_patients", "column_name": "medical_history", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
    ])
    
    # PII fields in User model
    op.bulk_insert(encryption_metadata, [
        {"table_name": "users", "column_name": "email", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "users", "column_name": "full_name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
    ])
    
    # Payment fields
    op.bulk_insert(encryption_metadata, [
        {"table_name": "patient_payments", "column_name": "payment_method_last4", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "stripe_customers", "column_name": "email", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "stripe_customers", "column_name": "name", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
        {"table_name": "stripe_customers", "column_name": "default_payment_method", "encryption_enabled": True, "migration_status": "pending", "backward_compatible": True},
    ])


def downgrade() -> None:
    """Drop encryption_metadata table"""
    op.drop_index("ix_encryption_metadata_status", table_name="encryption_metadata")
    op.drop_index("ix_encryption_metadata_key_id", table_name="encryption_metadata")
    op.drop_index("ix_encryption_metadata_table", table_name="encryption_metadata")
    op.drop_index("ix_encryption_metadata_table_column", table_name="encryption_metadata")
    op.drop_table("encryption_metadata")
