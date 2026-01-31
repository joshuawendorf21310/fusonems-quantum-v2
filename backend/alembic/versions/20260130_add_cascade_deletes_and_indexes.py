"""Add cascade delete constraints and indexes for nullable foreign keys

Revision ID: 20260130_cascade_indexes
Revises: 20260130_term
Create Date: 2026-01-30

This migration:
1. Adds cascade delete constraints to major foreign keys:
   - users.org_id: SET NULL (users can exist without org)
   - epcr_records.patient_id: CASCADE
   - billing_claims.epcr_patient_id: CASCADE
   - cad_dispatches.call_id: CASCADE
   - cad_dispatches.unit_id: CASCADE

2. Adds indexes for frequently queried nullable foreign keys:
   - file_records.deleted_by
   - terminology_builder.created_by
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError


def _get_fk_constraint_name(inspector, table_name, column_name, referred_table):
    """Find the foreign key constraint name for a given column."""
    try:
        fks = inspector.get_foreign_keys(table_name)
        for fk in fks:
            if column_name in fk['constrained_columns'] and fk['referred_table'] == referred_table:
                return fk['name']
    except (SQLAlchemyError, AttributeError, KeyError) as e:
        # Inspector method failed or table/column doesn't exist - use fallback naming
        pass
    # Fallback to standard naming convention
    return f"{table_name}_{column_name}_fkey"


revision: str = "20260130_cascade_indexes"
down_revision: Union[str, Sequence[str], None] = "20260130_term"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get inspector for constraint name lookup
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Use batch operations for SQLite compatibility
    # Note: SQLite doesn't support ALTER TABLE DROP CONSTRAINT directly,
    # so batch_alter_table handles this by recreating the table
    
    # 1. Add cascade delete constraints to foreign keys
    
    # users.org_id: SET NULL (users can exist without org)
    fk_name = _get_fk_constraint_name(inspector, "users", "org_id", "organizations")
    with op.batch_alter_table("users", schema=None) as batch_op:
        # Drop existing FK constraint
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        # Recreate with SET NULL on delete
        batch_op.create_foreign_key(
            fk_name,
            "organizations",
            ["org_id"],
            ["id"],
            ondelete="SET NULL"
        )
    
    # epcr_records.patient_id: CASCADE
    fk_name = _get_fk_constraint_name(inspector, "epcr_records", "patient_id", "epcr_patients")
    with op.batch_alter_table("epcr_records", schema=None) as batch_op:
        # Drop existing FK constraint
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        # Recreate with CASCADE on delete
        batch_op.create_foreign_key(
            fk_name,
            "epcr_patients",
            ["patient_id"],
            ["id"],
            ondelete="CASCADE"
        )
    
    # billing_claims.epcr_patient_id: CASCADE
    fk_name = _get_fk_constraint_name(inspector, "billing_claims", "epcr_patient_id", "epcr_patients")
    with op.batch_alter_table("billing_claims", schema=None) as batch_op:
        # Drop existing FK constraint
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        # Recreate with CASCADE on delete
        batch_op.create_foreign_key(
            fk_name,
            "epcr_patients",
            ["epcr_patient_id"],
            ["id"],
            ondelete="CASCADE"
        )
    
    # cad_dispatches.call_id: CASCADE
    fk_name = _get_fk_constraint_name(inspector, "cad_dispatches", "call_id", "cad_calls")
    with op.batch_alter_table("cad_dispatches", schema=None) as batch_op:
        # Drop existing FK constraint
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        # Recreate with CASCADE on delete
        batch_op.create_foreign_key(
            fk_name,
            "cad_calls",
            ["call_id"],
            ["id"],
            ondelete="CASCADE"
        )
    
    # cad_dispatches.unit_id: CASCADE
    fk_name = _get_fk_constraint_name(inspector, "cad_dispatches", "unit_id", "cad_units")
    with op.batch_alter_table("cad_dispatches", schema=None) as batch_op:
        # Drop existing FK constraint
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        # Recreate with CASCADE on delete
        batch_op.create_foreign_key(
            fk_name,
            "cad_units",
            ["unit_id"],
            ["id"],
            ondelete="CASCADE"
        )
    
    # 2. Add indexes for frequently queried nullable foreign keys
    
    # file_records.deleted_by (nullable FK)
    op.create_index(
        "ix_file_records_deleted_by",
        "file_records",
        ["deleted_by"],
        unique=False
    )
    
    # terminology_builder.created_by (nullable FK)
    op.create_index(
        "ix_terminology_builder_created_by",
        "terminology_builder",
        ["created_by"],
        unique=False
    )


def downgrade() -> None:
    # Get inspector for constraint name lookup
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Remove indexes
    op.drop_index("ix_terminology_builder_created_by", table_name="terminology_builder")
    op.drop_index("ix_file_records_deleted_by", table_name="file_records")
    
    # Restore original foreign key constraints (without cascade)
    
    # cad_dispatches.unit_id: restore without CASCADE
    fk_name = _get_fk_constraint_name(inspector, "cad_dispatches", "unit_id", "cad_units")
    with op.batch_alter_table("cad_dispatches", schema=None) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            "cad_units",
            ["unit_id"],
            ["id"]
        )
    
    # cad_dispatches.call_id: restore without CASCADE
    fk_name = _get_fk_constraint_name(inspector, "cad_dispatches", "call_id", "cad_calls")
    with op.batch_alter_table("cad_dispatches", schema=None) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            "cad_calls",
            ["call_id"],
            ["id"]
        )
    
    # billing_claims.epcr_patient_id: restore without CASCADE
    fk_name = _get_fk_constraint_name(inspector, "billing_claims", "epcr_patient_id", "epcr_patients")
    with op.batch_alter_table("billing_claims", schema=None) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            "epcr_patients",
            ["epcr_patient_id"],
            ["id"]
        )
    
    # epcr_records.patient_id: restore without CASCADE
    fk_name = _get_fk_constraint_name(inspector, "epcr_records", "patient_id", "epcr_patients")
    with op.batch_alter_table("epcr_records", schema=None) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            "epcr_patients",
            ["patient_id"],
            ["id"]
        )
    
    # users.org_id: restore without SET NULL
    fk_name = _get_fk_constraint_name(inspector, "users", "org_id", "organizations")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.create_foreign_key(
            fk_name,
            "organizations",
            ["org_id"],
            ["id"]
        )
