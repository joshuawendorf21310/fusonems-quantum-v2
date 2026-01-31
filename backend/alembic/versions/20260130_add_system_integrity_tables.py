"""Add System Integrity (SI) control tables for FedRAMP compliance

Revision ID: 20260130_system_integrity_tables
Revises: 20260130_vulnerability_tables
Create Date: 2026-01-30

This migration creates tables for FedRAMP System Integrity controls:
- SI-2: Flaw Remediation (patch_records)
- SI-3: Malicious Code Protection (malware_scans, signature_updates)
- SI-5: Security Alerts & Advisories (security_alerts)
- SI-6: Security Functionality Verification (security_functionality_tests)
- SI-7: Software & Information Integrity (integrity_verifications)
- SI-8: Spam Protection (spam_filter_results)
- SI-12: Information Handling & Retention (information_retention_policies, legal_holds, data_purge_records)
- SI-13: Predictable Failure Prevention (failure_prevention_actions)
- SI-16: Memory Protection (memory_protection_configs)
- SI-17: Fail-Safe Procedures (fail_safe_procedures)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_system_integrity_tables"
down_revision: Union[str, Sequence[str], None] = "20260130_vulnerability_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create System Integrity control tables"""
    
    # SI-2: Flaw Remediation - Patch Records
    op.create_table(
        "patch_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patch_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("cve_id", sa.String(length=32), nullable=True),
        sa.Column("vulnerability_id", sa.Integer(), nullable=True),
        sa.Column("component_type", sa.String(length=32), nullable=False),
        sa.Column("component_name", sa.String(length=256), nullable=False),
        sa.Column("current_version", sa.String(length=128), nullable=True),
        sa.Column("target_version", sa.String(length=128), nullable=False),
        sa.Column("patch_description", sa.Text(), nullable=True),
        sa.Column("patch_url", sa.String(length=512), nullable=True),
        sa.Column("patch_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_deployment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_breached", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("emergency_justification", sa.Text(), nullable=True),
        sa.Column("emergency_approver", sa.String(length=256), nullable=True),
        sa.Column("deployed_by", sa.String(length=256), nullable=True),
        sa.Column("deployment_method", sa.String(length=64), nullable=True),
        sa.Column("deployment_log", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(length=256), nullable=True),
        sa.Column("verification_method", sa.String(length=64), nullable=True),
        sa.Column("verification_result", sa.Text(), nullable=True),
        sa.Column("rollback_available", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rollback_instructions", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vulnerability_id"], ["vulnerabilities.id"], name="fk_patch_vulnerability_id"),
    )
    
    # SI-3: Malicious Code Protection - Malware Scans
    op.create_table(
        "malware_scans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scan_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("scan_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(length=512), nullable=True),
        sa.Column("file_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("threat_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("threat_name", sa.String(length=256), nullable=True),
        sa.Column("threat_type", sa.String(length=32), nullable=True),
        sa.Column("threat_signature", sa.String(length=256), nullable=True),
        sa.Column("scanner_engine", sa.String(length=64), nullable=True),
        sa.Column("scanner_version", sa.String(length=32), nullable=True),
        sa.Column("signature_version", sa.String(length=32), nullable=True),
        sa.Column("signature_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quarantined", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quarantine_path", sa.String(length=1024), nullable=True),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quarantined_by", sa.String(length=256), nullable=True),
        sa.Column("remediated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("remediation_action", sa.String(length=64), nullable=True),
        sa.Column("remediated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remediated_by", sa.String(length=256), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("upload_id", sa.String(length=128), nullable=True),
        sa.Column("scan_duration_ms", sa.Integer(), nullable=True),
        sa.Column("scan_details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    
    # SI-3: Signature Updates
    op.create_table(
        "signature_updates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("update_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("scanner_engine", sa.String(length=64), nullable=False),
        sa.Column("signature_version", sa.String(length=32), nullable=False),
        sa.Column("update_type", sa.String(length=32), nullable=False),
        sa.Column("update_size_bytes", sa.Integer(), nullable=True),
        sa.Column("update_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("installed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-5: Security Alerts
    op.create_table(
        "security_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_alert_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("affected_components", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("affected_versions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("cve_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=256), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=256), nullable=True),
        sa.Column("response_actions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("response_taken", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("distributed_to", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("distribution_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("references", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    
    # SI-6: Security Functionality Tests
    op.create_table(
        "security_functionality_tests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("test_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("test_name", sa.String(length=256), nullable=False),
        sa.Column("test_category", sa.String(length=64), nullable=False),
        sa.Column("test_type", sa.String(length=32), nullable=False),
        sa.Column("test_frequency", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("result_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("test_output", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("test_logs", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(length=256), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("related_components", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("related_vulnerabilities", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-7: Integrity Verifications
    op.create_table(
        "integrity_verifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("verification_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("check_type", sa.String(length=32), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_name", sa.String(length=512), nullable=False),
        sa.Column("target_path", sa.String(length=1024), nullable=True),
        sa.Column("target_version", sa.String(length=128), nullable=True),
        sa.Column("expected_hash", sa.String(length=64), nullable=True),
        sa.Column("actual_hash", sa.String(length=64), nullable=True),
        sa.Column("hash_match", sa.Boolean(), nullable=True),
        sa.Column("signed", sa.Boolean(), nullable=True),
        sa.Column("signer", sa.String(length=256), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=True),
        sa.Column("certificate_chain", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("certificate_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tamper_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tamper_details", sa.Text(), nullable=True),
        sa.Column("tamper_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("verification_passed", sa.Boolean(), nullable=True),
        sa.Column("verification_message", sa.Text(), nullable=True),
        sa.Column("baseline_id", sa.String(length=128), nullable=True),
        sa.Column("baseline_hash", sa.String(length=64), nullable=True),
        sa.Column("baseline_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.String(length=64), nullable=True),
        sa.Column("verification_tool", sa.String(length=128), nullable=True),
        sa.Column("verification_output", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-8: Spam Filter Results
    op.create_table(
        "spam_filter_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.String(length=256), nullable=False, unique=True),
        sa.Column("message_subject", sa.String(length=512), nullable=True),
        sa.Column("sender_email", sa.String(length=256), nullable=True),
        sa.Column("recipient_email", sa.String(length=256), nullable=True),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("spam_score", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("filter_engine", sa.String(length=64), nullable=True),
        sa.Column("filter_rules_matched", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("filter_action", sa.String(length=32), nullable=True),
        sa.Column("content_scanned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("links_checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attachments_scanned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("phishing_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("malware_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("threat_details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("action_taken", sa.String(length=32), nullable=True),
        sa.Column("action_taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    
    # SI-12: Retention Policies
    op.create_table(
        "information_retention_policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("policy_name", sa.String(length=256), nullable=False),
        sa.Column("policy_description", sa.Text(), nullable=True),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("data_category", sa.String(length=64), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("retention_period_days", sa.Integer(), nullable=False),
        sa.Column("retention_period_months", sa.Integer(), nullable=True),
        sa.Column("retention_period_years", sa.Integer(), nullable=True),
        sa.Column("auto_purge_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("purge_schedule", sa.String(length=64), nullable=True),
        sa.Column("purge_time", sa.String(length=8), nullable=True),
        sa.Column("legal_hold_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legal_hold_override", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("compliance_requirements", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-12: Legal Holds
    op.create_table(
        "legal_holds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hold_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("case_name", sa.String(length=256), nullable=False),
        sa.Column("case_number", sa.String(length=128), nullable=True),
        sa.Column("case_description", sa.Text(), nullable=True),
        sa.Column("data_types", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("user_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("date_range_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_range_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("legal_counsel", sa.String(length=256), nullable=True),
        sa.Column("court_order_number", sa.String(length=128), nullable=True),
        sa.Column("court_order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=256), nullable=False),
        sa.Column("released_by", sa.String(length=256), nullable=True),
        sa.Column("release_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # SI-12: Data Purge Records
    op.create_table(
        "data_purge_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("purge_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("policy_id", sa.String(length=128), nullable=True),
        sa.Column("purge_type", sa.String(length=32), nullable=False),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("data_category", sa.String(length=64), nullable=True),
        sa.Column("date_range_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_range_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("records_purged", sa.Integer(), nullable=True),
        sa.Column("records_skipped", sa.Integer(), nullable=True),
        sa.Column("purge_successful", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("executed_by", sa.String(length=256), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["policy_id"], ["information_retention_policies.policy_id"], name="fk_purge_policy_id"),
    )
    
    # SI-13: Failure Prevention Actions
    op.create_table(
        "failure_prevention_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("action_name", sa.String(length=256), nullable=False),
        sa.Column("action_description", sa.Text(), nullable=True),
        sa.Column("failure_type", sa.String(length=32), nullable=False),
        sa.Column("component_name", sa.String(length=256), nullable=False),
        sa.Column("component_type", sa.String(length=64), nullable=True),
        sa.Column("prevention_type", sa.String(length=32), nullable=False),
        sa.Column("redundancy_level", sa.Integer(), nullable=True),
        sa.Column("backup_frequency", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_verification_due", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failures_prevented", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_prevented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-16: Memory Protection Configs
    op.create_table(
        "memory_protection_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("config_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("system_name", sa.String(length=256), nullable=False),
        sa.Column("system_type", sa.String(length=64), nullable=False),
        sa.Column("aslr_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("dep_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("stack_protection", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("heap_protection", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("memory_isolation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="enabled"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_passed", sa.Boolean(), nullable=True),
        sa.Column("verification_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # SI-17: Fail-Safe Procedures
    op.create_table(
        "fail_safe_procedures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("procedure_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("procedure_name", sa.String(length=256), nullable=False),
        sa.Column("procedure_description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("trigger_conditions", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("threshold_value", sa.String(length=128), nullable=True),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("action_description", sa.Text(), nullable=False),
        sa.Column("action_script", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("times_triggered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_successful", sa.Boolean(), nullable=True),
        sa.Column("resolution_time_seconds", sa.Integer(), nullable=True),
        sa.Column("component_name", sa.String(length=256), nullable=True),
        sa.Column("system_name", sa.String(length=256), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index("ix_patch_records_patch_id", "patch_records", ["patch_id"], unique=True)
    op.create_index("idx_patch_status_priority", "patch_records", ["status", "priority"])
    op.create_index("idx_patch_sla_due", "patch_records", ["sla_due_date", "sla_breached"])
    
    op.create_index("ix_malware_scans_scan_id", "malware_scans", ["scan_id"], unique=True)
    op.create_index("idx_malware_threat_status", "malware_scans", ["threat_detected", "status"])
    op.create_index("idx_malware_quarantine", "malware_scans", ["quarantined", "quarantined_at"])
    
    op.create_index("ix_security_alerts_alert_id", "security_alerts", ["alert_id"], unique=True)
    op.create_index("idx_alert_severity_status", "security_alerts", ["severity", "status"])
    op.create_index("idx_alert_source_published", "security_alerts", ["source", "published_at"])
    
    op.create_index("ix_security_functionality_tests_test_id", "security_functionality_tests", ["test_id"], unique=True)
    op.create_index("idx_test_category_status", "security_functionality_tests", ["test_category", "status"])
    
    op.create_index("ix_integrity_verifications_verification_id", "integrity_verifications", ["verification_id"], unique=True)
    op.create_index("idx_integrity_status_type", "integrity_verifications", ["status", "check_type"])
    op.create_index("idx_integrity_tamper", "integrity_verifications", ["tamper_detected", "verified_at"])
    
    op.create_index("ix_spam_filter_results_message_id", "spam_filter_results", ["message_id"], unique=True)
    op.create_index("idx_spam_classification_score", "spam_filter_results", ["classification", "spam_score"])
    
    op.create_index("ix_information_retention_policies_policy_id", "information_retention_policies", ["policy_id"], unique=True)
    op.create_index("idx_retention_data_type_status", "information_retention_policies", ["data_type", "status"])
    
    op.create_index("ix_legal_holds_hold_id", "legal_holds", ["hold_id"], unique=True)
    op.create_index("idx_legal_hold_status", "legal_holds", ["status", "created_at"])
    
    op.create_index("ix_data_purge_records_purge_id", "data_purge_records", ["purge_id"], unique=True)
    op.create_index("idx_purge_data_type_created", "data_purge_records", ["data_type", "created_at"])
    
    op.create_index("ix_failure_prevention_actions_action_id", "failure_prevention_actions", ["action_id"], unique=True)
    op.create_index("idx_failure_type_component", "failure_prevention_actions", ["failure_type", "component_name"])
    
    op.create_index("ix_memory_protection_configs_config_id", "memory_protection_configs", ["config_id"], unique=True)
    op.create_index("idx_memory_system_status", "memory_protection_configs", ["system_name", "status"])
    
    op.create_index("ix_fail_safe_procedures_procedure_id", "fail_safe_procedures", ["procedure_id"], unique=True)
    op.create_index("idx_failsafe_status_enabled", "fail_safe_procedures", ["status", "enabled"])


def downgrade() -> None:
    """Drop System Integrity control tables"""
    
    # Drop indexes first
    op.drop_index("idx_failsafe_status_enabled", table_name="fail_safe_procedures")
    op.drop_index("ix_fail_safe_procedures_procedure_id", table_name="fail_safe_procedures")
    op.drop_index("idx_memory_system_status", table_name="memory_protection_configs")
    op.drop_index("ix_memory_protection_configs_config_id", table_name="memory_protection_configs")
    op.drop_index("idx_failure_type_component", table_name="failure_prevention_actions")
    op.drop_index("ix_failure_prevention_actions_action_id", table_name="failure_prevention_actions")
    op.drop_index("idx_purge_data_type_created", table_name="data_purge_records")
    op.drop_index("ix_data_purge_records_purge_id", table_name="data_purge_records")
    op.drop_index("idx_legal_hold_status", table_name="legal_holds")
    op.drop_index("ix_legal_holds_hold_id", table_name="legal_holds")
    op.drop_index("idx_retention_data_type_status", table_name="information_retention_policies")
    op.drop_index("ix_information_retention_policies_policy_id", table_name="information_retention_policies")
    op.drop_index("idx_spam_classification_score", table_name="spam_filter_results")
    op.drop_index("ix_spam_filter_results_message_id", table_name="spam_filter_results")
    op.drop_index("idx_integrity_tamper", table_name="integrity_verifications")
    op.drop_index("idx_integrity_status_type", table_name="integrity_verifications")
    op.drop_index("ix_integrity_verifications_verification_id", table_name="integrity_verifications")
    op.drop_index("idx_test_category_status", table_name="security_functionality_tests")
    op.drop_index("ix_security_functionality_tests_test_id", table_name="security_functionality_tests")
    op.drop_index("idx_alert_source_published", table_name="security_alerts")
    op.drop_index("idx_alert_severity_status", table_name="security_alerts")
    op.drop_index("ix_security_alerts_alert_id", table_name="security_alerts")
    op.drop_index("idx_malware_quarantine", table_name="malware_scans")
    op.drop_index("idx_malware_threat_status", table_name="malware_scans")
    op.drop_index("ix_malware_scans_scan_id", table_name="malware_scans")
    op.drop_index("idx_patch_sla_due", table_name="patch_records")
    op.drop_index("idx_patch_status_priority", table_name="patch_records")
    op.drop_index("ix_patch_records_patch_id", table_name="patch_records")
    
    # Drop tables
    op.drop_table("fail_safe_procedures")
    op.drop_table("memory_protection_configs")
    op.drop_table("failure_prevention_actions")
    op.drop_table("data_purge_records")
    op.drop_table("legal_holds")
    op.drop_table("information_retention_policies")
    op.drop_table("spam_filter_results")
    op.drop_table("integrity_verifications")
    op.drop_table("security_functionality_tests")
    op.drop_table("security_alerts")
    op.drop_table("signature_updates")
    op.drop_table("malware_scans")
    op.drop_table("patch_records")
