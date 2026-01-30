"""Add users.must_change_password for force-change on first login

Revision ID: 20260130_mustpw
Revises: 20260130_nemsis
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260130_mustpw"
down_revision: Union[str, Sequence[str], None] = "20260130_nemsis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
