"""Add IR-2, IR-3, IR-7, IR-8, IR-9 tables and IR-4(1), IR-5(1) automation fields

Revision ID: 20260130_ir_controls
Revises: 20260130_incident_response
Create Date: 2026-01-30

This migration adds tables and fields for remaining FedRAMP IR controls:
- IR-2: Incident Response Training (curricula, records, tabletop exercises)
- IR-3: Incident Response Testing (scenarios, executions)
- IR-7: Incident Response Assistance (requests, expert contacts)
- IR-8: Incident Response Plan (plans, distributions)
- IR-9: Information Spillage Response (spillage incidents)
- IR-4(1): Automated Incident Handling (fields on security_incidents)
- IR-5(1): Automated Tracking/Data Collection/Analysis (fields on security_incidents)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_ir_controls"
down_revision: Union[str, Sequence[str], None] = "20260130_incident_response"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add IR control tables and automation fields"""
    
    # Add automation fields to security_incidents for IR-4(1) and IR-5(1)
    op.add_column("security_incidents", sa.Column("automated_handling_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("security_incidents", sa.Column("automated_actions_taken", postgresql.JSON(), nullable=True))
    op.add_column("security_incidents", sa.Column("automation_workflow_id", sa.String(length=255), nullable=True))
    op.add_column("security_incidents", sa.Column("automated_tracking_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("security_incidents", sa.Column("collected_data", postgresql.JSON(), nullable=True))
    op.add_column("security_incidents", sa.Column("analysis_results", postgresql.JSON(), nullable=True))
    op.add_column("security_incidents", sa.Column("correlation_ids", postgresql.JSON(), nullable=True))
    op.add_column("security_incidents", sa.Column("data_collection_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("security_incidents", sa.Column("analysis_timestamp", sa.DateTime(timezone=True), nullable=True))
    
    # IR-2: Incident Response Training Tables
    op.create_table(
        "incident_training_curricula",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_role", sa.String(length=50), nullable=False),
        sa.Column("modules", postgresql.JSON(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("required_score_percent", sa.Integer(), nullable=False, server_default=sa.text("80")),
        sa.Column("valid_for_days", sa.Integer(), nullable=False, server_default=sa.text("365")),
        sa.Column("renewal_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.String(length=20), nullable=False, server_default=sa.text("'1.0'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    op.create_table(
        "incident_training_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'not_started'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_percent", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_modules", postgresql.JSON(), nullable=True),
        sa.Column("module_scores", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["curriculum_id"], ["incident_training_curricula.id"], ondelete="CASCADE"),
    )
    
    op.create_table(
        "tabletop_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("exercise_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("participant_user_ids", postgresql.JSON(), nullable=False),
        sa.Column("facilitator_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("outcomes", sa.Text(), nullable=True),
        sa.Column("strengths_identified", sa.Text(), nullable=True),
        sa.Column("areas_for_improvement", sa.Text(), nullable=True),
        sa.Column("participant_feedback", postgresql.JSON(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["facilitator_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # IR-3: Incident Response Testing Tables
    op.create_table(
        "incident_test_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("scenario_type", sa.String(length=50), nullable=False),
        sa.Column("objectives", postgresql.JSON(), nullable=False),
        sa.Column("procedures_to_test", postgresql.JSON(), nullable=False),
        sa.Column("expected_outcomes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_user_ids", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    op.create_table(
        "incident_test_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column("executed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("participants", postgresql.JSON(), nullable=True),
        sa.Column("objectives_met", postgresql.JSON(), nullable=True),
        sa.Column("procedures_tested", postgresql.JSON(), nullable=True),
        sa.Column("actual_outcomes", sa.Text(), nullable=True),
        sa.Column("strengths_identified", sa.Text(), nullable=True),
        sa.Column("weaknesses_identified", sa.Text(), nullable=True),
        sa.Column("gaps_identified", sa.Text(), nullable=True),
        sa.Column("improvement_recommendations", postgresql.JSON(), nullable=True),
        sa.Column("priority_actions", postgresql.JSON(), nullable=True),
        sa.Column("response_time_minutes", sa.Integer(), nullable=True),
        sa.Column("containment_time_minutes", sa.Integer(), nullable=True),
        sa.Column("resolution_time_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scenario_id"], ["incident_test_scenarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # IR-7: Incident Response Assistance Tables
    op.create_table(
        "incident_assistance_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default=sa.text("'normal'")),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolution_time_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    op.create_table(
        "incident_expert_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("expertise_areas", postgresql.JSON(), nullable=False),
        sa.Column("specializations", sa.Text(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("availability_notes", sa.Text(), nullable=True),
        sa.Column("preferred_contact_method", sa.String(length=50), nullable=True),
        sa.Column("average_response_time_minutes", sa.Integer(), nullable=True),
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # IR-8: Incident Response Plan Tables
    op.create_table(
        "incident_response_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plan_content", sa.Text(), nullable=False),
        sa.Column("plan_document_url", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_frequency_days", sa.Integer(), nullable=False, server_default=sa.text("365")),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    op.create_table(
        "plan_distributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("distributed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("distribution_method", sa.String(length=50), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledgment_ip_address", sa.String(length=45), nullable=True),
        sa.Column("distributed_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["incident_response_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["distributed_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # IR-9: Information Spillage Tables
    op.create_table(
        "information_spillages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("spillage_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(length=50), nullable=False),
        sa.Column("data_type", sa.String(length=100), nullable=True),
        sa.Column("sensitivity_level", sa.String(length=20), nullable=False, server_default=sa.text("'moderate'")),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("detected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("detected_by_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("detection_method", sa.String(length=100), nullable=True),
        sa.Column("affected_systems", postgresql.JSON(), nullable=True),
        sa.Column("affected_data_elements", postgresql.JSON(), nullable=True),
        sa.Column("estimated_records_affected", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'detected'")),
        sa.Column("contained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("containment_procedures", sa.Text(), nullable=True),
        sa.Column("containment_actions_taken", postgresql.JSON(), nullable=True),
        sa.Column("notifications_sent", postgresql.JSON(), nullable=True),
        sa.Column("notified_parties", postgresql.JSON(), nullable=True),
        sa.Column("notification_timestamps", postgresql.JSON(), nullable=True),
        sa.Column("cleanup_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleanup_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleanup_procedures", sa.Text(), nullable=True),
        sa.Column("cleanup_actions_taken", postgresql.JSON(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column("verification_method", sa.String(length=100), nullable=True),
        sa.Column("verification_results", sa.Text(), nullable=True),
        sa.Column("verification_passed", sa.Boolean(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["detected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # Create indexes
    op.create_index("idx_curriculum_role", "incident_training_curricula", ["target_role"])
    op.create_index("idx_curriculum_active", "incident_training_curricula", ["is_active"])
    op.create_index("idx_training_user_curriculum", "incident_training_records", ["user_id", "curriculum_id"])
    op.create_index("idx_training_status", "incident_training_records", ["status"])
    op.create_index("idx_training_expires", "incident_training_records", ["expires_at"])
    op.create_index("idx_training_completed", "incident_training_records", ["completed_at"])
    op.create_index("idx_exercise_org_date", "tabletop_exercises", ["org_id", "exercise_date"])
    op.create_index("idx_exercise_status", "tabletop_exercises", ["status"])
    op.create_index("idx_scenario_org", "incident_test_scenarios", ["org_id"])
    op.create_index("idx_scenario_status", "incident_test_scenarios", ["status"])
    op.create_index("idx_scenario_scheduled", "incident_test_scenarios", ["scheduled_date"])
    op.create_index("idx_execution_scenario", "incident_test_executions", ["scenario_id"])
    op.create_index("idx_execution_date", "incident_test_executions", ["execution_date"])
    op.create_index("idx_execution_status", "incident_test_executions", ["status"])
    op.create_index("idx_assistance_incident", "incident_assistance_requests", ["incident_id"])
    op.create_index("idx_assistance_status", "incident_assistance_requests", ["status"])
    op.create_index("idx_assistance_created", "incident_assistance_requests", ["created_at"])
    op.create_index("idx_expert_org", "incident_expert_contacts", ["org_id"])
    # Note: GIN index on JSONB column - PostgreSQL specific
    # op.create_index("idx_expert_expertise", "incident_expert_contacts", ["expertise_areas"], postgresql_using="gin")
    # Using regular index instead for compatibility
    op.create_index("idx_expert_expertise", "incident_expert_contacts", ["expertise_areas"])
    op.create_index("idx_expert_available", "incident_expert_contacts", ["is_available"])
    op.create_index("idx_plan_org_version", "incident_response_plans", ["org_id", "version"])
    op.create_index("idx_plan_status", "incident_response_plans", ["status"])
    op.create_index("idx_plan_active", "incident_response_plans", ["is_active"])
    op.create_index("idx_plan_next_review", "incident_response_plans", ["next_review_date"])
    op.create_index("idx_distribution_plan", "plan_distributions", ["plan_id"])
    op.create_index("idx_distribution_user", "plan_distributions", ["user_id"])
    op.create_index("idx_distribution_acknowledged", "plan_distributions", ["acknowledged_at"])
    op.create_index("idx_spillage_org", "information_spillages", ["org_id"])
    op.create_index("idx_spillage_status", "information_spillages", ["status"])
    op.create_index("idx_spillage_detected", "information_spillages", ["detected_at"])
    op.create_index("idx_spillage_classification", "information_spillages", ["classification"])
    op.create_index("ix_incident_training_curricula_org_id", "incident_training_curricula", ["org_id"])
    op.create_index("ix_incident_training_records_org_id", "incident_training_records", ["org_id"])
    op.create_index("ix_tabletop_exercises_org_id", "tabletop_exercises", ["org_id"])
    op.create_index("ix_incident_test_scenarios_org_id", "incident_test_scenarios", ["org_id"])
    op.create_index("ix_incident_test_executions_org_id", "incident_test_executions", ["org_id"])
    op.create_index("ix_incident_assistance_requests_org_id", "incident_assistance_requests", ["org_id"])
    op.create_index("ix_incident_expert_contacts_org_id", "incident_expert_contacts", ["org_id"])
    op.create_index("ix_incident_response_plans_org_id", "incident_response_plans", ["org_id"])
    op.create_index("ix_plan_distributions_org_id", "plan_distributions", ["org_id"])
    op.create_index("ix_information_spillages_org_id", "information_spillages", ["org_id"])
    op.create_index("ix_information_spillages_spillage_number", "information_spillages", ["spillage_number"])


def downgrade() -> None:
    """Remove IR control tables and automation fields"""
    
    # Drop indexes
    op.drop_index("ix_information_spillages_spillage_number", table_name="information_spillages")
    op.drop_index("ix_information_spillages_org_id", table_name="information_spillages")
    op.drop_index("ix_plan_distributions_org_id", table_name="plan_distributions")
    op.drop_index("ix_incident_response_plans_org_id", table_name="incident_response_plans")
    op.drop_index("ix_incident_expert_contacts_org_id", table_name="incident_expert_contacts")
    op.drop_index("ix_incident_assistance_requests_org_id", table_name="incident_assistance_requests")
    op.drop_index("ix_incident_test_executions_org_id", table_name="incident_test_executions")
    op.drop_index("ix_incident_test_scenarios_org_id", table_name="incident_test_scenarios")
    op.drop_index("ix_tabletop_exercises_org_id", table_name="tabletop_exercises")
    op.drop_index("ix_incident_training_records_org_id", table_name="incident_training_records")
    op.drop_index("ix_incident_training_curricula_org_id", table_name="incident_training_curricula")
    op.drop_index("idx_spillage_classification", table_name="information_spillages")
    op.drop_index("idx_spillage_detected", table_name="information_spillages")
    op.drop_index("idx_spillage_status", table_name="information_spillages")
    op.drop_index("idx_spillage_org", table_name="information_spillages")
    op.drop_index("idx_distribution_acknowledged", table_name="plan_distributions")
    op.drop_index("idx_distribution_user", table_name="plan_distributions")
    op.drop_index("idx_distribution_plan", table_name="plan_distributions")
    op.drop_index("idx_plan_next_review", table_name="incident_response_plans")
    op.drop_index("idx_plan_active", table_name="incident_response_plans")
    op.drop_index("idx_plan_status", table_name="incident_response_plans")
    op.drop_index("idx_plan_org_version", table_name="incident_response_plans")
    op.drop_index("idx_expert_available", table_name="incident_expert_contacts")
    op.drop_index("idx_expert_expertise", table_name="incident_expert_contacts")
    op.drop_index("idx_expert_org", table_name="incident_expert_contacts")
    op.drop_index("idx_assistance_created", table_name="incident_assistance_requests")
    op.drop_index("idx_assistance_status", table_name="incident_assistance_requests")
    op.drop_index("idx_assistance_incident", table_name="incident_assistance_requests")
    op.drop_index("idx_execution_status", table_name="incident_test_executions")
    op.drop_index("idx_execution_date", table_name="incident_test_executions")
    op.drop_index("idx_execution_scenario", table_name="incident_test_executions")
    op.drop_index("idx_scenario_scheduled", table_name="incident_test_scenarios")
    op.drop_index("idx_scenario_status", table_name="incident_test_scenarios")
    op.drop_index("idx_scenario_org", table_name="incident_test_scenarios")
    op.drop_index("idx_exercise_status", table_name="tabletop_exercises")
    op.drop_index("idx_exercise_org_date", table_name="tabletop_exercises")
    op.drop_index("idx_training_completed", table_name="incident_training_records")
    op.drop_index("idx_training_expires", table_name="incident_training_records")
    op.drop_index("idx_training_status", table_name="incident_training_records")
    op.drop_index("idx_training_user_curriculum", table_name="incident_training_records")
    op.drop_index("idx_curriculum_active", table_name="incident_training_curricula")
    op.drop_index("idx_curriculum_role", table_name="incident_training_curricula")
    
    # Drop tables
    op.drop_table("information_spillages")
    op.drop_table("plan_distributions")
    op.drop_table("incident_response_plans")
    op.drop_table("incident_expert_contacts")
    op.drop_table("incident_assistance_requests")
    op.drop_table("incident_test_executions")
    op.drop_table("incident_test_scenarios")
    op.drop_table("tabletop_exercises")
    op.drop_table("incident_training_records")
    op.drop_table("incident_training_curricula")
    
    # Remove automation fields from security_incidents
    op.drop_column("security_incidents", "analysis_timestamp")
    op.drop_column("security_incidents", "data_collection_timestamp")
    op.drop_column("security_incidents", "correlation_ids")
    op.drop_column("security_incidents", "analysis_results")
    op.drop_column("security_incidents", "collected_data")
    op.drop_column("security_incidents", "automated_tracking_enabled")
    op.drop_column("security_incidents", "automation_workflow_id")
    op.drop_column("security_incidents", "automated_actions_taken")
    op.drop_column("security_incidents", "automated_handling_enabled")
