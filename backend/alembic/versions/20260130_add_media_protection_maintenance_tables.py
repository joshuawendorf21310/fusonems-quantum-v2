"""FedRAMP MP-2 through MP-7 and MA-2 through MA-6 Tables

Revision ID: 20260130_media_maintenance
Revises: 20260130_config_mgmt
Create Date: 2026-01-30

This migration implements Media Protection and Maintenance tables for FedRAMP compliance:
Media Protection (MP):
- MP-2: Media Access - media_access table
- MP-3: Media Marking - media_marking table
- MP-4: Media Storage - media_storage table
- MP-5: Media Transport - media_transport table
- MP-6: Media Sanitization - media_sanitization table
- MP-7: Media Use - media_use table

Maintenance (MA):
- MA-2: Controlled Maintenance - controlled_maintenance table
- MA-3: Maintenance Tools - maintenance_tools and maintenance_tool_usage tables
- MA-4: Nonlocal Maintenance - nonlocal_maintenance table
- MA-5: Maintenance Personnel - maintenance_personnel table
- MA-6: Timely Maintenance - timely_maintenance table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260130_media_maintenance"
down_revision: Union[str, Sequence[str], None] = "20260130_config_mgmt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # MP-4: MEDIA STORAGE (created first as other tables reference it)
    # ========================================================================
    op.create_table(
        "media_storage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_identifier", sa.String(255), nullable=False, unique=True),
        sa.Column("media_type", sa.String(50), nullable=False),
        sa.Column("media_description", sa.Text(), nullable=True),
        sa.Column("storage_location", sa.String(500), nullable=False),
        sa.Column("storage_facility", sa.String(255), nullable=True),
        sa.Column("storage_room", sa.String(255), nullable=True),
        sa.Column("storage_container", sa.String(255), nullable=True),
        sa.Column("temperature_min", sa.String(50), nullable=True),
        sa.Column("temperature_max", sa.String(50), nullable=True),
        sa.Column("humidity_min", sa.String(50), nullable=True),
        sa.Column("humidity_max", sa.String(50), nullable=True),
        sa.Column("fire_suppression", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("access_control", sa.String(255), nullable=True),
        sa.Column("storage_status", sa.String(50), nullable=False, server_default="in_use"),
        sa.Column("inventory_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_inventory_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_inventory_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("disposal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disposal_method", sa.String(100), nullable=True),
        sa.Column("disposal_certificate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        # Note: disposal_certificate_id foreign key will be added after media_sanitization table is created
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_storage_org_status", "media_storage", ["org_id", "storage_status"], unique=False)
    op.create_index("idx_media_storage_location", "media_storage", ["storage_location"], unique=False)
    op.create_index("idx_media_storage_type", "media_storage", ["media_type"], unique=False)
    op.create_index("idx_media_storage_created", "media_storage", ["created_at"], unique=False)
    op.create_index("ix_media_storage_org_id", "media_storage", ["org_id"], unique=False)
    op.create_index("ix_media_storage_media_identifier", "media_storage", ["media_identifier"], unique=True)

    # ========================================================================
    # MP-2: MEDIA ACCESS
    # ========================================================================
    op.create_table(
        "media_access",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("access_status", sa.String(50), nullable=False, server_default="granted"),
        sa.Column("access_purpose", sa.Text(), nullable=False),
        sa.Column("access_level", sa.String(50), nullable=False),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=True),
        sa.Column("authorization_reason", sa.Text(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_storage.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_access_org_media", "media_access", ["org_id", "media_id"], unique=False)
    op.create_index("idx_media_access_user", "media_access", ["user_id"], unique=False)
    op.create_index("idx_media_access_status", "media_access", ["access_status"], unique=False)
    op.create_index("idx_media_access_dates", "media_access", ["granted_at", "expires_at"], unique=False)

    # ========================================================================
    # MP-3: MEDIA MARKING
    # ========================================================================
    op.create_table(
        "media_marking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classification_level", sa.String(50), nullable=False),
        sa.Column("classification_label", sa.String(255), nullable=False),
        sa.Column("classification_marking", sa.Text(), nullable=True),
        sa.Column("marked_by_user_id", sa.Integer(), nullable=False),
        sa.Column("marked_by_email", sa.String(255), nullable=True),
        sa.Column("validated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("validated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_storage.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["marked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["validated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_marking_org_media", "media_marking", ["org_id", "media_id"], unique=False)
    op.create_index("idx_media_marking_classification", "media_marking", ["classification_level"], unique=False)
    op.create_index("idx_media_marking_created", "media_marking", ["created_at"], unique=False)

    # ========================================================================
    # MP-5: MEDIA TRANSPORT
    # ========================================================================
    op.create_table(
        "media_transport",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transport_number", sa.String(100), nullable=False, unique=True),
        sa.Column("transport_purpose", sa.Text(), nullable=False),
        sa.Column("origin_location", sa.String(500), nullable=False),
        sa.Column("destination_location", sa.String(500), nullable=False),
        sa.Column("destination_contact", sa.String(255), nullable=True),
        sa.Column("destination_contact_phone", sa.String(50), nullable=True),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=False),
        sa.Column("authorization_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("transporter_name", sa.String(255), nullable=False),
        sa.Column("transporter_company", sa.String(255), nullable=True),
        sa.Column("transporter_contact", sa.String(255), nullable=True),
        sa.Column("encryption_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("encryption_method", sa.String(100), nullable=True),
        sa.Column("encryption_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("chain_of_custody", postgresql.JSON(), nullable=True),
        sa.Column("transport_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("transport_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_number", sa.String(255), nullable=True),
        sa.Column("carrier_name", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_storage.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_transport_org_media", "media_transport", ["org_id", "media_id"], unique=False)
    op.create_index("idx_media_transport_status", "media_transport", ["transport_status"], unique=False)
    op.create_index("idx_media_transport_dates", "media_transport", ["transport_date", "expected_delivery_date"], unique=False)

    # ========================================================================
    # MP-6: MEDIA SANITIZATION
    # ========================================================================
    op.create_table(
        "media_sanitization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sanitization_number", sa.String(100), nullable=False, unique=True),
        sa.Column("sanitization_method", sa.String(50), nullable=False),
        sa.Column("sanitization_reason", sa.Text(), nullable=False),
        sa.Column("sanitization_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("sanitized_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sanitized_by_name", sa.String(255), nullable=True),
        sa.Column("sanitized_by_company", sa.String(255), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.String(100), nullable=True),
        sa.Column("verification_results", sa.Text(), nullable=True),
        sa.Column("sanitization_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certificate_number", sa.String(100), nullable=True, unique=True),
        sa.Column("certificate_issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certificate_issued_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sanitization_procedures", sa.Text(), nullable=True),
        sa.Column("sanitization_evidence", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_storage.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sanitized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["certificate_issued_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_sanitization_org_media", "media_sanitization", ["org_id", "media_id"], unique=False)
    op.create_index("idx_media_sanitization_status", "media_sanitization", ["sanitization_status"], unique=False)
    op.create_index("idx_media_sanitization_method", "media_sanitization", ["sanitization_method"], unique=False)
    op.create_index("idx_media_sanitization_date", "media_sanitization", ["sanitization_date"], unique=False)

    # ========================================================================
    # MP-7: MEDIA USE
    # ========================================================================
    op.create_table(
        "media_use",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("use_purpose", sa.Text(), nullable=False),
        sa.Column("use_location", sa.String(500), nullable=True),
        sa.Column("device_used_on", sa.String(255), nullable=True),
        sa.Column("policy_compliant", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("policy_violations", postgresql.JSON(), nullable=True),
        sa.Column("policy_acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("policy_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("use_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("use_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_logged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_access_logged", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_storage.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_use_org_media", "media_use", ["org_id", "media_id"], unique=False)
    op.create_index("idx_media_use_user", "media_use", ["user_id"], unique=False)
    op.create_index("idx_media_use_dates", "media_use", ["use_start_date", "use_end_date"], unique=False)
    op.create_index("idx_media_use_compliant", "media_use", ["policy_compliant"], unique=False)

    # ========================================================================
    # MA-5: MAINTENANCE PERSONNEL (created first as other tables reference it)
    # ========================================================================
    op.create_table(
        "maintenance_personnel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("personnel_name", sa.String(255), nullable=False),
        sa.Column("personnel_email", sa.String(255), nullable=True),
        sa.Column("personnel_phone", sa.String(50), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("company_contact", sa.String(255), nullable=True),
        sa.Column("company_phone", sa.String(50), nullable=True),
        sa.Column("authorization_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorization_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("background_check_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("background_check_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("background_check_results", sa.Text(), nullable=True),
        sa.Column("access_level", sa.String(50), nullable=True),
        sa.Column("allowed_systems", postgresql.JSON(), nullable=True),
        sa.Column("restricted_systems", postgresql.JSON(), nullable=True),
        sa.Column("escort_required", sa.String(50), nullable=False, server_default="required"),
        sa.Column("escort_personnel_id", sa.Integer(), nullable=True),
        sa.Column("activity_logged", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_activity_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escort_personnel_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_maint_personnel_org_status", "maintenance_personnel", ["org_id", "authorization_status"], unique=False)
    op.create_index("idx_maint_personnel_name", "maintenance_personnel", ["personnel_name"], unique=False)
    op.create_index("idx_maint_personnel_company", "maintenance_personnel", ["company_name"], unique=False)

    # ========================================================================
    # MA-2: CONTROLLED MAINTENANCE
    # ========================================================================
    op.create_table(
        "controlled_maintenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("system_name", sa.String(255), nullable=False),
        sa.Column("component_name", sa.String(255), nullable=True),
        sa.Column("component_type", sa.String(100), nullable=True),
        sa.Column("scheduled_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maintenance_status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("approval_status", sa.String(50), nullable=True, server_default="pending"),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_comment", sa.Text(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_email", sa.String(255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("assigned_personnel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("impact_assessment", sa.Text(), nullable=True),
        sa.Column("downtime_expected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("downtime_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("maintenance_log", postgresql.JSON(), nullable=True),
        sa.Column("maintenance_notes", sa.Text(), nullable=True),
        sa.Column("completed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_personnel_id"], ["maintenance_personnel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["completed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_controlled_maint_org_status", "controlled_maintenance", ["org_id", "maintenance_status"], unique=False)
    op.create_index("idx_controlled_maint_type", "controlled_maintenance", ["maintenance_type"], unique=False)
    op.create_index("idx_controlled_maint_dates", "controlled_maintenance", ["scheduled_start_date", "scheduled_end_date"], unique=False)
    op.create_index("idx_controlled_maint_priority", "controlled_maintenance", ["priority"], unique=False)

    # ========================================================================
    # MA-3: MAINTENANCE TOOLS
    # ========================================================================
    op.create_table(
        "maintenance_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("tool_type", sa.String(100), nullable=False),
        sa.Column("tool_version", sa.String(100), nullable=True),
        sa.Column("tool_manufacturer", sa.String(255), nullable=True),
        sa.Column("tool_serial_number", sa.String(255), nullable=True, unique=True),
        sa.Column("tool_description", sa.Text(), nullable=True),
        sa.Column("tool_capabilities", postgresql.JSON(), nullable=True),
        sa.Column("tool_status", sa.String(50), nullable=False, server_default="pending_approval"),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorization_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("security_risks", postgresql.JSON(), nullable=True),
        sa.Column("security_mitigations", sa.Text(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("usage_restrictions", sa.Text(), nullable=True),
        sa.Column("allowed_systems", postgresql.JSON(), nullable=True),
        sa.Column("restricted_systems", postgresql.JSON(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("assigned_to_personnel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_personnel_id"], ["maintenance_personnel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_maint_tool_org_status", "maintenance_tools", ["org_id", "tool_status"], unique=False)
    op.create_index("idx_maint_tool_name", "maintenance_tools", ["tool_name"], unique=False)
    op.create_index("idx_maint_tool_type", "maintenance_tools", ["tool_type"], unique=False)

    op.create_table(
        "maintenance_tool_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_purpose", sa.Text(), nullable=False),
        sa.Column("system_used_on", sa.String(255), nullable=False),
        sa.Column("used_by_personnel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("usage_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usage_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_results", sa.Text(), nullable=True),
        sa.Column("issues_encountered", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tool_id"], ["maintenance_tools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["maintenance_id"], ["controlled_maintenance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by_personnel_id"], ["maintenance_personnel.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tool_usage_tool", "maintenance_tool_usage", ["tool_id"], unique=False)
    op.create_index("idx_tool_usage_maint", "maintenance_tool_usage", ["maintenance_id"], unique=False)
    op.create_index("idx_tool_usage_dates", "maintenance_tool_usage", ["usage_start_date", "usage_end_date"], unique=False)

    # ========================================================================
    # MA-4: NONLOCAL MAINTENANCE
    # ========================================================================
    op.create_table(
        "nonlocal_maintenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("session_number", sa.String(100), nullable=False, unique=True),
        sa.Column("session_purpose", sa.Text(), nullable=False),
        sa.Column("maintenance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("system_name", sa.String(255), nullable=False),
        sa.Column("system_ip_address", sa.String(45), nullable=True),
        sa.Column("system_hostname", sa.String(255), nullable=True),
        sa.Column("personnel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("authorization_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_method", sa.String(100), nullable=False),
        sa.Column("access_protocol", sa.String(50), nullable=True),
        sa.Column("encryption_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("encryption_method", sa.String(100), nullable=True),
        sa.Column("session_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("session_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_monitored", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("session_log_path", sa.String(500), nullable=True),
        sa.Column("session_recording_path", sa.String(500), nullable=True),
        sa.Column("allowed_commands", postgresql.JSON(), nullable=True),
        sa.Column("restricted_commands", postgresql.JSON(), nullable=True),
        sa.Column("allowed_files", postgresql.JSON(), nullable=True),
        sa.Column("restricted_files", postgresql.JSON(), nullable=True),
        sa.Column("terminated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("termination_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["maintenance_id"], ["controlled_maintenance.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["personnel_id"], ["maintenance_personnel.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["terminated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_nonlocal_maint_org_status", "nonlocal_maintenance", ["org_id", "session_status"], unique=False)
    op.create_index("idx_nonlocal_maint_personnel", "nonlocal_maintenance", ["personnel_id"], unique=False)
    op.create_index("idx_nonlocal_maint_dates", "nonlocal_maintenance", ["session_start_date", "session_end_date"], unique=False)

    # ========================================================================
    # MA-6: TIMELY MAINTENANCE
    # ========================================================================
    op.create_table(
        "timely_maintenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(255), nullable=False),
        sa.Column("component_name", sa.String(255), nullable=True),
        sa.Column("component_type", sa.String(100), nullable=True),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("maintenance_due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("maintenance_completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_status", sa.String(50), nullable=True),
        sa.Column("sla_met", sa.Boolean(), nullable=True),
        sa.Column("sla_variance_hours", sa.Integer(), nullable=True),
        sa.Column("preventive_schedule_days", sa.Integer(), nullable=True),
        sa.Column("last_preventive_maintenance_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_preventive_maintenance_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maintenance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("compliance_status", sa.String(50), nullable=True),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["maintenance_id"], ["controlled_maintenance.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_timely_maint_org_system", "timely_maintenance", ["org_id", "system_name"], unique=False)
    op.create_index("idx_timely_maint_sla_status", "timely_maintenance", ["sla_status"], unique=False)
    op.create_index("idx_timely_maint_due_date", "timely_maintenance", ["maintenance_due_date"], unique=False)
    op.create_index("idx_timely_maint_type", "timely_maintenance", ["maintenance_type"], unique=False)

    # Add foreign key constraint for media_storage.disposal_certificate_id
    # (it references media_sanitization which is now created)
    op.create_foreign_key(
        "media_storage_disposal_certificate_id_fkey",
        "media_storage",
        "media_sanitization",
        ["disposal_certificate_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_table("timely_maintenance")
    op.drop_table("nonlocal_maintenance")
    op.drop_table("maintenance_tool_usage")
    op.drop_table("maintenance_tools")
    op.drop_table("controlled_maintenance")
    op.drop_table("maintenance_personnel")
    op.drop_table("media_use")
    op.drop_table("media_sanitization")
    op.drop_table("media_transport")
    op.drop_table("media_marking")
    op.drop_table("media_access")
    op.drop_table("media_storage")
