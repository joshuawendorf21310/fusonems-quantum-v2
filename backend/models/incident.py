"""
Security Incident Model for FedRAMP IR-4, IR-5, IR-6 Compliance

This model provides comprehensive security incident tracking and management
required for FedRAMP Incident Response controls:
- IR-4: Incident Handling
- IR-5: Incident Monitoring
- IR-6: Incident Reporting

Incidents are classified by severity and tracked through their lifecycle
with complete audit trails and activity logs.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class IncidentSeverity(str, Enum):
    """Incident severity classification levels"""
    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status in lifecycle"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentCategory(str, Enum):
    """Categories of security incidents"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    NETWORK_INTRUSION = "network_intrusion"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    DENIAL_OF_SERVICE = "denial_of_service"
    CONFIGURATION_ERROR = "configuration_error"
    PHYSICAL_SECURITY = "physical_security"
    OTHER = "other"


class SecurityIncident(Base):
    """
    Security incident tracking table for FedRAMP IR-4, IR-5, IR-6 compliance.
    
    Tracks security incidents from detection through resolution with complete
    audit trails, timeline, and activity logs.
    """
    __tablename__ = "security_incidents"
    __table_args__ = (
        # Indexes for common query patterns
        Index('idx_incident_status_severity', 'status', 'severity'),
        Index('idx_incident_org_status', 'org_id', 'status'),
        Index('idx_incident_created', 'created_at'),
        Index('idx_incident_category', 'category'),
        Index('idx_incident_assigned_to', 'assigned_to_user_id'),
        Index('idx_incident_detected_at', 'detected_at'),
        Index('idx_incident_resolved_at', 'resolved_at'),
        Index('idx_incident_us_cert_reported', 'us_cert_reported_at'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization context
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Incident identification
    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    severity = Column(
        String(20),
        nullable=False,
        index=True,
        default=IncidentSeverity.INFORMATIONAL.value,
    )
    category = Column(
        String(50),
        nullable=False,
        index=True,
        default=IncidentCategory.OTHER.value,
    )
    
    # Status tracking
    status = Column(
        String(20),
        nullable=False,
        index=True,
        default=IncidentStatus.NEW.value,
    )
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    contained_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Detection and reporting
    detected_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    detected_by_system = Column(Boolean, default=False, nullable=False)  # True if auto-detected
    detection_method = Column(String(100), nullable=True)  # audit_log, siem, manual, etc.
    
    # Assignment
    assigned_to_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Affected systems and users
    affected_systems = Column(JSON, nullable=True)  # List of system identifiers
    affected_users = Column(JSON, nullable=True)  # List of user IDs or emails
    affected_resources = Column(JSON, nullable=True)  # List of resource identifiers
    
    # Investigation details
    root_cause = Column(Text, nullable=True)
    impact_assessment = Column(Text, nullable=True)
    containment_actions = Column(Text, nullable=True)
    remediation_actions = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    
    # US-CERT reporting (IR-6 requirement)
    us_cert_reported = Column(Boolean, default=False, nullable=False)
    us_cert_reported_at = Column(DateTime(timezone=True), nullable=True, index=True)
    us_cert_report_id = Column(String(255), nullable=True)
    us_cert_follow_up_required = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    tags = Column(JSON, nullable=True)  # Flexible tags for categorization
    metadata = Column(JSON, nullable=True)  # Additional flexible metadata
    
    # Compliance fields
    classification = Column(String(50), nullable=True)  # PHI, NON_PHI, PII, etc.
    training_mode = Column(Boolean, default=False, nullable=False)
    
    # IR-4(1): Automated Incident Handling
    automated_handling_enabled = Column(Boolean, default=False, nullable=False)
    automated_actions_taken = Column(JSON, nullable=True)  # List of automated actions
    automation_workflow_id = Column(String(255), nullable=True)  # Reference to automation workflow
    
    # IR-5(1): Automated Tracking / Data Collection / Analysis
    automated_tracking_enabled = Column(Boolean, default=True, nullable=False)
    collected_data = Column(JSON, nullable=True)  # Automatically collected data/artifacts
    analysis_results = Column(JSON, nullable=True)  # Automated analysis results
    correlation_ids = Column(JSON, nullable=True)  # Related event/incident IDs
    data_collection_timestamp = Column(DateTime(timezone=True), nullable=True)
    analysis_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    detected_by_user = relationship("User", foreign_keys=[detected_by_user_id], lazy="select")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id], lazy="select")
    
    def __repr__(self):
        return (
            f"<SecurityIncident(id={self.id}, "
            f"incident_number={self.incident_number}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )


class IncidentActivity(Base):
    """
    Activity log for security incidents.
    
    Tracks all activities, updates, and changes related to an incident
    for complete audit trail and timeline reconstruction.
    """
    __tablename__ = "incident_activities"
    __table_args__ = (
        Index('idx_activity_incident', 'incident_id'),
        Index('idx_activity_user', 'user_id'),
        Index('idx_activity_timestamp', 'timestamp'),
        Index('idx_activity_type', 'activity_type'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Incident reference
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Activity details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    activity_type = Column(String(50), nullable=False, index=True)  # status_change, comment, assignment, etc.
    description = Column(Text, nullable=False)
    
    # User who performed the activity
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_email = Column(String(255), nullable=True)  # Denormalized for retention
    
    # Activity details
    old_value = Column(String(255), nullable=True)  # For status/severity changes
    new_value = Column(String(255), nullable=True)  # For status/severity changes
    details = Column(JSON, nullable=True)  # Additional activity details
    
    # Request context (for audit trail)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationship
    incident = relationship("SecurityIncident", lazy="select")
    user = relationship("User", lazy="select")
    
    def __repr__(self):
        return (
            f"<IncidentActivity(id={self.id}, "
            f"incident_id={self.incident_id}, "
            f"activity_type={self.activity_type}, "
            f"timestamp={self.timestamp})>"
        )


class IncidentTimeline(Base):
    """
    Timeline of key events for an incident.
    
    Provides chronological view of incident lifecycle events for
    investigation and reporting purposes.
    """
    __tablename__ = "incident_timeline"
    __table_args__ = (
        Index('idx_timeline_incident', 'incident_id'),
        Index('idx_timeline_event_time', 'event_time'),
        Index('idx_timeline_event_type', 'event_type'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Incident reference
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Timeline event
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # detected, contained, resolved, etc.
    event_description = Column(Text, nullable=False)
    
    # Event source
    source = Column(String(100), nullable=True)  # system, user, external, etc.
    source_id = Column(String(255), nullable=True)  # ID of the source
    
    # Additional context
    metadata = Column(JSON, nullable=True)
    
    # Relationship
    incident = relationship("SecurityIncident", lazy="select")
    
    def __repr__(self):
        return (
            f"<IncidentTimeline(id={self.id}, "
            f"incident_id={self.incident_id}, "
            f"event_type={self.event_type}, "
            f"event_time={self.event_time})>"
        )


# ============================================================================
# IR-2: Incident Response Training Models
# ============================================================================


class TrainingRole(str, Enum):
    """Roles that require incident response training"""
    INCIDENT_RESPONDER = "incident_responder"
    SECURITY_ANALYST = "security_analyst"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    IT_STAFF = "it_staff"
    ALL_PERSONNEL = "all_personnel"


class TrainingStatus(str, Enum):
    """Training completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"


class IncidentTrainingCurriculum(Base):
    """
    IR-2: Incident Response Training Curriculum
    
    Defines training curricula for different roles with required modules
    and completion criteria.
    """
    __tablename__ = "incident_training_curricula"
    __table_args__ = (
        Index('idx_curriculum_role', 'target_role'),
        Index('idx_curriculum_active', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String(50), nullable=False, index=True)  # TrainingRole enum value
    
    # Curriculum content
    modules = Column(JSON, nullable=False)  # List of module definitions
    duration_hours = Column(Integer, nullable=False, default=0)
    required_score_percent = Column(Integer, nullable=False, default=80)
    
    # Validity and renewal
    valid_for_days = Column(Integer, nullable=False, default=365)  # Training expires after N days
    renewal_required = Column(Boolean, default=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    def __repr__(self):
        return f"<IncidentTrainingCurriculum(id={self.id}, name={self.name}, role={self.target_role})>"


class IncidentTrainingRecord(Base):
    """
    IR-2: Individual Training Completion Records
    
    Tracks training completion for each user per curriculum.
    """
    __tablename__ = "incident_training_records"
    __table_args__ = (
        Index('idx_training_user_curriculum', 'user_id', 'curriculum_id'),
        Index('idx_training_status', 'status'),
        Index('idx_training_expires', 'expires_at'),
        Index('idx_training_completed', 'completed_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_id = Column(UUID(as_uuid=True), ForeignKey("incident_training_curricula.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(20), nullable=False, index=True, default=TrainingStatus.NOT_STARTED.value)
    
    # Progress tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Assessment results
    score_percent = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    
    # Module completion
    completed_modules = Column(JSON, nullable=True)  # List of completed module IDs
    module_scores = Column(JSON, nullable=True)  # Map of module_id -> score
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    user = relationship("User", lazy="select")
    curriculum = relationship("IncidentTrainingCurriculum", lazy="select")
    
    def __repr__(self):
        return f"<IncidentTrainingRecord(id={self.id}, user_id={self.user_id}, status={self.status})>"


class TabletopExercise(Base):
    """
    IR-2: Tabletop Exercise Records
    
    Tracks tabletop exercises conducted for incident response training.
    """
    __tablename__ = "tabletop_exercises"
    __table_args__ = (
        Index('idx_exercise_org_date', 'org_id', 'exercise_date'),
        Index('idx_exercise_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scenario = Column(Text, nullable=False)  # Exercise scenario description
    
    exercise_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Participants
    participant_user_ids = Column(JSON, nullable=False)  # List of user IDs
    facilitator_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Results
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, in_progress, completed, cancelled
    outcomes = Column(Text, nullable=True)  # Exercise outcomes and lessons learned
    strengths_identified = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    
    # Feedback
    participant_feedback = Column(JSON, nullable=True)  # Map of user_id -> feedback
    overall_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    def __repr__(self):
        return f"<TabletopExercise(id={self.id}, name={self.name}, date={self.exercise_date})>"


# ============================================================================
# IR-3: Incident Response Testing Models
# ============================================================================


class TestScenarioStatus(str, Enum):
    """Test scenario execution status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IncidentTestScenario(Base):
    """
    IR-3: Incident Response Test Scenarios
    
    Defines test scenarios for incident response procedures.
    """
    __tablename__ = "incident_test_scenarios"
    __table_args__ = (
        Index('idx_scenario_org', 'org_id'),
        Index('idx_scenario_status', 'status'),
        Index('idx_scenario_scheduled', 'scheduled_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    scenario_type = Column(String(50), nullable=False)  # malware, breach, dos, etc.
    
    # Test details
    objectives = Column(JSON, nullable=False)  # List of test objectives
    procedures_to_test = Column(JSON, nullable=False)  # List of procedures/controls to test
    expected_outcomes = Column(Text, nullable=True)
    
    # Scheduling
    status = Column(String(20), nullable=False, index=True, default=TestScenarioStatus.DRAFT.value)
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Participants
    assigned_user_ids = Column(JSON, nullable=True)  # List of user IDs assigned to test
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    def __repr__(self):
        return f"<IncidentTestScenario(id={self.id}, name={self.name}, status={self.status})>"


class IncidentTestExecution(Base):
    """
    IR-3: Test Execution Records
    
    Records the execution and results of incident response tests.
    """
    __tablename__ = "incident_test_executions"
    __table_args__ = (
        Index('idx_execution_scenario', 'scenario_id'),
        Index('idx_execution_date', 'execution_date'),
        Index('idx_execution_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("incident_test_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    execution_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True, default=TestScenarioStatus.IN_PROGRESS.value)
    
    # Execution details
    executed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    participants = Column(JSON, nullable=True)  # List of participant user IDs
    
    # Results
    objectives_met = Column(JSON, nullable=True)  # Map of objective -> met (bool)
    procedures_tested = Column(JSON, nullable=True)  # Map of procedure -> result
    actual_outcomes = Column(Text, nullable=True)
    
    # Analysis
    strengths_identified = Column(Text, nullable=True)
    weaknesses_identified = Column(Text, nullable=True)
    gaps_identified = Column(Text, nullable=True)
    
    # Recommendations
    improvement_recommendations = Column(JSON, nullable=True)  # List of recommendations
    priority_actions = Column(JSON, nullable=True)  # List of high-priority actions
    
    # Metrics
    response_time_minutes = Column(Integer, nullable=True)
    containment_time_minutes = Column(Integer, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    scenario = relationship("IncidentTestScenario", lazy="select")
    
    def __repr__(self):
        return f"<IncidentTestExecution(id={self.id}, scenario_id={self.scenario_id}, date={self.execution_date})>"


# ============================================================================
# IR-7: Incident Response Assistance Models
# ============================================================================


class AssistanceRequestStatus(str, Enum):
    """Assistance request status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentAssistanceRequest(Base):
    """
    IR-7: Incident Response Assistance Requests
    
    Tracks requests for assistance during incident response.
    """
    __tablename__ = "incident_assistance_requests"
    __table_args__ = (
        Index('idx_assistance_incident', 'incident_id'),
        Index('idx_assistance_status', 'status'),
        Index('idx_assistance_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    incident_id = Column(UUID(as_uuid=True), ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Request details
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # help_desk, expert_consultation, resource_request, etc.
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent
    
    # Assignment
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, index=True, default=AssistanceRequestStatus.OPEN.value)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    incident = relationship("SecurityIncident", lazy="select")
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id], lazy="select")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id], lazy="select")
    
    def __repr__(self):
        return f"<IncidentAssistanceRequest(id={self.id}, type={self.request_type}, status={self.status})>"


class IncidentExpertContact(Base):
    """
    IR-7: Expert Contact Directory
    
    Maintains directory of experts available for incident response assistance.
    """
    __tablename__ = "incident_expert_contacts"
    __table_args__ = (
        Index('idx_expert_org', 'org_id'),
        Index('idx_expert_expertise', 'expertise_areas'),
        Index('idx_expert_available', 'is_available'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Expert information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    organization = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    
    # Expertise
    expertise_areas = Column(JSON, nullable=False)  # List of expertise areas (malware, forensics, etc.)
    specializations = Column(Text, nullable=True)
    
    # Availability
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    availability_notes = Column(Text, nullable=True)
    preferred_contact_method = Column(String(50), nullable=True)  # email, phone, etc.
    
    # Response metrics
    average_response_time_minutes = Column(Integer, nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    def __repr__(self):
        return f"<IncidentExpertContact(id={self.id}, name={self.name}, expertise={self.expertise_areas})>"


# ============================================================================
# IR-8: Incident Response Plan Models
# ============================================================================


class PlanStatus(str, Enum):
    """Plan status"""
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    ARCHIVED = "archived"


class IncidentResponsePlan(Base):
    """
    IR-8: Incident Response Plan
    
    Stores incident response plans with versioning and distribution tracking.
    """
    __tablename__ = "incident_response_plans"
    __table_args__ = (
        Index('idx_plan_org_version', 'org_id', 'version'),
        Index('idx_plan_status', 'status'),
        Index('idx_plan_active', 'is_active'),
        Index('idx_plan_next_review', 'next_review_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plan identification
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Plan content
    plan_content = Column(Text, nullable=False)  # Full plan text/content
    plan_document_url = Column(String(1000), nullable=True)  # URL to document if stored externally
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, index=True, default=PlanStatus.DRAFT.value)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # Review and updates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True, index=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
    # Approval
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id], lazy="select")
    
    def __repr__(self):
        return f"<IncidentResponsePlan(id={self.id}, name={self.name}, version={self.version})>"


class PlanDistribution(Base):
    """
    IR-8: Plan Distribution Records
    
    Tracks distribution of incident response plans to personnel.
    """
    __tablename__ = "plan_distributions"
    __table_args__ = (
        Index('idx_distribution_plan', 'plan_id'),
        Index('idx_distribution_user', 'user_id'),
        Index('idx_distribution_acknowledged', 'acknowledged_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    plan_id = Column(UUID(as_uuid=True), ForeignKey("incident_response_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Distribution details
    distributed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    distribution_method = Column(String(50), nullable=False)  # email, portal, manual, etc.
    
    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True), nullable=True, index=True)
    acknowledgment_ip_address = Column(String(45), nullable=True)
    
    # Metadata
    distributed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    plan = relationship("IncidentResponsePlan", lazy="select")
    user = relationship("User", lazy="select")
    
    def __repr__(self):
        return f"<PlanDistribution(id={self.id}, plan_id={self.plan_id}, user_id={self.user_id})>"


# ============================================================================
# IR-9: Information Spillage Response Models
# ============================================================================


class SpillageStatus(str, Enum):
    """Information spillage status"""
    DETECTED = "detected"
    CONTAINED = "contained"
    CLEANUP_IN_PROGRESS = "cleanup_in_progress"
    VERIFIED = "verified"
    CLOSED = "closed"


class InformationSpillage(Base):
    """
    IR-9: Information Spillage Incident
    
    Tracks information spillage incidents from detection through cleanup verification.
    """
    __tablename__ = "information_spillages"
    __table_args__ = (
        Index('idx_spillage_org', 'org_id'),
        Index('idx_spillage_status', 'status'),
        Index('idx_spillage_detected', 'detected_at'),
        Index('idx_spillage_classification', 'classification'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Incident identification
    spillage_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    classification = Column(String(50), nullable=False, index=True)  # PHI, PII, NON_PHI, etc.
    data_type = Column(String(100), nullable=True)  # patient_data, financial_data, etc.
    sensitivity_level = Column(String(20), nullable=False, default="moderate")  # low, moderate, high, critical
    
    # Detection
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    detected_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    detected_by_system = Column(Boolean, default=False, nullable=False)
    detection_method = Column(String(100), nullable=True)
    
    # Affected systems and data
    affected_systems = Column(JSON, nullable=True)  # List of system identifiers
    affected_data_elements = Column(JSON, nullable=True)  # List of data elements/types
    estimated_records_affected = Column(Integer, nullable=True)
    
    # Containment
    status = Column(String(20), nullable=False, index=True, default=SpillageStatus.DETECTED.value)
    contained_at = Column(DateTime(timezone=True), nullable=True)
    containment_procedures = Column(Text, nullable=True)
    containment_actions_taken = Column(JSON, nullable=True)  # List of actions taken
    
    # Notification
    notifications_sent = Column(JSON, nullable=True)  # List of notifications sent
    notified_parties = Column(JSON, nullable=True)  # List of parties notified
    notification_timestamps = Column(JSON, nullable=True)  # Map of party -> timestamp
    
    # Cleanup
    cleanup_started_at = Column(DateTime(timezone=True), nullable=True)
    cleanup_completed_at = Column(DateTime(timezone=True), nullable=True)
    cleanup_procedures = Column(Text, nullable=True)
    cleanup_actions_taken = Column(JSON, nullable=True)  # List of cleanup actions
    
    # Verification
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_method = Column(String(100), nullable=True)
    verification_results = Column(Text, nullable=True)
    verification_passed = Column(Boolean, nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    lessons_learned = Column(Text, nullable=True)
    
    # Assignment
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    tags = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    detected_by_user = relationship("User", foreign_keys=[detected_by_user_id], lazy="select")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id], lazy="select")
    verified_by_user = relationship("User", foreign_keys=[verified_by_user_id], lazy="select")
    
    def __repr__(self):
        return (
            f"<InformationSpillage(id={self.id}, "
            f"spillage_number={self.spillage_number}, "
            f"status={self.status}, "
            f"classification={self.classification})>"
        )
