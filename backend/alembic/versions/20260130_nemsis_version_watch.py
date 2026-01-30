"""NEMSIS version watch table (single row)

Revision ID: 20260130_nemsis
Revises: 20260130_term
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_nemsis"
down_revision: Union[str, Sequence[str], None] = "20260130_term"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nemsis_version_watch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_known_version", sa.String(32), nullable=False, server_default=sa.text("'3.5.1'")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notified_version", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO nemsis_version_watch (id, last_known_version) VALUES (1, '3.5.1')")


def downgrade() -> None:
    op.drop_table("nemsis_version_watch")
