"""
Assessment & Authorization (CA) Models for FedRAMP Compliance

This module provides models for:
- CA-2: Security Assessments
- CA-3: System Interconnections
- CA-5: Plan of Action & Milestones (POA&M)
- CA-6: Security Authorization
- CA-7: Continuous Monitoring (enhanced)
- CA-8: Penetration Testing
- CA-9: Internal System Connections
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
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


# ============================================================================
# CA-2: Security Assessments
# ============================================================================

class AssessmentStatus(str, Enum):
    """Security assessment status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class AssessmentType(str, Enum):
    """Types of security assessments"""
    INITIAL = "initial"
    ANNUAL = "annual"
    CONTINUOUS = "continuous"
    AD_HOC = "ad_hoc"
    REAUTHORIZATION = "reauthorization"


class ControlTestResult(str, Enum):
    """Control test results"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_TESTED = "not_tested"
    NOT_APPLICABLE = "not_applicable"


class SecurityAssessment(Base):
    """
    CA-2: Security Assessment
    
    Tracks security assessments including control testing and results.
    """
    __tablename__ = "security_assessments"
    __table_args__ = (
        Index('idx_assessment_org_status', 'org_id', 'status'),
        Index('idx_assessment_type', 'assessment_type'),
        Index('idx_assessment_date', 'assessment_date'),
        Index('idx_assessment_assessor', 'assessor_user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Assessment identification
    assessment_name = Column(String(255), nullable=False, index=True)
    assessment_number = Column(String(100), unique=True, nullable=True, index=True)  # e.g., "ASSESS-2026-001"
    assessment_type = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=AssessmentStatus.PLANNED.value,
        index=True,
    )
    
    # Assessment details
    assessment_description = Column(Text, nullable=True)
    scope_description = Column(Text, nullable=True)
    systems_in_scope = Column(JSON, nullable=True)  # List of system IDs
    
    # Scheduling
    planned_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_end_date = Column(DateTime(timezone=True), nullable=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Assessors
    assessor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assessor_name = Column(String(255), nullable=True)
    assessor_organization = Column(String(255), nullable=True)
    assessor_type = Column(String(50), nullable=True)  # internal, external, 3pao
    
    # Assessment results
    overall_result = Column(String(50), nullable=True)  # passed, failed, conditional
    findings_summary = Column(Text, nullable=True)
    findings_count = Column(Integer, nullable=False, default=0)
    critical_findings_count = Column(Integer, nullable=False, default=0)
    high_findings_count = Column(Integer, nullable=False, default=0)
    medium_findings_count = Column(Integer, nullable=False, default=0)
    low_findings_count = Column(Integer, nullable=False, default=0)
    
    # Assessment report
    assessment_report_url = Column(String(1000), nullable=True)
    assessment_report_content = Column(Text, nullable=True)
    
    # Next assessment
    next_assessment_due = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    control_tests = relationship("ControlTest", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("AssessmentFinding", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<SecurityAssessment(id={self.id}, "
            f"assessment_name={self.assessment_name}, "
            f"status={self.status})>"
        )


class ControlTest(Base):
    """
    CA-2: Individual control test within security assessment
    """
    __tablename__ = "control_tests"
    __table_args__ = (
        Index('idx_control_test_assessment', 'assessment_id'),
        Index('idx_control_test_control', 'control_family', 'control_id'),
        Index('idx_control_test_result', 'test_result'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Control identification
    control_family = Column(String(10), nullable=False, index=True)
    control_id = Column(String(50), nullable=False, index=True)
    control_title = Column(String(255), nullable=True)
    
    # Test details
    test_procedure = Column(Text, nullable=True)
    test_objectives = Column(Text, nullable=True)
    test_method = Column(String(100), nullable=True)  # interview, examine, test
    
    # Test results
    test_result = Column(String(50), nullable=False, index=True)
    test_notes = Column(Text, nullable=True)
    evidence_collected = Column(JSON, nullable=True)  # List of evidence references
    
    # Test execution
    tested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    tested_at = Column(DateTime(timezone=True), nullable=True)
    
    # Findings
    findings_identified = Column(JSON, nullable=True)  # List of finding IDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    assessment = relationship("SecurityAssessment", back_populates="control_tests")
    
    def __repr__(self):
        return (
            f"<ControlTest(id={self.id}, "
            f"control_id={self.control_id}, "
            f"test_result={self.test_result})>"
        )


class AssessmentFinding(Base):
    """
    CA-2: Findings identified during security assessment
    """
    __tablename__ = "assessment_findings"
    __table_args__ = (
        Index('idx_finding_assessment', 'assessment_id'),
        Index('idx_finding_severity', 'severity'),
        Index('idx_finding_status', 'status'),
        Index('idx_finding_control', 'control_family', 'control_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Finding identification
    finding_number = Column(String(100), nullable=True, index=True)  # e.g., "FIND-2026-001"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Related control
    control_family = Column(String(10), nullable=True, index=True)
    control_id = Column(String(50), nullable=True, index=True)
    
    # Severity
    severity = Column(String(50), nullable=False, index=True)  # critical, high, medium, low
    severity_score = Column(Float, nullable=True)
    
    # Finding details
    vulnerability_description = Column(Text, nullable=True)
    impact_description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="open", index=True)  # open, in_progress, resolved, accepted
    
    # POA&M tracking
    poam_id = Column(String(100), nullable=True, index=True)  # Reference to POA&M item
    
    # Timestamps
    identified_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    assessment = relationship("SecurityAssessment", back_populates="findings")
    
    def __repr__(self):
        return (
            f"<AssessmentFinding(id={self.id}, "
            f"finding_number={self.finding_number}, "
            f"severity={self.severity})>"
        )


# ============================================================================
# CA-3: System Interconnections
# ============================================================================

class InterconnectionStatus(str, Enum):
    """System interconnection status"""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class InterconnectionType(str, Enum):
    """Types of system interconnections"""
    DIRECT = "direct"
    NETWORK = "network"
    DATA_SHARING = "data_sharing"
    API = "api"
    BATCH_TRANSFER = "batch_transfer"
    OTHER = "other"


class SystemInterconnection(Base):
    """
    CA-3: System Interconnection
    
    Tracks interconnections between systems with ISA/MOU management.
    """
    __tablename__ = "system_interconnections"
    __table_args__ = (
        Index('idx_interconnection_org_status', 'org_id', 'status'),
        Index('idx_interconnection_systems', 'system_id', 'connected_system_id'),
        Index('idx_interconnection_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Interconnection identification
    interconnection_name = Column(String(255), nullable=False, index=True)
    interconnection_number = Column(String(100), unique=True, nullable=True, index=True)  # e.g., "IC-2026-001"
    interconnection_type = Column(String(50), nullable=False, index=True)
    
    # Systems involved
    system_id = Column(String(128), nullable=False, index=True)  # Our system
    system_name = Column(String(255), nullable=False)
    connected_system_id = Column(String(128), nullable=False, index=True)  # External system
    connected_system_name = Column(String(255), nullable=False)
    connected_organization = Column(String(255), nullable=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=InterconnectionStatus.PROPOSED.value,
        index=True,
    )
    
    # Interconnection details
    purpose = Column(Text, nullable=False)
    data_types_exchanged = Column(JSON, nullable=True)  # List of data types
    data_classification = Column(String(50), nullable=True)  # PHI, PII, etc.
    connection_method = Column(Text, nullable=True)
    connection_endpoints = Column(JSON, nullable=True)  # Connection details
    
    # Security requirements
    security_requirements = Column(JSON, nullable=True)  # List of security requirements
    security_controls = Column(JSON, nullable=True)  # Controls implemented
    
    # ISA/MOU documents
    isa_document_url = Column(String(1000), nullable=True)  # Interconnection Security Agreement
    mou_document_url = Column(String(1000), nullable=True)  # Memorandum of Understanding
    isa_approved = Column(Boolean, default=False, nullable=False)
    mou_approved = Column(Boolean, default=False, nullable=False)
    
    # Approval workflow
    proposed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    proposed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    termination_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    def __repr__(self):
        return (
            f"<SystemInterconnection(id={self.id}, "
            f"interconnection_name={self.interconnection_name}, "
            f"status={self.status})>"
        )


# ============================================================================
# CA-5: Plan of Action & Milestones (POA&M)
# ============================================================================

class POAMStatus(str, Enum):
    """POA&M item status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class POAMPriority(str, Enum):
    """POA&M priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class POAMItem(Base):
    """
    CA-5: Plan of Action & Milestones (POA&M) Item
    
    Tracks remediation plans for security findings.
    """
    __tablename__ = "poam_items"
    __table_args__ = (
        Index('idx_poam_org_status', 'org_id', 'status'),
        Index('idx_poam_priority', 'priority'),
        Index('idx_poam_due_date', 'scheduled_completion_date'),
        Index('idx_poam_control', 'control_family', 'control_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # POA&M identification
    poam_id = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "POAM-2026-001"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Related finding/assessment
    finding_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Reference to assessment finding
    assessment_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Reference to assessment
    
    # Related control
    control_family = Column(String(10), nullable=True, index=True)
    control_id = Column(String(50), nullable=True, index=True)
    
    # Severity and priority
    severity = Column(String(50), nullable=False, index=True)  # critical, high, medium, low
    priority = Column(String(50), nullable=False, index=True)
    risk_score = Column(Float, nullable=True)  # Calculated risk score
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=POAMStatus.OPEN.value,
        index=True,
    )
    
    # Remediation plan
    remediation_plan = Column(Text, nullable=False)
    remediation_steps = Column(JSON, nullable=True)  # List of remediation steps
    responsible_party = Column(String(255), nullable=True)
    responsible_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Milestones
    milestones = Column(JSON, nullable=True)  # List of milestones with dates
    scheduled_completion_date = Column(DateTime(timezone=True), nullable=True, index=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    progress_percent = Column(Float, nullable=False, default=0.0)
    progress_notes = Column(Text, nullable=True)
    
    # Resources
    estimated_cost = Column(Float, nullable=True)
    resources_required = Column(JSON, nullable=True)  # List of required resources
    
    # Status updates
    status_updates = Column(JSON, nullable=True)  # List of status update records
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    def __repr__(self):
        return (
            f"<POAMItem(id={self.id}, "
            f"poam_id={self.poam_id}, "
            f"status={self.status}, "
            f"priority={self.priority})>"
        )


# ============================================================================
# CA-6: Security Authorization
# ============================================================================

class AuthorizationStatus(str, Enum):
    """Authorization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONDITIONAL = "conditional"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AuthorizationType(str, Enum):
    """Types of authorization"""
    INITIAL = "initial"
    REAUTHORIZATION = "reauthorization"
    CONTINUOUS = "continuous"


class SecurityAuthorization(Base):
    """
    CA-6: Security Authorization
    
    Tracks ATO (Authority to Operate) and authorization status.
    """
    __tablename__ = "security_authorizations"
    __table_args__ = (
        Index('idx_auth_org_status', 'org_id', 'status'),
        Index('idx_auth_type', 'authorization_type'),
        Index('idx_auth_expires', 'authorization_expires_at'),
        Index('idx_auth_system', 'system_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Authorization identification
    authorization_number = Column(String(100), unique=True, nullable=True, index=True)  # e.g., "ATO-2026-001"
    system_id = Column(String(128), nullable=False, index=True)
    system_name = Column(String(255), nullable=False)
    authorization_type = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=AuthorizationStatus.PENDING.value,
        index=True,
    )
    
    # Authorization boundary
    authorization_boundary = Column(Text, nullable=True)
    boundary_diagram_url = Column(String(1000), nullable=True)
    
    # Authorization details
    authorization_decision = Column(Text, nullable=True)
    authorization_conditions = Column(JSON, nullable=True)  # List of conditions
    authorization_terms = Column(Text, nullable=True)
    
    # Authorizing official
    authorizing_official_name = Column(String(255), nullable=True)
    authorizing_official_title = Column(String(255), nullable=True)
    authorizing_official_email = Column(String(255), nullable=True)
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Dates
    authorization_date = Column(DateTime(timezone=True), nullable=True, index=True)
    authorization_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    next_reauthorization_due = Column(DateTime(timezone=True), nullable=True)
    
    # Related documents
    authorization_document_url = Column(String(1000), nullable=True)
    ssp_reference = Column(String(255), nullable=True)  # Reference to SSP
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    def __repr__(self):
        return (
            f"<SecurityAuthorization(id={self.id}, "
            f"authorization_number={self.authorization_number}, "
            f"status={self.status})>"
        )


# ============================================================================
# CA-8: Penetration Testing
# ============================================================================

class PenTestStatus(str, Enum):
    """Penetration test status"""
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class PenTestType(str, Enum):
    """Types of penetration tests"""
    NETWORK = "network"
    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    WIRELESS = "wireless"
    SOCIAL_ENGINEERING = "social_engineering"
    PHYSICAL = "physical"
    FULL_SCOPE = "full_scope"


class PenetrationTest(Base):
    """
    CA-8: Penetration Test
    
    Tracks penetration testing activities and results.
    """
    __tablename__ = "penetration_tests"
    __table_args__ = (
        Index('idx_pentest_org_status', 'org_id', 'status'),
        Index('idx_pentest_type', 'test_type'),
        Index('idx_pentest_date', 'test_date'),
        Index('idx_pentest_tester', 'tester_organization'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Test identification
    test_name = Column(String(255), nullable=False, index=True)
    test_number = Column(String(100), unique=True, nullable=True, index=True)  # e.g., "PENTEST-2026-001"
    test_type = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=PenTestStatus.PLANNED.value,
        index=True,
    )
    
    # Test scope
    scope_description = Column(Text, nullable=False)
    systems_in_scope = Column(JSON, nullable=True)  # List of system IDs
    scope_limitations = Column(Text, nullable=True)
    
    # Scheduling
    planned_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_end_date = Column(DateTime(timezone=True), nullable=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    test_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Tester information
    tester_organization = Column(String(255), nullable=True, index=True)
    tester_name = Column(String(255), nullable=True)
    tester_email = Column(String(255), nullable=True)
    tester_type = Column(String(50), nullable=True)  # internal, external, 3pao
    
    # Test results
    vulnerabilities_found = Column(Integer, nullable=False, default=0)
    critical_vulnerabilities = Column(Integer, nullable=False, default=0)
    high_vulnerabilities = Column(Integer, nullable=False, default=0)
    medium_vulnerabilities = Column(Integer, nullable=False, default=0)
    low_vulnerabilities = Column(Integer, nullable=False, default=0)
    
    test_results_summary = Column(Text, nullable=True)
    test_report_url = Column(String(1000), nullable=True)
    
    # Remediation tracking
    remediation_required = Column(Boolean, default=False, nullable=False)
    remediation_verified = Column(Boolean, default=False, nullable=False)
    remediation_verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Next test
    next_test_due = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    findings = relationship("PenTestFinding", back_populates="penetration_test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<PenetrationTest(id={self.id}, "
            f"test_name={self.test_name}, "
            f"status={self.status})>"
        )


class PenTestFinding(Base):
    """
    CA-8: Penetration test finding
    """
    __tablename__ = "pentest_findings"
    __table_args__ = (
        Index('idx_pentest_finding_test', 'penetration_test_id'),
        Index('idx_pentest_finding_severity', 'severity'),
        Index('idx_pentest_finding_status', 'remediation_status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    penetration_test_id = Column(
        UUID(as_uuid=True),
        ForeignKey("penetration_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    finding_number = Column(String(100), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)
    
    vulnerability_details = Column(Text, nullable=True)
    exploitation_steps = Column(Text, nullable=True)
    impact_assessment = Column(Text, nullable=True)
    remediation_recommendations = Column(Text, nullable=True)
    
    remediation_status = Column(String(50), nullable=False, default="open", index=True)  # open, in_progress, remediated, verified
    remediation_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    penetration_test = relationship("PenetrationTest", back_populates="findings")
    
    def __repr__(self):
        return (
            f"<PenTestFinding(id={self.id}, "
            f"finding_number={self.finding_number}, "
            f"severity={self.severity})>"
        )


# ============================================================================
# CA-9: Internal System Connections
# ============================================================================

class InternalConnectionStatus(str, Enum):
    """Internal connection status"""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class InternalSystemConnection(Base):
    """
    CA-9: Internal System Connection
    
    Tracks internal connections between systems within the organization.
    """
    __tablename__ = "internal_system_connections"
    __table_args__ = (
        Index('idx_internal_conn_org_status', 'org_id', 'status'),
        Index('idx_internal_conn_systems', 'source_system_id', 'target_system_id'),
        Index('idx_internal_conn_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Connection identification
    connection_name = Column(String(255), nullable=False, index=True)
    connection_number = Column(String(100), unique=True, nullable=True, index=True)  # e.g., "ICONN-2026-001"
    
    # Systems involved
    source_system_id = Column(String(128), nullable=False, index=True)
    source_system_name = Column(String(255), nullable=False)
    target_system_id = Column(String(128), nullable=False, index=True)
    target_system_name = Column(String(255), nullable=False)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=InternalConnectionStatus.PROPOSED.value,
        index=True,
    )
    
    # Connection details
    purpose = Column(Text, nullable=False)
    connection_type = Column(String(50), nullable=False)  # api, database, network, file_transfer, etc.
    data_types_exchanged = Column(JSON, nullable=True)
    data_classification = Column(String(50), nullable=True)
    
    # Security requirements
    security_requirements = Column(JSON, nullable=True)
    security_controls = Column(JSON, nullable=True)
    connection_security_document_url = Column(String(1000), nullable=True)
    
    # Approval workflow
    proposed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    proposed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    termination_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    def __repr__(self):
        return (
            f"<InternalSystemConnection(id={self.id}, "
            f"connection_name={self.connection_name}, "
            f"status={self.status})>"
        )
