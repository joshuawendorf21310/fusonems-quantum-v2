"""Add FedRAMP Audit, Identity, and Configuration Management controls

Revision ID: 20260130_fedramp_controls
Revises: 20260130_comprehensive_audit
Create Date: 2026-01-30

This migration creates tables for:
- AU-5: Audit Failure Response
- AU-7: Audit Reduction
- AU-10: Non-Repudiation
- AU-14: Session Audit
- IA-2(11): Separate Device Authentication
- IA-3: Device Identification
- IA-5(2): PKI Authentication
- CM-4: Security Impact Analysis
- CM-7: Least Functionality
- CM-8: Component Inventory
- CM-9: Configuration Management Plan
- CM-10: Software Usage Restrictions
- CM-11: User-Installed Software
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_fedramp_controls"
down_revision: Union[str, Sequence[str], None] = "20260130_comprehensive_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all FedRAMP control tables"""
    
    # AU-5: Audit Failure Response
    op.create_table(
        "audit_failure_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("failure_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="detected"),
        sa.Column("failure_message", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_details", postgresql.JSON, nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("detected_by", sa.String(length=255), nullable=True),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alert_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("alert_recipients", postgresql.JSON, nullable=True),
        sa.Column("failover_activated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("failover_activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failover_target", sa.String(length=255), nullable=True),
        sa.Column("failover_status", sa.String(length=50), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("storage_usage_percent", sa.Integer(), nullable=True),
        sa.Column("log_rate_per_second", sa.Integer(), nullable=True),
        sa.Column("affected_events_count", sa.Integer(), nullable=True),
        sa.Column("events_recovered", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_audit_failure_org_status", "audit_failure_responses", ["org_id", "status"])
    op.create_index("idx_audit_failure_detected", "audit_failure_responses", ["detected_at"])
    op.create_index("idx_audit_failure_type", "audit_failure_responses", ["failure_type"])
    op.create_index("idx_audit_failure_severity", "audit_failure_responses", ["severity"])
    
    op.create_table(
        "audit_system_capacity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("storage_usage_percent", sa.Integer(), nullable=False),
        sa.Column("storage_available_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_total_bytes", sa.Integer(), nullable=True),
        sa.Column("log_rate_per_second", sa.Integer(), nullable=True),
        sa.Column("log_queue_size", sa.Integer(), nullable=True),
        sa.Column("storage_warning_threshold", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("storage_critical_threshold", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("is_healthy", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("warnings_active", postgresql.JSON, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_capacity_org_timestamp", "audit_system_capacity", ["org_id", "recorded_at"])
    op.create_index("idx_capacity_recorded", "audit_system_capacity", ["recorded_at"])
    
    # AU-7: Audit Reduction
    op.create_table(
        "audit_reduction_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("report_name", sa.String(length=255), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("query_filters", postgresql.JSON, nullable=True),
        sa.Column("query_parameters", postgresql.JSON, nullable=True),
        sa.Column("summary_statistics", postgresql.JSON, nullable=True),
        sa.Column("detected_patterns", postgresql.JSON, nullable=True),
        sa.Column("findings", postgresql.JSON, nullable=True),
        sa.Column("recommendations", postgresql.JSON, nullable=True),
        sa.Column("report_content", postgresql.JSON, nullable=True),
        sa.Column("report_format", sa.String(length=50), nullable=True),
        sa.Column("events_analyzed", sa.Integer(), nullable=True),
        sa.Column("generation_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSON, nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_report_org_type", "audit_reduction_reports", ["org_id", "report_type"])
    op.create_index("idx_report_status", "audit_reduction_reports", ["status"])
    op.create_index("idx_report_created", "audit_reduction_reports", ["created_at"])
    op.create_index("idx_report_period", "audit_reduction_reports", ["period_start", "period_end"])
    
    op.create_table(
        "audit_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("pattern_type", sa.String(length=50), nullable=False),
        sa.Column("pattern_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pattern_definition", postgresql.JSON, nullable=False),
        sa.Column("matched_events", postgresql.JSON, nullable=True),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("detected_by", sa.String(length=255), nullable=True),
        sa.Column("first_occurrence", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_occurrence", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["acknowledged_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_pattern_org_type", "audit_patterns", ["org_id", "pattern_type"])
    op.create_index("idx_pattern_detected", "audit_patterns", ["detected_at"])
    op.create_index("idx_pattern_severity", "audit_patterns", ["severity"])
    
    op.create_table(
        "audit_query_optimizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("query_type", sa.String(length=100), nullable=False),
        sa.Column("query_parameters", postgresql.JSON, nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False),
        sa.Column("events_scanned", sa.Integer(), nullable=True),
        sa.Column("events_returned", sa.Integer(), nullable=True),
        sa.Column("index_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("optimization_applied", postgresql.JSON, nullable=True),
        sa.Column("performance_improvement_percent", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_query_opt_org", "audit_query_optimizations", ["org_id"])
    op.create_index("idx_query_opt_timestamp", "audit_query_optimizations", ["recorded_at"])
    
    # AU-10: Non-Repudiation
    op.create_table(
        "digital_signatures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("action_criticality", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("content_hash", sa.String(length=255), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=True),
        sa.Column("full_content", postgresql.JSON, nullable=True),
        sa.Column("signature_algorithm", sa.String(length=50), nullable=False, server_default="RSA-SHA256"),
        sa.Column("signature_value", sa.Text(), nullable=False),
        sa.Column("signature_certificate", sa.Text(), nullable=True),
        sa.Column("signed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("signed_by_email", sa.String(length=255), nullable=True),
        sa.Column("signed_by_role", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="signed"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column("verification_result", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("audit_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_signature_org_resource", "digital_signatures", ["org_id", "resource_type", "resource_id"])
    op.create_index("idx_signature_user", "digital_signatures", ["signed_by_user_id"])
    op.create_index("idx_signature_status", "digital_signatures", ["status"])
    op.create_index("idx_signature_created", "digital_signatures", ["created_at"])
    op.create_index("idx_signature_hash", "digital_signatures", ["content_hash"])
    
    op.create_table(
        "receipt_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("communication_type", sa.String(length=100), nullable=False),
        sa.Column("communication_content", sa.Text(), nullable=True),
        sa.Column("sent_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sent_by_email", sa.String(length=255), nullable=True),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=True),
        sa.Column("receipt_hash", sa.String(length=255), nullable=False),
        sa.Column("receipt_signature", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("acknowledgment_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sent_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_receipt_org_resource", "receipt_confirmations", ["org_id", "resource_type", "resource_id"])
    op.create_index("idx_receipt_recipient", "receipt_confirmations", ["recipient_user_id"])
    op.create_index("idx_receipt_status", "receipt_confirmations", ["status"])
    op.create_index("idx_receipt_created", "receipt_confirmations", ["created_at"])
    
    # AU-14: Session Audit
    op.create_table(
        "session_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("jwt_jti", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_method", sa.String(length=10), nullable=True),
        sa.Column("request_path", sa.String(length=1000), nullable=True),
        sa.Column("event_data", postgresql.JSON, nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("audit_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["auth_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_session_audit_session", "session_audit_events", ["session_id"])
    op.create_index("idx_session_audit_user", "session_audit_events", ["user_id", "org_id"])
    op.create_index("idx_session_audit_event_type", "session_audit_events", ["event_type"])
    op.create_index("idx_session_audit_timestamp", "session_audit_events", ["timestamp"])
    op.create_index("idx_session_audit_resource", "session_audit_events", ["resource_type", "resource_id"])
    
    # IA-2(11), IA-3, IA-5(2): Device Authentication
    op.create_table(
        "separate_device_auths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False, server_default="hardware_token"),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("device_serial", sa.String(length=255), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("hardware_info", postgresql.JSON, nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("registered_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registered_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_sep_device_user", "separate_device_auths", ["user_id", "org_id"])
    op.create_index("idx_sep_device_device", "separate_device_auths", ["device_id"])
    op.create_index("idx_sep_device_status", "separate_device_auths", ["status"])
    op.create_index("idx_sep_device_created", "separate_device_auths", ["registered_at"])
    
    op.create_table(
        "device_identifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("hardware_info", postgresql.JSON, nullable=True),
        sa.Column("software_info", postgresql.JSON, nullable=True),
        sa.Column("network_info", postgresql.JSON, nullable=True),
        sa.Column("is_trusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("trust_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trust_reason", sa.Text(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_access_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_device_id_org", "device_identifications", ["org_id"])
    op.create_index("idx_device_id_fingerprint", "device_identifications", ["device_fingerprint"])
    op.create_index("idx_device_id_user", "device_identifications", ["user_id"])
    op.create_index("idx_device_id_status", "device_identifications", ["status"])
    
    op.create_table(
        "pki_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("certificate_serial", sa.String(length=255), nullable=False),
        sa.Column("certificate_subject", sa.String(length=500), nullable=False),
        sa.Column("certificate_issuer", sa.String(length=500), nullable=False),
        sa.Column("certificate_thumbprint", sa.String(length=255), nullable=False),
        sa.Column("certificate_pem", sa.Text(), nullable=True),
        sa.Column("private_key_encrypted", sa.Text(), nullable=True),
        sa.Column("certificate_type", sa.String(length=50), nullable=False),
        sa.Column("is_cac_piv", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("registered_by_user_id", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("revocation_crl_url", sa.String(length=500), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_status", sa.String(length=50), nullable=True),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registered_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_pki_user", "pki_certificates", ["user_id", "org_id"])
    op.create_index("idx_pki_serial", "pki_certificates", ["certificate_serial"])
    op.create_index("idx_pki_status", "pki_certificates", ["status"])
    op.create_index("idx_pki_expires", "pki_certificates", ["expires_at"])
    
    op.create_table(
        "pki_authentication_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("certificate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("certificate_serial", sa.String(length=255), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("certificate_valid", sa.Boolean(), nullable=True),
        sa.Column("certificate_expired", sa.Boolean(), nullable=True),
        sa.Column("certificate_revoked", sa.Boolean(), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["certificate_id"], ["pki_certificates.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_pki_attempt_user", "pki_authentication_attempts", ["user_id", "org_id"])
    op.create_index("idx_pki_attempt_cert", "pki_authentication_attempts", ["certificate_id"])
    op.create_index("idx_pki_attempt_timestamp", "pki_authentication_attempts", ["attempted_at"])
    op.create_index("idx_pki_attempt_outcome", "pki_authentication_attempts", ["outcome"])
    
    # CM-4: Security Impact Analysis
    op.create_table(
        "security_impact_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("change_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("impact_level", sa.String(length=50), nullable=False),
        sa.Column("impact_description", sa.Text(), nullable=False),
        sa.Column("affected_components", postgresql.JSON, nullable=True),
        sa.Column("security_risks", postgresql.JSON, nullable=True),
        sa.Column("mitigation_measures", postgresql.JSON, nullable=True),
        sa.Column("security_test_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("security_test_requirements", postgresql.JSON, nullable=True),
        sa.Column("security_test_results", postgresql.JSON, nullable=True),
        sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["change_request_id"], ["configuration_change_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_impact_analysis_change", "security_impact_analyses", ["change_request_id"])
    op.create_index("idx_impact_analysis_org", "security_impact_analyses", ["org_id"])
    op.create_index("idx_impact_analysis_status", "security_impact_analyses", ["approval_status"])
    
    # CM-7: Least Functionality
    op.create_table(
        "service_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("service_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_unnecessary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ports", postgresql.JSON, nullable=True),
        sa.Column("protocols", postgresql.JSON, nullable=True),
        sa.Column("port_restrictions", postgresql.JSON, nullable=True),
        sa.Column("protocol_restrictions", postgresql.JSON, nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_service_org", "service_inventory", ["org_id"])
    op.create_index("idx_service_name", "service_inventory", ["service_name"])
    op.create_index("idx_service_status", "service_inventory", ["is_enabled"])
    
    # CM-8: Component Inventory
    op.create_table(
        "system_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("component_name", sa.String(length=255), nullable=False),
        sa.Column("component_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("discovery_method", sa.String(length=100), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("configuration", postgresql.JSON, nullable=True),
        sa.Column("dependencies", postgresql.JSON, nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_component_org_type", "system_components", ["org_id", "component_type"])
    op.create_index("idx_component_name", "system_components", ["component_name"])
    op.create_index("idx_component_status", "system_components", ["status"])
    op.create_index("idx_component_version", "system_components", ["version"])
    
    # CM-9: Configuration Management Plan
    op.create_table(
        "configuration_management_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plan_content", postgresql.JSON, nullable=False),
        sa.Column("plan_document", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_cm_plan_org", "configuration_management_plans", ["org_id"])
    op.create_index("idx_cm_plan_status", "configuration_management_plans", ["status"])
    op.create_index("idx_cm_plan_version", "configuration_management_plans", ["version"])
    
    # CM-10: Software Usage Restrictions
    op.create_table(
        "software_licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("software_name", sa.String(length=255), nullable=False),
        sa.Column("software_version", sa.String(length=100), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("license_type", sa.String(length=100), nullable=False),
        sa.Column("license_key", sa.String(length=500), nullable=True),
        sa.Column("license_agreement", sa.Text(), nullable=True),
        sa.Column("max_installations", sa.Integer(), nullable=True),
        sa.Column("current_installations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usage_restrictions", postgresql.JSON, nullable=True),
        sa.Column("license_status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("is_compliant", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_monitored", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_license_org", "software_licenses", ["org_id"])
    op.create_index("idx_license_software", "software_licenses", ["software_name"])
    op.create_index("idx_license_status", "software_licenses", ["license_status"])
    
    # CM-11: User-Installed Software
    op.create_table(
        "user_installed_software",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("software_name", sa.String(length=255), nullable=False),
        sa.Column("software_version", sa.String(length=100), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("installation_path", sa.String(length=1000), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("installation_method", sa.String(length=100), nullable=True),
        sa.Column("installation_reason", sa.Text(), nullable=True),
        sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("detection_method", sa.String(length=100), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("removal_reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rejected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["removed_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_user_software_user", "user_installed_software", ["user_id", "org_id"])
    op.create_index("idx_user_software_status", "user_installed_software", ["approval_status"])
    op.create_index("idx_user_software_installed", "user_installed_software", ["installed_at"])


def downgrade() -> None:
    """Drop all FedRAMP control tables"""
    op.drop_table("user_installed_software")
    op.drop_table("software_licenses")
    op.drop_table("configuration_management_plans")
    op.drop_table("system_components")
    op.drop_table("service_inventory")
    op.drop_table("security_impact_analyses")
    op.drop_table("pki_authentication_attempts")
    op.drop_table("pki_certificates")
    op.drop_table("device_identifications")
    op.drop_table("separate_device_auths")
    op.drop_table("session_audit_events")
    op.drop_table("receipt_confirmations")
    op.drop_table("digital_signatures")
    op.drop_table("audit_query_optimizations")
    op.drop_table("audit_patterns")
    op.drop_table("audit_reduction_reports")
    op.drop_table("audit_system_capacity")
    op.drop_table("audit_failure_responses")
