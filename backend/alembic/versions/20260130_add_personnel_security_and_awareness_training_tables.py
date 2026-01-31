"""Add Personnel Security (PS) and Awareness & Training (AT) FedRAMP Tables

Revision ID: 20260130_ps_at_tables
Revises: 20260130_config_mgmt
Create Date: 2026-01-30

This migration implements tables for FedRAMP compliance:
- PS-2 through PS-8: Personnel Security controls
- AT-2 through AT-5: Awareness & Training controls
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260130_ps_at_tables"
down_revision: Union[str, Sequence[str], None] = "20260130_config_mgmt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # PS-2: Position Risk Designation
    # ============================================================================
    op.create_table(
        "position_risk_designations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("position_title", sa.String(255), nullable=False),
        sa.Column("position_id", sa.String(100), nullable=False, unique=True),
        sa.Column("department", sa.String(255), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("risk_justification", sa.Text(), nullable=False),
        sa.Column("last_review_date", sa.Date(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requires_clearance", sa.Boolean(), default=False),
        sa.Column("clearance_level", sa.String(100), nullable=True),
        sa.Column("special_requirements", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_position_risk_designations_org_id", "position_risk_designations", ["org_id"])
    op.create_index("ix_position_risk_designations_position_id", "position_risk_designations", ["position_id"], unique=True)
    op.create_index("ix_position_risk_designations_risk_level", "position_risk_designations", ["risk_level"])
    op.create_index("ix_position_risk_designations_next_review_date", "position_risk_designations", ["next_review_date"])
    op.create_index("ix_position_risk_org_position", "position_risk_designations", ["org_id", "position_id"])

    # ============================================================================
    # PS-3: Personnel Screening
    # ============================================================================
    op.create_table(
        "personnel_screenings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("position_risk_id", sa.Integer(), nullable=False),
        sa.Column("screening_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("background_check_required", sa.Boolean(), default=True),
        sa.Column("background_check_completed", sa.Boolean(), default=False),
        sa.Column("background_check_date", sa.Date(), nullable=True),
        sa.Column("background_check_result", sa.String(255), nullable=True),
        sa.Column("credit_check_required", sa.Boolean(), default=False),
        sa.Column("credit_check_completed", sa.Boolean(), default=False),
        sa.Column("credit_check_date", sa.Date(), nullable=True),
        sa.Column("drug_test_required", sa.Boolean(), default=False),
        sa.Column("drug_test_completed", sa.Boolean(), default=False),
        sa.Column("drug_test_date", sa.Date(), nullable=True),
        sa.Column("drug_test_result", sa.String(255), nullable=True),
        sa.Column("reference_check_required", sa.Boolean(), default=True),
        sa.Column("reference_check_completed", sa.Boolean(), default=False),
        sa.Column("reference_check_date", sa.Date(), nullable=True),
        sa.Column("screening_initiated_date", sa.Date(), nullable=False),
        sa.Column("screening_completed_date", sa.Date(), nullable=True),
        sa.Column("screening_expiration_date", sa.Date(), nullable=True),
        sa.Column("rescreening_required", sa.Boolean(), default=True),
        sa.Column("rescreening_frequency_months", sa.Integer(), default=36),
        sa.Column("next_rescreening_date", sa.Date(), nullable=True),
        sa.Column("screening_result", sa.Text(), nullable=True),
        sa.Column("screening_notes", sa.Text(), nullable=True),
        sa.Column("screening_officer_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_risk_id"], ["position_risk_designations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["screening_officer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_screenings_org_id", "personnel_screenings", ["org_id"])
    op.create_index("ix_personnel_screenings_user_id", "personnel_screenings", ["user_id"])
    op.create_index("ix_personnel_screenings_status", "personnel_screenings", ["status"])
    op.create_index("ix_screening_org_user", "personnel_screenings", ["org_id", "user_id"])
    op.create_index("ix_screening_expiration", "personnel_screenings", ["screening_expiration_date"])

    # ============================================================================
    # PS-4: Personnel Termination
    # ============================================================================
    op.create_table(
        "personnel_terminations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("termination_date", sa.Date(), nullable=False),
        sa.Column("termination_reason", sa.String(255), nullable=False),
        sa.Column("termination_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="initiated"),
        sa.Column("access_revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("systems_access_revoked", postgresql.JSON(), nullable=True),
        sa.Column("exit_interview_required", sa.Boolean(), default=True),
        sa.Column("exit_interview_completed", sa.Boolean(), default=False),
        sa.Column("exit_interview_date", sa.Date(), nullable=True),
        sa.Column("exit_interview_notes", sa.Text(), nullable=True),
        sa.Column("exit_interview_conducted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assets_returned", sa.Boolean(), default=False),
        sa.Column("assets_returned_date", sa.Date(), nullable=True),
        sa.Column("assets_list", postgresql.JSON(), nullable=True),
        sa.Column("assets_returned_list", postgresql.JSON(), nullable=True),
        sa.Column("final_paycheck_processed", sa.Boolean(), default=False),
        sa.Column("benefits_terminated", sa.Boolean(), default=False),
        sa.Column("cobra_notification_sent", sa.Boolean(), default=False),
        sa.Column("termination_initiated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("termination_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["access_revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exit_interview_conducted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["termination_initiated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_terminations_org_id", "personnel_terminations", ["org_id"])
    op.create_index("ix_personnel_terminations_user_id", "personnel_terminations", ["user_id"])
    op.create_index("ix_personnel_terminations_status", "personnel_terminations", ["status"])
    op.create_index("ix_termination_org_user", "personnel_terminations", ["org_id", "user_id"])
    op.create_index("ix_termination_date", "personnel_terminations", ["termination_date"])

    # ============================================================================
    # PS-5: Personnel Transfer
    # ============================================================================
    op.create_table(
        "personnel_transfers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("transfer_reason", sa.String(255), nullable=False),
        sa.Column("from_position_id", sa.Integer(), nullable=True),
        sa.Column("from_department", sa.String(255), nullable=True),
        sa.Column("from_role", sa.String(100), nullable=True),
        sa.Column("to_position_id", sa.Integer(), nullable=False),
        sa.Column("to_department", sa.String(255), nullable=False),
        sa.Column("to_role", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="initiated"),
        sa.Column("access_adjusted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_adjusted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("access_changes", postgresql.JSON(), nullable=True),
        sa.Column("role_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("role_changes", postgresql.JSON(), nullable=True),
        sa.Column("requires_new_screening", sa.Boolean(), default=False),
        sa.Column("new_screening_id", sa.Integer(), nullable=True),
        sa.Column("transfer_initiated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("transfer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_position_id"], ["position_risk_designations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_position_id"], ["position_risk_designations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["access_adjusted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["new_screening_id"], ["personnel_screenings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["transfer_initiated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_transfers_org_id", "personnel_transfers", ["org_id"])
    op.create_index("ix_personnel_transfers_user_id", "personnel_transfers", ["user_id"])
    op.create_index("ix_personnel_transfers_status", "personnel_transfers", ["status"])
    op.create_index("ix_transfer_org_user", "personnel_transfers", ["org_id", "user_id"])
    op.create_index("ix_transfer_date", "personnel_transfers", ["transfer_date"])

    # ============================================================================
    # PS-6: Access Agreements
    # ============================================================================
    op.create_table(
        "access_agreements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agreement_type", sa.String(100), nullable=False),
        sa.Column("agreement_title", sa.String(255), nullable=False),
        sa.Column("agreement_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("signature_method", sa.String(50), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("requires_renewal", sa.Boolean(), default=True),
        sa.Column("renewal_frequency_months", sa.Integer(), default=12),
        sa.Column("next_renewal_date", sa.Date(), nullable=True),
        sa.Column("agreement_document_path", sa.String(500), nullable=True),
        sa.Column("signed_document_path", sa.String(500), nullable=True),
        sa.Column("agreement_content_hash", sa.String(255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_agreements_org_id", "access_agreements", ["org_id"])
    op.create_index("ix_access_agreements_user_id", "access_agreements", ["user_id"])
    op.create_index("ix_access_agreements_agreement_type", "access_agreements", ["agreement_type"])
    op.create_index("ix_access_agreements_status", "access_agreements", ["status"])
    op.create_index("ix_agreement_org_user", "access_agreements", ["org_id", "user_id"])
    op.create_index("ix_agreement_expiration", "access_agreements", ["expiration_date"])
    op.create_index("ix_agreement_renewal", "access_agreements", ["next_renewal_date"])

    # ============================================================================
    # PS-7: Third-Party Personnel Security
    # ============================================================================
    op.create_table(
        "third_party_personnel",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("vendor_contact_name", sa.String(255), nullable=False),
        sa.Column("vendor_contact_email", sa.String(255), nullable=False),
        sa.Column("vendor_contact_phone", sa.String(50), nullable=True),
        sa.Column("personnel_name", sa.String(255), nullable=False),
        sa.Column("personnel_email", sa.String(255), nullable=False),
        sa.Column("personnel_phone", sa.String(50), nullable=True),
        sa.Column("personnel_role", sa.String(255), nullable=False),
        sa.Column("contract_number", sa.String(100), nullable=True),
        sa.Column("contract_start_date", sa.Date(), nullable=False),
        sa.Column("contract_end_date", sa.Date(), nullable=True),
        sa.Column("security_clearance_required", sa.Boolean(), default=False),
        sa.Column("security_clearance_level", sa.String(100), nullable=True),
        sa.Column("security_clearance_verified", sa.Boolean(), default=False),
        sa.Column("background_check_required", sa.Boolean(), default=True),
        sa.Column("background_check_completed", sa.Boolean(), default=False),
        sa.Column("background_check_date", sa.Date(), nullable=True),
        sa.Column("nda_required", sa.Boolean(), default=True),
        sa.Column("nda_signed", sa.Boolean(), default=False),
        sa.Column("nda_signed_date", sa.Date(), nullable=True),
        sa.Column("system_access_granted", sa.Boolean(), default=False),
        sa.Column("systems_accessed", postgresql.JSON(), nullable=True),
        sa.Column("access_granted_date", sa.Date(), nullable=True),
        sa.Column("access_revoked_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("compliance_verified", sa.Boolean(), default=False),
        sa.Column("compliance_verified_date", sa.Date(), nullable=True),
        sa.Column("compliance_verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["compliance_verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_third_party_personnel_org_id", "third_party_personnel", ["org_id"])
    op.create_index("ix_third_party_personnel_vendor_name", "third_party_personnel", ["vendor_name"])
    op.create_index("ix_third_party_personnel_personnel_email", "third_party_personnel", ["personnel_email"])
    op.create_index("ix_third_party_personnel_status", "third_party_personnel", ["status"])
    op.create_index("ix_third_party_org_vendor", "third_party_personnel", ["org_id", "vendor_name"])
    op.create_index("ix_third_party_contract", "third_party_personnel", ["contract_end_date"])

    # ============================================================================
    # PS-8: Personnel Sanctions
    # ============================================================================
    op.create_table(
        "personnel_sanctions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("violation_type", sa.String(100), nullable=False),
        sa.Column("violation_description", sa.Text(), nullable=False),
        sa.Column("violation_date", sa.Date(), nullable=False),
        sa.Column("sanction_type", sa.String(100), nullable=False),
        sa.Column("sanction_severity", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("sanction_start_date", sa.Date(), nullable=False),
        sa.Column("sanction_end_date", sa.Date(), nullable=True),
        sa.Column("sanction_conditions", sa.Text(), nullable=True),
        sa.Column("remediation_required", sa.Boolean(), default=True),
        sa.Column("remediation_plan", sa.Text(), nullable=True),
        sa.Column("remediation_completed", sa.Boolean(), default=False),
        sa.Column("remediation_completed_date", sa.Date(), nullable=True),
        sa.Column("appeal_filed", sa.Boolean(), default=False),
        sa.Column("appeal_date", sa.Date(), nullable=True),
        sa.Column("appeal_decision", sa.String(255), nullable=True),
        sa.Column("appeal_decision_date", sa.Date(), nullable=True),
        sa.Column("incident_report_path", sa.String(500), nullable=True),
        sa.Column("supporting_documents", postgresql.JSON(), nullable=True),
        sa.Column("reported_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sanctioned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reported_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sanctioned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_sanctions_org_id", "personnel_sanctions", ["org_id"])
    op.create_index("ix_personnel_sanctions_user_id", "personnel_sanctions", ["user_id"])
    op.create_index("ix_personnel_sanctions_violation_type", "personnel_sanctions", ["violation_type"])
    op.create_index("ix_personnel_sanctions_status", "personnel_sanctions", ["status"])
    op.create_index("ix_sanction_org_user", "personnel_sanctions", ["org_id", "user_id"])
    op.create_index("ix_sanction_violation_date", "personnel_sanctions", ["violation_date"])

    # ============================================================================
    # AT-2: Security Awareness Training
    # ============================================================================
    op.create_table(
        "security_awareness_trainings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("module_code", sa.String(100), nullable=False, unique=True),
        sa.Column("module_name", sa.String(255), nullable=False),
        sa.Column("module_description", sa.Text(), nullable=True),
        sa.Column("module_category", sa.String(100), nullable=False),
        sa.Column("delivery_method", sa.String(50), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("training_content_path", sa.String(500), nullable=True),
        sa.Column("mandatory", sa.Boolean(), default=True),
        sa.Column("required_frequency_months", sa.Integer(), default=12),
        sa.Column("passing_score_percentage", sa.Float(), default=80.0),
        sa.Column("reminder_days_before_due", postgresql.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_awareness_trainings_org_id", "security_awareness_trainings", ["org_id"])
    op.create_index("ix_security_awareness_trainings_module_code", "security_awareness_trainings", ["module_code"], unique=True)
    op.create_index("ix_security_awareness_trainings_mandatory", "security_awareness_trainings", ["mandatory"])
    op.create_index("ix_security_awareness_trainings_active", "security_awareness_trainings", ["active"])
    op.create_index("ix_awareness_training_org_active", "security_awareness_trainings", ["org_id", "active"])

    op.create_table(
        "security_awareness_training_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_percentage", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), default=0),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_sent_30_days", sa.Boolean(), default=False),
        sa.Column("reminder_sent_15_days", sa.Boolean(), default=False),
        sa.Column("reminder_sent_7_days", sa.Boolean(), default=False),
        sa.Column("reminder_sent_overdue", sa.Boolean(), default=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_id"], ["security_awareness_trainings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_awareness_training_assignments_org_id", "security_awareness_training_assignments", ["org_id"])
    op.create_index("ix_security_awareness_training_assignments_user_id", "security_awareness_training_assignments", ["user_id"])
    op.create_index("ix_security_awareness_training_assignments_status", "security_awareness_training_assignments", ["status"])
    op.create_index("ix_awareness_assignment_org_user", "security_awareness_training_assignments", ["org_id", "user_id"])
    op.create_index("ix_awareness_assignment_due", "security_awareness_training_assignments", ["due_date"])
    op.create_index("ix_awareness_assignment_status", "security_awareness_training_assignments", ["status"])

    # ============================================================================
    # AT-3: Role-Based Security Training
    # ============================================================================
    op.create_table(
        "role_based_security_trainings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("training_code", sa.String(100), nullable=False, unique=True),
        sa.Column("training_name", sa.String(255), nullable=False),
        sa.Column("training_description", sa.Text(), nullable=True),
        sa.Column("training_category", sa.String(100), nullable=False),
        sa.Column("required_role", sa.String(100), nullable=False),
        sa.Column("required_roles", postgresql.JSON(), nullable=True),
        sa.Column("delivery_method", sa.String(50), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("training_content_path", sa.String(500), nullable=True),
        sa.Column("mandatory", sa.Boolean(), default=True),
        sa.Column("required_frequency_months", sa.Integer(), default=12),
        sa.Column("passing_score_percentage", sa.Float(), default=80.0),
        sa.Column("requires_competency_validation", sa.Boolean(), default=False),
        sa.Column("competency_level_required", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_role_based_security_trainings_org_id", "role_based_security_trainings", ["org_id"])
    op.create_index("ix_role_based_security_trainings_training_code", "role_based_security_trainings", ["training_code"], unique=True)
    op.create_index("ix_role_based_security_trainings_required_role", "role_based_security_trainings", ["required_role"])
    op.create_index("ix_role_based_security_trainings_active", "role_based_security_trainings", ["active"])
    op.create_index("ix_role_training_org_role", "role_based_security_trainings", ["org_id", "required_role"])

    op.create_table(
        "role_based_training_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_percentage", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("competency_assessed", sa.Boolean(), default=False),
        sa.Column("competency_level_achieved", sa.String(50), nullable=True),
        sa.Column("competency_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("competency_assessed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), default=0),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_id"], ["role_based_security_trainings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competency_assessed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_role_based_training_assignments_org_id", "role_based_training_assignments", ["org_id"])
    op.create_index("ix_role_based_training_assignments_user_id", "role_based_training_assignments", ["user_id"])
    op.create_index("ix_role_based_training_assignments_status", "role_based_training_assignments", ["status"])
    op.create_index("ix_role_assignment_org_user", "role_based_training_assignments", ["org_id", "user_id"])
    op.create_index("ix_role_assignment_due", "role_based_training_assignments", ["due_date"])
    op.create_index("ix_role_assignment_status", "role_based_training_assignments", ["status"])

    # ============================================================================
    # AT-4: Security Training Records
    # ============================================================================
    op.create_table(
        "security_training_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("training_type", sa.String(100), nullable=False),
        sa.Column("training_name", sa.String(255), nullable=False),
        sa.Column("training_provider", sa.String(255), nullable=True),
        sa.Column("training_code", sa.String(100), nullable=True),
        sa.Column("training_date", sa.Date(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("delivery_method", sa.String(50), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("score_percentage", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("certificate_issued", sa.Boolean(), default=False),
        sa.Column("certificate_number", sa.String(100), nullable=True),
        sa.Column("certificate_issue_date", sa.Date(), nullable=True),
        sa.Column("certificate_expiration_date", sa.Date(), nullable=True),
        sa.Column("certificate_document_path", sa.String(500), nullable=True),
        sa.Column("competency_level_achieved", sa.String(50), nullable=True),
        sa.Column("competency_validated", sa.Boolean(), default=False),
        sa.Column("competency_validated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("external_training", sa.Boolean(), default=False),
        sa.Column("external_provider_name", sa.String(255), nullable=True),
        sa.Column("external_training_id", sa.String(100), nullable=True),
        sa.Column("ceu_credits", sa.Float(), default=0.0),
        sa.Column("cme_credits", sa.Float(), default=0.0),
        sa.Column("compliance_required", sa.Boolean(), default=True),
        sa.Column("compliance_status", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competency_validated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_training_records_org_id", "security_training_records", ["org_id"])
    op.create_index("ix_security_training_records_user_id", "security_training_records", ["user_id"])
    op.create_index("ix_security_training_records_training_type", "security_training_records", ["training_type"])
    op.create_index("ix_security_training_records_status", "security_training_records", ["status"])
    op.create_index("ix_security_training_records_training_code", "security_training_records", ["training_code"])
    op.create_index("ix_security_training_records_certificate_number", "security_training_records", ["certificate_number"])
    op.create_index("ix_training_record_org_user", "security_training_records", ["org_id", "user_id"])
    op.create_index("ix_training_record_date", "security_training_records", ["training_date"])
    op.create_index("ix_training_record_certificate", "security_training_records", ["certificate_expiration_date"])

    # ============================================================================
    # AT-5: Contacts with Security Groups
    # ============================================================================
    op.create_table(
        "security_group_contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("security_group_name", sa.String(255), nullable=False),
        sa.Column("security_group_type", sa.String(100), nullable=False),
        sa.Column("security_group_website", sa.String(500), nullable=True),
        sa.Column("security_group_contact_email", sa.String(255), nullable=True),
        sa.Column("contact_type", sa.String(50), nullable=False),
        sa.Column("event_name", sa.String(255), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("event_location", sa.String(255), nullable=True),
        sa.Column("event_duration_days", sa.Integer(), nullable=True),
        sa.Column("membership_status", sa.String(50), nullable=True),
        sa.Column("membership_start_date", sa.Date(), nullable=True),
        sa.Column("membership_end_date", sa.Date(), nullable=True),
        sa.Column("membership_level", sa.String(100), nullable=True),
        sa.Column("participation_role", sa.String(100), nullable=True),
        sa.Column("presentation_title", sa.String(500), nullable=True),
        sa.Column("presentation_date", sa.Date(), nullable=True),
        sa.Column("knowledge_shared", sa.Boolean(), default=False),
        sa.Column("knowledge_shared_date", sa.Date(), nullable=True),
        sa.Column("knowledge_shared_summary", sa.Text(), nullable=True),
        sa.Column("knowledge_shared_with_team", sa.Boolean(), default=False),
        sa.Column("benefits_received", sa.Text(), nullable=True),
        sa.Column("outcomes_achieved", sa.Text(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), default=False),
        sa.Column("follow_up_notes", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_group_contacts_org_id", "security_group_contacts", ["org_id"])
    op.create_index("ix_security_group_contacts_user_id", "security_group_contacts", ["user_id"])
    op.create_index("ix_security_group_contacts_security_group_name", "security_group_contacts", ["security_group_name"])
    op.create_index("ix_security_group_contacts_contact_type", "security_group_contacts", ["contact_type"])
    op.create_index("ix_security_group_contacts_event_date", "security_group_contacts", ["event_date"])
    op.create_index("ix_security_group_contacts_membership_end_date", "security_group_contacts", ["membership_end_date"])
    op.create_index("ix_security_contact_org_user", "security_group_contacts", ["org_id", "user_id"])
    op.create_index("ix_security_contact_group", "security_group_contacts", ["security_group_name"])
    op.create_index("ix_security_contact_type", "security_group_contacts", ["contact_type"])
    op.create_index("ix_security_contact_event", "security_group_contacts", ["event_date"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("security_group_contacts")
    op.drop_table("security_training_records")
    op.drop_table("role_based_training_assignments")
    op.drop_table("role_based_security_trainings")
    op.drop_table("security_awareness_training_assignments")
    op.drop_table("security_awareness_trainings")
    op.drop_table("personnel_sanctions")
    op.drop_table("third_party_personnel")
    op.drop_table("access_agreements")
    op.drop_table("personnel_transfers")
    op.drop_table("personnel_terminations")
    op.drop_table("personnel_screenings")
    op.drop_table("position_risk_designations")
