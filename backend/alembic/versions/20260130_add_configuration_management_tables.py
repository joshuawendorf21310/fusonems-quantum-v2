"""FedRAMP CM-2, CM-3, CM-6 Configuration Management Tables

Revision ID: 20260130_config_mgmt
Revises: 20260130_fedramp_auth
Create Date: 2026-01-30

This migration implements configuration management tables for FedRAMP compliance:
1. CM-2: Baseline Configurations - configuration_baselines table
2. CM-3: Configuration Change Control - configuration_change_requests and configuration_change_approvals tables
3. CM-6: Configuration Settings - configuration_compliance_status table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260130_config_mgmt"
down_revision: Union[str, Sequence[str], None] = "20260130_fedramp_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create configuration_baselines table (CM-2)
    op.create_table(
        "configuration_baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("configuration_snapshot", postgresql.JSON(), nullable=False),
        sa.Column("scope", postgresql.JSON(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Integer(), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["activated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_baseline_org_status", "configuration_baselines", ["org_id", "status"], unique=False)
    op.create_index("idx_baseline_created", "configuration_baselines", ["created_at"], unique=False)
    op.create_index("idx_baseline_name", "configuration_baselines", ["name"], unique=False)
    op.create_index("ix_configuration_baselines_org_id", "configuration_baselines", ["org_id"], unique=False)
    op.create_index("ix_configuration_baselines_created_by_user_id", "configuration_baselines", ["created_by_user_id"], unique=False)

    # Create configuration_change_requests table (CM-3)
    op.create_table(
        "configuration_change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("change_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("baseline_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("configuration_changes", postgresql.JSON(), nullable=False),
        sa.Column("affected_components", postgresql.JSON(), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("risk_level", sa.String(50), nullable=True),
        sa.Column("impact_assessment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_email", sa.String(255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("scheduled_implementation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_implementation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("implemented_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rollback_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column("rolled_back_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["baseline_id"], ["configuration_baselines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["implemented_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rolled_back_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_change_req_org_status", "configuration_change_requests", ["org_id", "status"], unique=False)
    op.create_index("idx_change_req_baseline", "configuration_change_requests", ["baseline_id"], unique=False)
    op.create_index("idx_change_req_created", "configuration_change_requests", ["requested_at"], unique=False)
    op.create_index("idx_change_req_priority", "configuration_change_requests", ["priority"], unique=False)
    op.create_index("ix_configuration_change_requests_org_id", "configuration_change_requests", ["org_id"], unique=False)
    op.create_index("ix_configuration_change_requests_change_number", "configuration_change_requests", ["change_number"], unique=True)
    op.create_index("ix_configuration_change_requests_requested_by_user_id", "configuration_change_requests", ["requested_by_user_id"], unique=False)

    # Create configuration_change_approvals table (CM-3)
    op.create_table(
        "configuration_change_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("change_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approval_role_required", sa.String(100), nullable=True),
        sa.Column("approver_user_id", sa.Integer(), nullable=True),
        sa.Column("approver_email", sa.String(255), nullable=True),
        sa.Column("approval_status", sa.String(50), nullable=False),
        sa.Column("approval_comment", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["change_request_id"], ["configuration_change_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approver_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_approval_change_req", "configuration_change_approvals", ["change_request_id"], unique=False)
    op.create_index("idx_approval_approver", "configuration_change_approvals", ["approver_user_id"], unique=False)
    op.create_index("idx_approval_status", "configuration_change_approvals", ["approval_status"], unique=False)
    op.create_index("ix_configuration_change_approvals_change_request_id", "configuration_change_approvals", ["change_request_id"], unique=False)

    # Create configuration_compliance_status table (CM-6)
    op.create_table(
        "configuration_compliance_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("baseline_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("component_name", sa.String(255), nullable=False),
        sa.Column("component_type", sa.String(100), nullable=True),
        sa.Column("compliance_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("current_configuration", postgresql.JSON(), nullable=True),
        sa.Column("expected_configuration", postgresql.JSON(), nullable=True),
        sa.Column("has_drift", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("drift_details", postgresql.JSON(), nullable=True),
        sa.Column("drift_severity", sa.String(50), nullable=True),
        sa.Column("compliance_rules_checked", postgresql.JSON(), nullable=True),
        sa.Column("compliance_violations", postgresql.JSON(), nullable=True),
        sa.Column("remediation_suggestions", postgresql.JSON(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("checked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("check_method", sa.String(100), nullable=True),
        sa.Column("next_check_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["baseline_id"], ["configuration_baselines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["checked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_compliance_org_status", "configuration_compliance_status", ["org_id", "compliance_status"], unique=False)
    op.create_index("idx_compliance_baseline", "configuration_compliance_status", ["baseline_id"], unique=False)
    op.create_index("idx_compliance_component", "configuration_compliance_status", ["component_name"], unique=False)
    op.create_index("idx_compliance_checked", "configuration_compliance_status", ["last_checked_at"], unique=False)
    op.create_index("ix_configuration_compliance_status_org_id", "configuration_compliance_status", ["org_id"], unique=False)
    op.create_index("ix_configuration_compliance_status_has_drift", "configuration_compliance_status", ["has_drift"], unique=False)


def downgrade() -> None:
    # Drop configuration compliance status table
    op.drop_index("ix_configuration_compliance_status_has_drift", table_name="configuration_compliance_status")
    op.drop_index("ix_configuration_compliance_status_org_id", table_name="configuration_compliance_status")
    op.drop_index("idx_compliance_checked", table_name="configuration_compliance_status")
    op.drop_index("idx_compliance_component", table_name="configuration_compliance_status")
    op.drop_index("idx_compliance_baseline", table_name="configuration_compliance_status")
    op.drop_index("idx_compliance_org_status", table_name="configuration_compliance_status")
    op.drop_table("configuration_compliance_status")
    
    # Drop configuration change approvals table
    op.drop_index("ix_configuration_change_approvals_change_request_id", table_name="configuration_change_approvals")
    op.drop_index("idx_approval_status", table_name="configuration_change_approvals")
    op.drop_index("idx_approval_approver", table_name="configuration_change_approvals")
    op.drop_index("idx_approval_change_req", table_name="configuration_change_approvals")
    op.drop_table("configuration_change_approvals")
    
    # Drop configuration change requests table
    op.drop_index("ix_configuration_change_requests_requested_by_user_id", table_name="configuration_change_requests")
    op.drop_index("ix_configuration_change_requests_change_number", table_name="configuration_change_requests")
    op.drop_index("ix_configuration_change_requests_org_id", table_name="configuration_change_requests")
    op.drop_index("idx_change_req_priority", table_name="configuration_change_requests")
    op.drop_index("idx_change_req_created", table_name="configuration_change_requests")
    op.drop_index("idx_change_req_baseline", table_name="configuration_change_requests")
    op.drop_index("idx_change_req_org_status", table_name="configuration_change_requests")
    op.drop_table("configuration_change_requests")
    
    # Drop configuration baselines table
    op.drop_index("ix_configuration_baselines_created_by_user_id", table_name="configuration_baselines")
    op.drop_index("ix_configuration_baselines_org_id", table_name="configuration_baselines")
    op.drop_index("idx_baseline_name", table_name="configuration_baselines")
    op.drop_index("idx_baseline_created", table_name="configuration_baselines")
    op.drop_index("idx_baseline_org_status", table_name="configuration_baselines")
    op.drop_table("configuration_baselines")
