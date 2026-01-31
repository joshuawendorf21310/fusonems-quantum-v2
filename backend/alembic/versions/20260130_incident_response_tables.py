"""Add incident response tables for FedRAMP IR-4, IR-5, IR-6 compliance

Revision ID: 20260130_incident_response
Revises: 20260130_comprehensive_audit
Create Date: 2026-01-30

This migration creates the security incident tracking tables for FedRAMP IR-4, IR-5, IR-6 compliance:
- security_incidents: Main incident tracking table
- incident_activities: Activity log for incidents
- incident_timeline: Timeline of key events

These tables support:
- IR-4: Incident Handling
- IR-5: Incident Monitoring
- IR-6: Incident Reporting
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_incident_response"
down_revision: Union[str, Sequence[str], None] = "20260130_comprehensive_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create incident response tables with all required indexes"""
    
    # Create security_incidents table
    op.create_table(
        "security_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("incident_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="informational"),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="other"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("detected_by_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("detection_method", sa.String(length=100), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("affected_systems", postgresql.JSON(), nullable=True),
        sa.Column("affected_users", postgresql.JSON(), nullable=True),
        sa.Column("affected_resources", postgresql.JSON(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("impact_assessment", sa.Text(), nullable=True),
        sa.Column("containment_actions", sa.Text(), nullable=True),
        sa.Column("remediation_actions", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("us_cert_reported", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("us_cert_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("us_cert_report_id", sa.String(length=255), nullable=True),
        sa.Column("us_cert_follow_up_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tags", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("classification", sa.String(length=50), nullable=True),
        sa.Column("training_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["detected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # Create incident_activities table
    op.create_table(
        "incident_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # Create incident_timeline table
    op.create_table(
        "incident_timeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"], ondelete="CASCADE"),
    )
    
    # Create indexes for security_incidents
    op.create_index("idx_incident_status_severity", "security_incidents", ["status", "severity"])
    op.create_index("idx_incident_org_status", "security_incidents", ["org_id", "status"])
    op.create_index("idx_incident_created", "security_incidents", ["created_at"])
    op.create_index("idx_incident_category", "security_incidents", ["category"])
    op.create_index("idx_incident_assigned_to", "security_incidents", ["assigned_to_user_id"])
    op.create_index("idx_incident_detected_at", "security_incidents", ["detected_at"])
    op.create_index("idx_incident_resolved_at", "security_incidents", ["resolved_at"])
    op.create_index("idx_incident_us_cert_reported", "security_incidents", ["us_cert_reported_at"])
    op.create_index("ix_security_incidents_org_id", "security_incidents", ["org_id"])
    op.create_index("ix_security_incidents_incident_number", "security_incidents", ["incident_number"])
    op.create_index("ix_security_incidents_status", "security_incidents", ["status"])
    op.create_index("ix_security_incidents_severity", "security_incidents", ["severity"])
    op.create_index("ix_security_incidents_category", "security_incidents", ["category"])
    op.create_index("ix_security_incidents_detected_by_user_id", "security_incidents", ["detected_by_user_id"])
    op.create_index("ix_security_incidents_assigned_to_user_id", "security_incidents", ["assigned_to_user_id"])
    
    # Create indexes for incident_activities
    op.create_index("idx_activity_incident", "incident_activities", ["incident_id"])
    op.create_index("idx_activity_user", "incident_activities", ["user_id"])
    op.create_index("idx_activity_timestamp", "incident_activities", ["timestamp"])
    op.create_index("idx_activity_type", "incident_activities", ["activity_type"])
    op.create_index("ix_incident_activities_incident_id", "incident_activities", ["incident_id"])
    op.create_index("ix_incident_activities_user_id", "incident_activities", ["user_id"])
    
    # Create indexes for incident_timeline
    op.create_index("idx_timeline_incident", "incident_timeline", ["incident_id"])
    op.create_index("idx_timeline_event_time", "incident_timeline", ["event_time"])
    op.create_index("idx_timeline_event_type", "incident_timeline", ["event_type"])
    op.create_index("ix_incident_timeline_incident_id", "incident_timeline", ["incident_id"])


def downgrade() -> None:
    """Drop incident response tables and indexes"""
    
    # Drop indexes for incident_timeline
    op.drop_index("ix_incident_timeline_incident_id", table_name="incident_timeline")
    op.drop_index("idx_timeline_event_type", table_name="incident_timeline")
    op.drop_index("idx_timeline_event_time", table_name="incident_timeline")
    op.drop_index("idx_timeline_incident", table_name="incident_timeline")
    
    # Drop indexes for incident_activities
    op.drop_index("ix_incident_activities_user_id", table_name="incident_activities")
    op.drop_index("ix_incident_activities_incident_id", table_name="incident_activities")
    op.drop_index("idx_activity_type", table_name="incident_activities")
    op.drop_index("idx_activity_timestamp", table_name="incident_activities")
    op.drop_index("idx_activity_user", table_name="incident_activities")
    op.drop_index("idx_activity_incident", table_name="incident_activities")
    
    # Drop indexes for security_incidents
    op.drop_index("ix_security_incidents_assigned_to_user_id", table_name="security_incidents")
    op.drop_index("ix_security_incidents_detected_by_user_id", table_name="security_incidents")
    op.drop_index("ix_security_incidents_category", table_name="security_incidents")
    op.drop_index("ix_security_incidents_severity", table_name="security_incidents")
    op.drop_index("ix_security_incidents_status", table_name="security_incidents")
    op.drop_index("ix_security_incidents_incident_number", table_name="security_incidents")
    op.drop_index("ix_security_incidents_org_id", table_name="security_incidents")
    op.drop_index("idx_incident_us_cert_reported", table_name="security_incidents")
    op.drop_index("idx_incident_resolved_at", table_name="security_incidents")
    op.drop_index("idx_incident_detected_at", table_name="security_incidents")
    op.drop_index("idx_incident_assigned_to", table_name="security_incidents")
    op.drop_index("idx_incident_category", table_name="security_incidents")
    op.drop_index("idx_incident_created", table_name="security_incidents")
    op.drop_index("idx_incident_org_status", table_name="security_incidents")
    op.drop_index("idx_incident_status_severity", table_name="security_incidents")
    
    # Drop tables
    op.drop_table("incident_timeline")
    op.drop_table("incident_activities")
    op.drop_table("security_incidents")
