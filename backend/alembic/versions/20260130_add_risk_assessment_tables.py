"""Add risk assessment tables for FedRAMP RA-2, RA-3, RA-6 compliance

Revision ID: 20260130_risk_assessment_tables
Revises: 20260130_vulnerability_tables
Create Date: 2026-01-30

This migration creates tables for FedRAMP Risk Assessment controls:
- RA-2: Security Categorization (FIPS 199)
  - system_categorizations: System-level security categorization
  - data_categorizations: Data-level security categorization
- RA-3: Risk Assessment
  - risk_assessments: Comprehensive risk assessment records
  - risk_factors: Individual risk factors (threat-vulnerability pairs)
  - treatment_plans: Risk treatment plans
- RA-6: Technical Surveillance Countermeasures
  - surveillance_events: Surveillance detection and countermeasure events

All tables support comprehensive audit logging and compliance reporting.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_risk_assessment_tables"
down_revision: Union[str, Sequence[str], None] = "20260130_vulnerability_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create risk assessment tables"""
    
    # ========================================================================
    # RA-2: Security Categorization (FIPS 199)
    # ========================================================================
    
    # Create system_categorizations table
    op.create_table(
        "system_categorizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("system_name", sa.String(length=255), nullable=False),
        sa.Column("system_description", sa.Text(), nullable=True),
        sa.Column("system_owner", sa.String(length=255), nullable=True),
        sa.Column("system_id", sa.String(length=128), nullable=True, unique=True),
        sa.Column("confidentiality_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("integrity_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("availability_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("overall_impact_level", sa.String(length=32), nullable=False),
        sa.Column("categorization_rationale", sa.Text(), nullable=True),
        sa.Column("categorization_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("categorized_by", sa.String(length=255), nullable=True),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("approval_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create data_categorizations table
    op.create_table(
        "data_categorizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("system_categorization_id", sa.Integer(), nullable=False),
        sa.Column("data_type", sa.String(length=255), nullable=False),
        sa.Column("data_description", sa.Text(), nullable=True),
        sa.Column("data_classification", sa.String(length=100), nullable=True),
        sa.Column("confidentiality_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("integrity_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("availability_impact", sa.String(length=32), nullable=False, server_default="low"),
        sa.Column("overall_impact_level", sa.String(length=32), nullable=False),
        sa.Column("categorization_rationale", sa.Text(), nullable=True),
        sa.Column("categorization_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("categorized_by", sa.String(length=255), nullable=True),
        sa.Column("data_volume", sa.String(length=100), nullable=True),
        sa.Column("sensitivity_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["system_categorization_id"],
            ["system_categorizations.id"],
            name="fk_data_categorizations_system_id",
            ondelete="CASCADE"
        ),
    )
    
    # ========================================================================
    # RA-3: Risk Assessment
    # ========================================================================
    
    # Create risk_assessments table
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("assessment_name", sa.String(length=255), nullable=False),
        sa.Column("assessment_description", sa.Text(), nullable=True),
        sa.Column("assessment_type", sa.String(length=100), nullable=False),
        sa.Column("scope_description", sa.Text(), nullable=True),
        sa.Column("systems_in_scope", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("data_types_in_scope", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("assessment_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("assessed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("overall_risk_level", sa.String(length=32), nullable=False),
        sa.Column("overall_risk_score", sa.Float(), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("key_findings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("recommendations", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("next_assessment_due", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create risk_factors table
    op.create_table(
        "risk_factors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("risk_assessment_id", sa.Integer(), nullable=False),
        sa.Column("risk_name", sa.String(length=255), nullable=False),
        sa.Column("risk_description", sa.Text(), nullable=True),
        sa.Column("threat_category", sa.String(length=100), nullable=False),
        sa.Column("threat_description", sa.Text(), nullable=True),
        sa.Column("threat_source", sa.String(length=255), nullable=True),
        sa.Column("threat_capability", sa.String(length=100), nullable=True),
        sa.Column("vulnerability_category", sa.String(length=100), nullable=False),
        sa.Column("vulnerability_description", sa.Text(), nullable=True),
        sa.Column("vulnerability_id", sa.String(length=128), nullable=True),
        sa.Column("affected_systems", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("likelihood", sa.String(length=32), nullable=False),
        sa.Column("likelihood_score", sa.Float(), nullable=True),
        sa.Column("impact", sa.String(length=32), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_scenario", sa.Text(), nullable=True),
        sa.Column("potential_impact", sa.Text(), nullable=True),
        sa.Column("existing_controls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("control_effectiveness", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["risk_assessment_id"],
            ["risk_assessments.id"],
            name="fk_risk_factors_assessment_id",
            ondelete="CASCADE"
        ),
    )
    
    # Create treatment_plans table
    op.create_table(
        "treatment_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("risk_assessment_id", sa.Integer(), nullable=False),
        sa.Column("risk_factor_id", sa.Integer(), nullable=True),
        sa.Column("plan_name", sa.String(length=255), nullable=False),
        sa.Column("plan_description", sa.Text(), nullable=True),
        sa.Column("treatment_strategy", sa.String(length=32), nullable=False),
        sa.Column("treatment_actions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("responsible_party", sa.String(length=255), nullable=True),
        sa.Column("target_completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("implementation_status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("implementation_progress", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("implementation_notes", sa.Text(), nullable=True),
        sa.Column("residual_risk_level", sa.String(length=32), nullable=True),
        sa.Column("residual_risk_score", sa.Float(), nullable=True),
        sa.Column("effectiveness_assessment", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("resources_required", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["risk_assessment_id"],
            ["risk_assessments.id"],
            name="fk_treatment_plans_assessment_id",
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["risk_factor_id"],
            ["risk_factors.id"],
            name="fk_treatment_plans_risk_factor_id",
            ondelete="SET NULL"
        ),
    )
    
    # ========================================================================
    # RA-6: Technical Surveillance Countermeasures
    # ========================================================================
    
    # Create surveillance_events table
    op.create_table(
        "surveillance_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_name", sa.String(length=255), nullable=False),
        sa.Column("event_description", sa.Text(), nullable=True),
        sa.Column("surveillance_type", sa.String(length=100), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("detected_by", sa.String(length=255), nullable=True),
        sa.Column("detection_method", sa.String(length=255), nullable=True),
        sa.Column("detection_source", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("affected_systems", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("affected_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("threat_source", sa.String(length=255), nullable=True),
        sa.Column("threat_capability", sa.String(length=100), nullable=True),
        sa.Column("threat_intent", sa.String(length=100), nullable=True),
        sa.Column("potential_impact", sa.Text(), nullable=True),
        sa.Column("data_exposed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("systems_compromised", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("impact_level", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="detected"),
        sa.Column("response_actions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("countermeasures_applied", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("investigation_notes", sa.Text(), nullable=True),
        sa.Column("investigated_by", sa.String(length=255), nullable=True),
        sa.Column("investigation_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=255), nullable=True),
        sa.Column("related_events", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # ========================================================================
    # Create Indexes
    # ========================================================================
    
    # RA-2 Indexes
    op.create_index("ix_system_categorizations_system_name", "system_categorizations", ["system_name"])
    op.create_index("ix_system_categorizations_system_id", "system_categorizations", ["system_id"], unique=True)
    op.create_index("ix_system_categorizations_overall_impact_level", "system_categorizations", ["overall_impact_level"])
    op.create_index("ix_system_categorizations_is_active", "system_categorizations", ["is_active"])
    op.create_index("idx_system_cat_impact", "system_categorizations", ["overall_impact_level", "is_active"])
    
    op.create_index("ix_data_categorizations_system_id", "data_categorizations", ["system_categorization_id"])
    op.create_index("ix_data_categorizations_data_type", "data_categorizations", ["data_type"])
    op.create_index("ix_data_categorizations_overall_impact_level", "data_categorizations", ["overall_impact_level"])
    op.create_index("ix_data_categorizations_is_active", "data_categorizations", ["is_active"])
    op.create_index("idx_data_cat_system", "data_categorizations", ["system_categorization_id", "data_type"])
    op.create_index("idx_data_cat_impact", "data_categorizations", ["overall_impact_level", "is_active"])
    
    # RA-3 Indexes
    op.create_index("ix_risk_assessments_assessment_name", "risk_assessments", ["assessment_name"])
    op.create_index("ix_risk_assessments_assessment_date", "risk_assessments", ["assessment_date"])
    op.create_index("ix_risk_assessments_status", "risk_assessments", ["status"])
    op.create_index("ix_risk_assessments_overall_risk_level", "risk_assessments", ["overall_risk_level"])
    op.create_index("idx_risk_assessment_status_date", "risk_assessments", ["status", "assessment_date"])
    op.create_index("idx_risk_assessment_level", "risk_assessments", ["overall_risk_level", "status"])
    
    op.create_index("ix_risk_factors_assessment_id", "risk_factors", ["risk_assessment_id"])
    op.create_index("ix_risk_factors_risk_name", "risk_factors", ["risk_name"])
    op.create_index("ix_risk_factors_threat_category", "risk_factors", ["threat_category"])
    op.create_index("ix_risk_factors_vulnerability_category", "risk_factors", ["vulnerability_category"])
    op.create_index("ix_risk_factors_likelihood", "risk_factors", ["likelihood"])
    op.create_index("ix_risk_factors_impact", "risk_factors", ["impact"])
    op.create_index("ix_risk_factors_risk_level", "risk_factors", ["risk_level"])
    op.create_index("ix_risk_factors_status", "risk_factors", ["status"])
    op.create_index("idx_risk_factor_assessment_status", "risk_factors", ["risk_assessment_id", "status"])
    op.create_index("idx_risk_factor_level", "risk_factors", ["risk_level", "status"])
    op.create_index("idx_risk_factor_threat_vuln", "risk_factors", ["threat_category", "vulnerability_category"])
    
    op.create_index("ix_treatment_plans_assessment_id", "treatment_plans", ["risk_assessment_id"])
    op.create_index("ix_treatment_plans_risk_factor_id", "treatment_plans", ["risk_factor_id"])
    op.create_index("ix_treatment_plans_plan_name", "treatment_plans", ["plan_name"])
    op.create_index("ix_treatment_plans_treatment_strategy", "treatment_plans", ["treatment_strategy"])
    op.create_index("ix_treatment_plans_implementation_status", "treatment_plans", ["implementation_status"])
    op.create_index("idx_treatment_plan_assessment_status", "treatment_plans", ["risk_assessment_id", "implementation_status"])
    op.create_index("idx_treatment_plan_strategy", "treatment_plans", ["treatment_strategy", "implementation_status"])
    
    # RA-6 Indexes
    op.create_index("ix_surveillance_events_event_name", "surveillance_events", ["event_name"])
    op.create_index("ix_surveillance_events_surveillance_type", "surveillance_events", ["surveillance_type"])
    op.create_index("ix_surveillance_events_detected_at", "surveillance_events", ["detected_at"])
    op.create_index("ix_surveillance_events_status", "surveillance_events", ["status"])
    op.create_index("idx_surveillance_type_status", "surveillance_events", ["surveillance_type", "status"])
    op.create_index("idx_surveillance_detected", "surveillance_events", ["detected_at", "status"])
    op.create_index("idx_surveillance_status", "surveillance_events", ["status", "detected_at"])


def downgrade() -> None:
    """Drop risk assessment tables"""
    
    # Drop indexes
    op.drop_index("idx_surveillance_status", table_name="surveillance_events")
    op.drop_index("idx_surveillance_detected", table_name="surveillance_events")
    op.drop_index("idx_surveillance_type_status", table_name="surveillance_events")
    op.drop_index("ix_surveillance_events_status", table_name="surveillance_events")
    op.drop_index("ix_surveillance_events_detected_at", table_name="surveillance_events")
    op.drop_index("ix_surveillance_events_surveillance_type", table_name="surveillance_events")
    op.drop_index("ix_surveillance_events_event_name", table_name="surveillance_events")
    
    op.drop_index("idx_treatment_plan_strategy", table_name="treatment_plans")
    op.drop_index("idx_treatment_plan_assessment_status", table_name="treatment_plans")
    op.drop_index("ix_treatment_plans_implementation_status", table_name="treatment_plans")
    op.drop_index("ix_treatment_plans_treatment_strategy", table_name="treatment_plans")
    op.drop_index("ix_treatment_plans_plan_name", table_name="treatment_plans")
    op.drop_index("ix_treatment_plans_risk_factor_id", table_name="treatment_plans")
    op.drop_index("ix_treatment_plans_assessment_id", table_name="treatment_plans")
    
    op.drop_index("idx_risk_factor_threat_vuln", table_name="risk_factors")
    op.drop_index("idx_risk_factor_level", table_name="risk_factors")
    op.drop_index("idx_risk_factor_assessment_status", table_name="risk_factors")
    op.drop_index("ix_risk_factors_status", table_name="risk_factors")
    op.drop_index("ix_risk_factors_risk_level", table_name="risk_factors")
    op.drop_index("ix_risk_factors_impact", table_name="risk_factors")
    op.drop_index("ix_risk_factors_likelihood", table_name="risk_factors")
    op.drop_index("ix_risk_factors_vulnerability_category", table_name="risk_factors")
    op.drop_index("ix_risk_factors_threat_category", table_name="risk_factors")
    op.drop_index("ix_risk_factors_risk_name", table_name="risk_factors")
    op.drop_index("ix_risk_factors_assessment_id", table_name="risk_factors")
    
    op.drop_index("idx_risk_assessment_level", table_name="risk_assessments")
    op.drop_index("idx_risk_assessment_status_date", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_overall_risk_level", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_status", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_assessment_date", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_assessment_name", table_name="risk_assessments")
    
    op.drop_index("idx_data_cat_impact", table_name="data_categorizations")
    op.drop_index("idx_data_cat_system", table_name="data_categorizations")
    op.drop_index("ix_data_categorizations_is_active", table_name="data_categorizations")
    op.drop_index("ix_data_categorizations_overall_impact_level", table_name="data_categorizations")
    op.drop_index("ix_data_categorizations_data_type", table_name="data_categorizations")
    op.drop_index("ix_data_categorizations_system_id", table_name="data_categorizations")
    
    op.drop_index("idx_system_cat_impact", table_name="system_categorizations")
    op.drop_index("ix_system_categorizations_is_active", table_name="system_categorizations")
    op.drop_index("ix_system_categorizations_overall_impact_level", table_name="system_categorizations")
    op.drop_index("ix_system_categorizations_system_id", table_name="system_categorizations")
    op.drop_index("ix_system_categorizations_system_name", table_name="system_categorizations")
    
    # Drop tables (in reverse order of dependencies)
    op.drop_table("surveillance_events")
    op.drop_table("treatment_plans")
    op.drop_table("risk_factors")
    op.drop_table("risk_assessments")
    op.drop_table("data_categorizations")
    op.drop_table("system_categorizations")
