"""Terminology builder (NEMSIS-constrained ICD-10, SNOMED, RXNorm)

Revision ID: 20260130_term
Revises: 20260130_agency
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_term"
down_revision: Union[str, Sequence[str], None] = "20260130_agency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "terminology_builder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code_set", sa.String(32), nullable=False),
        sa.Column("use_case", sa.String(32), nullable=False),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("alternate_text", sa.String(512), nullable=True),
        sa.Column("nemsis_element_ref", sa.String(128), nullable=True),
        sa.Column("nemsis_value_set", sa.String(128), nullable=True),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_terminology_builder_org_id", "terminology_builder", ["org_id"])
    op.create_index("ix_terminology_builder_code_set", "terminology_builder", ["code_set"])
    op.create_index("ix_terminology_builder_use_case", "terminology_builder", ["use_case"])
    op.create_index("ix_terminology_builder_code", "terminology_builder", ["code"])
    op.create_index("ix_terminology_builder_nemsis_element_ref", "terminology_builder", ["nemsis_element_ref"])


def downgrade() -> None:
    op.drop_index("ix_terminology_builder_nemsis_element_ref", table_name="terminology_builder")
    op.drop_index("ix_terminology_builder_code", table_name="terminology_builder")
    op.drop_index("ix_terminology_builder_use_case", table_name="terminology_builder")
    op.drop_index("ix_terminology_builder_code_set", table_name="terminology_builder")
    op.drop_index("ix_terminology_builder_org_id", table_name="terminology_builder")
    op.drop_table("terminology_builder")
