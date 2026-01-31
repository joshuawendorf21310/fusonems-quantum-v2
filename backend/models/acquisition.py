"""
System Acquisition (SA) Models for FedRAMP Compliance

This module provides models for FedRAMP SA controls:
- SA-2: Allocation of Resources
- SA-3: System Development Life Cycle
- SA-4: Acquisition Process
- SA-5: Information System Documentation
- SA-8: Security Engineering Principles
- SA-9: External Information System Services
- SA-10: Developer Configuration Management
- SA-11: Developer Security Testing
- SA-12: Supply Chain Risk Management
- SA-15: Development Process, Standards, and Tools
- SA-16: Developer-Provided Training
- SA-17: Developer Security Architecture
- SA-21: Developer Screening
- SA-22: Unsupported System Components
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
from sqlalchemy.orm import relationship

from core.database import Base


# ============================================================================
# SA-2: Allocation of Resources
# ============================================================================

class BudgetCategory(str, Enum):
    """Budget categories for security resources"""
    SECURITY_TOOLS = "security_tools"
    PERSONNEL = "personnel"
    TRAINING = "training"
    ASSESSMENTS = "assessments"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"
    OTHER = "other"


class ResourceStatus(str, Enum):
    """Resource allocation status"""
    PLANNED = "planned"
    APPROVED = "approved"
    ALLOCATED = "allocated"
    IN_USE = "in_use"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SecurityBudget(Base):
    """
    Security budget tracking for resource allocation.
    
    FedRAMP SA-2: Allocation of resources for security.
    """
    __tablename__ = "security_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Budget Information
    budget_name = Column(String(255), nullable=False, index=True)
    budget_description = Column(Text, nullable=True)
    budget_category = Column(String(32), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    
    # Financial Details
    allocated_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, nullable=False, default=0.0)
    remaining_amount = Column(Float, nullable=False)
    
    # Planning
    planned_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_end_date = Column(DateTime(timezone=True), nullable=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=ResourceStatus.PLANNED.value, index=True)
    
    # Approval
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    resource_plans = relationship("ResourcePlan", back_populates="budget", cascade="all, delete-orphan")
    cost_analyses = relationship("CostAnalysis", back_populates="budget", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_budget_category_status", "budget_category", "status"),
        Index("idx_budget_fiscal_year", "fiscal_year", "status"),
    )


class ResourcePlan(Base):
    """
    Resource planning for security initiatives.
    
    FedRAMP SA-2: Resource planning and allocation.
    """
    __tablename__ = "resource_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    security_budget_id = Column(
        Integer,
        ForeignKey("security_budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Plan Information
    plan_name = Column(String(255), nullable=False, index=True)
    plan_description = Column(Text, nullable=True)
    
    # Resource Requirements
    resource_type = Column(String(100), nullable=False)  # "personnel", "equipment", "software", "services"
    resource_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=ResourceStatus.PLANNED.value, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    budget = relationship("SecurityBudget", back_populates="resource_plans")
    
    __table_args__ = (
        Index("idx_resource_plan_budget_status", "security_budget_id", "status"),
    )


class CostAnalysis(Base):
    """
    Cost analysis for security resource allocation.
    
    FedRAMP SA-2: Cost analysis and budget justification.
    """
    __tablename__ = "cost_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    security_budget_id = Column(
        Integer,
        ForeignKey("security_budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Analysis Information
    analysis_name = Column(String(255), nullable=False, index=True)
    analysis_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    analyzed_by = Column(String(255), nullable=True)
    
    # Cost Breakdown
    direct_costs = Column(Float, nullable=False, default=0.0)
    indirect_costs = Column(Float, nullable=False, default=0.0)
    total_costs = Column(Float, nullable=False)
    
    # Benefits
    expected_benefits = Column(Text, nullable=True)
    roi_estimate = Column(Float, nullable=True)
    
    # Alternatives
    alternatives_considered = Column(JSON, nullable=True)
    selected_option_rationale = Column(Text, nullable=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    budget = relationship("SecurityBudget", back_populates="cost_analyses")
    
    __table_args__ = (
        Index("idx_cost_analysis_budget", "security_budget_id", "analysis_date"),
    )


# ============================================================================
# SA-3: System Development Life Cycle
# ============================================================================

class SDLCPhase(str, Enum):
    """SDLC phases"""
    INITIATION = "initiation"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    OPERATIONS = "operations"
    DISPOSAL = "disposal"


class PhaseStatus(str, Enum):
    """SDLC phase status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class SecurityGateStatus(str, Enum):
    """Security gate status"""
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"
    PENDING = "pending"


class SDLCProject(Base):
    """
    System Development Life Cycle project tracking.
    
    FedRAMP SA-3: SDLC phase tracking and management.
    """
    __tablename__ = "sdlc_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Project Information
    project_name = Column(String(255), nullable=False, index=True)
    project_description = Column(Text, nullable=True)
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Project Management
    project_manager = Column(String(255), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Current Phase
    current_phase = Column(String(32), nullable=False, default=SDLCPhase.INITIATION.value, index=True)
    project_status = Column(String(32), nullable=False, default=PhaseStatus.NOT_STARTED.value, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    phases = relationship("SDLCPhase", back_populates="project", cascade="all, delete-orphan")
    security_gates = relationship("SecurityGate", back_populates="project", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_sdlc_project_status_phase", "project_status", "current_phase"),
    )


class SDLCPhase(Base):
    """
    Individual SDLC phase tracking.
    
    FedRAMP SA-3: Phase-level tracking and approvals.
    """
    __tablename__ = "sdlc_phases"
    
    id = Column(Integer, primary_key=True, index=True)
    sdlc_project_id = Column(
        Integer,
        ForeignKey("sdlc_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Phase Information
    phase_name = Column(String(32), nullable=False, index=True)
    phase_description = Column(Text, nullable=True)
    phase_order = Column(Integer, nullable=False)
    
    # Timeline
    planned_start_date = Column(DateTime(timezone=True), nullable=True)
    planned_end_date = Column(DateTime(timezone=True), nullable=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=PhaseStatus.NOT_STARTED.value, index=True)
    completion_percentage = Column(Float, nullable=False, default=0.0)
    
    # Deliverables
    deliverables = Column(JSON, nullable=True)  # List of deliverables
    deliverables_completed = Column(JSON, nullable=True)  # List of completed deliverables
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    project = relationship("SDLCProject", back_populates="phases")
    
    __table_args__ = (
        Index("idx_sdlc_phase_project_status", "sdlc_project_id", "status"),
        Index("idx_sdlc_phase_order", "sdlc_project_id", "phase_order"),
    )


class SecurityGate(Base):
    """
    Security gate enforcement for SDLC phases.
    
    FedRAMP SA-3: Security gate enforcement and checkpoint validation.
    """
    __tablename__ = "security_gates"
    
    id = Column(Integer, primary_key=True, index=True)
    sdlc_project_id = Column(
        Integer,
        ForeignKey("sdlc_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    phase_id = Column(
        Integer,
        ForeignKey("sdlc_phases.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Gate Information
    gate_name = Column(String(255), nullable=False, index=True)
    gate_description = Column(Text, nullable=True)
    gate_type = Column(String(100), nullable=False)  # "security_review", "code_review", "pen_test", etc.
    
    # Requirements
    requirements = Column(JSON, nullable=True)  # List of requirements
    requirements_met = Column(JSON, nullable=True)  # List of met requirements
    
    # Status
    status = Column(String(32), nullable=False, default=SecurityGateStatus.PENDING.value, index=True)
    
    # Review
    reviewed_by = Column(String(255), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Waiver
    waiver_required = Column(Boolean, nullable=False, default=False)
    waiver_approved = Column(Boolean, nullable=False, default=False)
    waiver_approved_by = Column(String(255), nullable=True)
    waiver_approval_date = Column(DateTime(timezone=True), nullable=True)
    waiver_rationale = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    project = relationship("SDLCProject", back_populates="security_gates")
    
    __table_args__ = (
        Index("idx_security_gate_project_status", "sdlc_project_id", "status"),
        Index("idx_security_gate_phase", "phase_id", "status"),
    )


# ============================================================================
# SA-4: Acquisition Process
# ============================================================================

class ContractStatus(str, Enum):
    """Contract status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    EXECUTED = "executed"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class VendorAssessmentStatus(str, Enum):
    """Vendor security assessment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAIVED = "waived"


class AcquisitionContract(Base):
    """
    Acquisition contract with security requirements.
    
    FedRAMP SA-4: Security requirements in contracts.
    """
    __tablename__ = "acquisition_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contract Information
    contract_number = Column(String(128), nullable=False, unique=True, index=True)
    contract_name = Column(String(255), nullable=False, index=True)
    contract_description = Column(Text, nullable=True)
    
    # Vendor Information
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_contact = Column(String(255), nullable=True)
    vendor_email = Column(String(255), nullable=True)
    
    # Contract Details
    contract_value = Column(Float, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    renewal_date = Column(DateTime(timezone=True), nullable=True)
    
    # Security Requirements
    security_requirements = Column(JSON, nullable=True)  # List of security requirements
    security_requirements_met = Column(Boolean, nullable=False, default=False)
    security_requirements_notes = Column(Text, nullable=True)
    
    # Compliance
    compliance_status = Column(String(32), nullable=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=ContractStatus.DRAFT.value, index=True)
    
    # Approval
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    vendor_assessments = relationship("VendorSecurityAssessment", back_populates="contract", cascade="all, delete-orphan")
    compliance_reviews = relationship("ContractComplianceReview", back_populates="contract", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_contract_status_vendor", "status", "vendor_name"),
        Index("idx_contract_end_date", "end_date", "status"),
    )


class VendorSecurityAssessment(Base):
    """
    Vendor security assessment.
    
    FedRAMP SA-4: Vendor security assessment and evaluation.
    """
    __tablename__ = "vendor_security_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    acquisition_contract_id = Column(
        Integer,
        ForeignKey("acquisition_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Assessment Information
    assessment_name = Column(String(255), nullable=False, index=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assessed_by = Column(String(255), nullable=True)
    
    # Assessment Areas
    security_controls_assessed = Column(JSON, nullable=True)  # List of controls assessed
    security_posture_score = Column(Float, nullable=True)  # 0.0 to 1.0
    risk_level = Column(String(32), nullable=True)  # "low", "medium", "high", "critical"
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    critical_findings = Column(Integer, nullable=False, default=0)
    high_findings = Column(Integer, nullable=False, default=0)
    medium_findings = Column(Integer, nullable=False, default=0)
    low_findings = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Status
    status = Column(String(32), nullable=False, default=VendorAssessmentStatus.PENDING.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    contract = relationship("AcquisitionContract", back_populates="vendor_assessments")
    
    __table_args__ = (
        Index("idx_vendor_assessment_contract_status", "acquisition_contract_id", "status"),
        Index("idx_vendor_assessment_risk", "risk_level", "status"),
    )


class ContractComplianceReview(Base):
    """
    Contract compliance review.
    
    FedRAMP SA-4: Contract compliance monitoring and review.
    """
    __tablename__ = "contract_compliance_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    acquisition_contract_id = Column(
        Integer,
        ForeignKey("acquisition_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Review Information
    review_name = Column(String(255), nullable=False, index=True)
    review_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by = Column(String(255), nullable=True)
    
    # Compliance Check
    requirements_checked = Column(JSON, nullable=True)  # List of requirements checked
    requirements_compliant = Column(Integer, nullable=False, default=0)
    requirements_non_compliant = Column(Integer, nullable=False, default=0)
    compliance_percentage = Column(Float, nullable=False, default=0.0)
    
    # Findings
    non_compliance_findings = Column(JSON, nullable=True)  # List of non-compliance findings
    remediation_required = Column(Boolean, nullable=False, default=False)
    remediation_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=True)  # "compliant", "non_compliant", "remediation_in_progress"
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    contract = relationship("AcquisitionContract", back_populates="compliance_reviews")
    
    __table_args__ = (
        Index("idx_compliance_review_contract_date", "acquisition_contract_id", "review_date"),
    )


# ============================================================================
# SA-5: Information System Documentation
# ============================================================================

class DocumentationType(str, Enum):
    """Documentation types"""
    SYSTEM_DESIGN = "system_design"
    SECURITY_PLAN = "security_plan"
    CONFIGURATION = "configuration"
    OPERATIONS = "operations"
    USER_MANUAL = "user_manual"
    ADMIN_MANUAL = "admin_manual"
    TEST_PLAN = "test_plan"
    INCIDENT_RESPONSE = "incident_response"
    OTHER = "other"


class DocumentationStatus(str, Enum):
    """Documentation status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    OBSOLETE = "obsolete"


class SystemDocumentation(Base):
    """
    Information system documentation inventory.
    
    FedRAMP SA-5: Information system documentation tracking.
    """
    __tablename__ = "system_documentation"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Documentation Information
    document_name = Column(String(255), nullable=False, index=True)
    document_type = Column(String(32), nullable=False, index=True)
    document_description = Column(Text, nullable=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Version Control
    version = Column(String(64), nullable=False, default="1.0", index=True)
    previous_version = Column(String(64), nullable=True)
    version_history = Column(JSON, nullable=True)  # List of version history entries
    
    # Content
    document_location = Column(String(512), nullable=True)  # URL or file path
    document_format = Column(String(32), nullable=True)  # "pdf", "docx", "html", etc.
    document_size_bytes = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=DocumentationStatus.DRAFT.value, index=True)
    
    # Ownership
    author = Column(String(255), nullable=True)
    owner = Column(String(255), nullable=True)
    reviewer = Column(String(255), nullable=True)
    
    # Dates
    created_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_updated_date = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    review_date = Column(DateTime(timezone=True), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    
    # Distribution
    distribution_list = Column(JSON, nullable=True)  # List of recipients
    distribution_tracking = Column(JSON, nullable=True)  # Distribution tracking data
    
    # Access Control
    classification = Column(String(32), nullable=True)  # "public", "internal", "confidential", "restricted"
    access_restrictions = Column(JSON, nullable=True)  # List of access restrictions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    distributions = relationship("DocumentationDistribution", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_documentation_system_type", "system_name", "document_type"),
        Index("idx_documentation_status_version", "status", "version"),
    )


class DocumentationDistribution(Base):
    """
    Documentation distribution tracking.
    
    FedRAMP SA-5: Distribution tracking and access control.
    """
    __tablename__ = "documentation_distributions"
    
    id = Column(Integer, primary_key=True, index=True)
    system_documentation_id = Column(
        Integer,
        ForeignKey("system_documentation.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Distribution Information
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    recipient_role = Column(String(100), nullable=True)
    
    # Distribution Details
    distribution_method = Column(String(100), nullable=True)  # "email", "portal", "physical", etc.
    distribution_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    distributed_by = Column(String(255), nullable=True)
    
    # Acknowledgment
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledgment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Access Tracking
    last_accessed_date = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, nullable=False, default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    document = relationship("SystemDocumentation", back_populates="distributions")
    
    __table_args__ = (
        Index("idx_distribution_document_date", "system_documentation_id", "distribution_date"),
        Index("idx_distribution_acknowledged", "acknowledged", "distribution_date"),
    )


# ============================================================================
# SA-8: Security Engineering Principles
# ============================================================================

class DesignPrinciple(str, Enum):
    """Security design principles"""
    DEFENSE_IN_DEPTH = "defense_in_depth"
    LEAST_PRIVILEGE = "least_privilege"
    FAIL_SECURE = "fail_secure"
    SECURITY_BY_DEFAULT = "security_by_default"
    SECURITY_BY_DESIGN = "security_by_design"
    SEPARATION_OF_DUTIES = "separation_of_duties"
    LEAST_COMMON_MECHANISM = "least_common_mechanism"
    COMPLETE_MEDIATION = "complete_mediation"
    ECONOMY_OF_MECHANISM = "economy_of_mechanism"
    OPEN_DESIGN = "open_design"
    PSYCHOLOGICAL_ACCEPTABILITY = "psychological_acceptability"
    OTHER = "other"


class ReviewStatus(str, Enum):
    """Review status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


class SecurityDesignReview(Base):
    """
    Security design review and architecture validation.
    
    FedRAMP SA-8: Security engineering principles enforcement.
    """
    __tablename__ = "security_design_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Review Information
    review_name = Column(String(255), nullable=False, index=True)
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Design Principles
    principles_applied = Column(JSON, nullable=True)  # List of design principles
    principles_compliance = Column(JSON, nullable=True)  # Compliance status for each principle
    
    # Architecture
    architecture_document = Column(String(512), nullable=True)  # Reference to architecture doc
    threat_model = Column(String(512), nullable=True)  # Reference to threat model
    security_controls = Column(JSON, nullable=True)  # List of security controls
    
    # Review Details
    review_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by = Column(String(255), nullable=True)
    review_team = Column(JSON, nullable=True)  # List of reviewers
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    critical_findings = Column(Integer, nullable=False, default=0)
    high_findings = Column(Integer, nullable=False, default=0)
    medium_findings = Column(Integer, nullable=False, default=0)
    low_findings = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Status
    status = Column(String(32), nullable=False, default=ReviewStatus.PENDING.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    checkpoints = relationship("SecurityCheckpoint", back_populates="review", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_design_review_system_status", "system_name", "status"),
        Index("idx_design_review_date", "review_date", "status"),
    )


class SecurityCheckpoint(Base):
    """
    Security review checkpoint.
    
    FedRAMP SA-8: Security review checkpoints and validation.
    """
    __tablename__ = "security_checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    security_design_review_id = Column(
        Integer,
        ForeignKey("security_design_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Checkpoint Information
    checkpoint_name = Column(String(255), nullable=False, index=True)
    checkpoint_description = Column(Text, nullable=True)
    checkpoint_type = Column(String(100), nullable=False)  # "design", "code", "deployment", etc.
    
    # Requirements
    requirements = Column(JSON, nullable=True)  # List of requirements
    requirements_met = Column(JSON, nullable=True)  # List of met requirements
    
    # Status
    status = Column(String(32), nullable=False, default=ReviewStatus.PENDING.value, index=True)
    
    # Review
    reviewed_by = Column(String(255), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    review = relationship("SecurityDesignReview", back_populates="checkpoints")
    
    __table_args__ = (
        Index("idx_checkpoint_review_status", "security_design_review_id", "status"),
    )


# ============================================================================
# SA-9: External Information System Services
# ============================================================================

class ServiceType(str, Enum):
    """External service types"""
    CLOUD_SERVICE = "cloud_service"
    SAAS = "saas"
    INFRASTRUCTURE = "infrastructure"
    SOFTWARE = "software"
    CONSULTING = "consulting"
    SUPPORT = "support"
    OTHER = "other"


class ServiceStatus(str, Enum):
    """Service status"""
    EVALUATION = "evaluation"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class SLAMetric(str, Enum):
    """SLA metric types"""
    UPTIME = "uptime"
    RESPONSE_TIME = "response_time"
    AVAILABILITY = "availability"
    SECURITY_INCIDENTS = "security_incidents"
    DATA_BREACHES = "data_breaches"
    COMPLIANCE = "compliance"
    OTHER = "other"


class ExternalService(Base):
    """
    External information system service tracking.
    
    FedRAMP SA-9: External information system services management.
    """
    __tablename__ = "external_services"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Service Information
    service_name = Column(String(255), nullable=False, index=True)
    service_description = Column(Text, nullable=True)
    service_type = Column(String(32), nullable=False, index=True)
    
    # Provider Information
    provider_name = Column(String(255), nullable=False, index=True)
    provider_contact = Column(String(255), nullable=True)
    provider_email = Column(String(255), nullable=True)
    
    # Service Details
    service_url = Column(String(512), nullable=True)
    service_start_date = Column(DateTime(timezone=True), nullable=True)
    service_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Data Handling
    data_types_processed = Column(JSON, nullable=True)  # List of data types
    data_classification = Column(String(32), nullable=True)  # Highest classification level
    data_location = Column(String(255), nullable=True)  # Geographic location
    
    # Security Assessment
    security_assessment_completed = Column(Boolean, nullable=False, default=False)
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_score = Column(Float, nullable=True)
    security_risk_level = Column(String(32), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=ServiceStatus.EVALUATION.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    sla_metrics = relationship("SLAMetric", back_populates="service", cascade="all, delete-orphan")
    security_assessments = relationship("ExternalServiceSecurityAssessment", back_populates="service", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_external_service_status_type", "status", "service_type"),
        Index("idx_external_service_provider", "provider_name", "status"),
    )


class SLAMetric(Base):
    """
    SLA metric tracking for external services.
    
    FedRAMP SA-9: SLA management and monitoring.
    """
    __tablename__ = "sla_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    external_service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metric Information
    metric_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(32), nullable=False, index=True)
    
    # SLA Targets
    target_value = Column(Float, nullable=False)
    target_unit = Column(String(32), nullable=True)  # "percent", "seconds", "count", etc.
    measurement_period = Column(String(32), nullable=True)  # "daily", "weekly", "monthly"
    
    # Actual Performance
    actual_value = Column(Float, nullable=True)
    last_measured_date = Column(DateTime(timezone=True), nullable=True)
    
    # Compliance
    sla_met = Column(Boolean, nullable=True)
    sla_violations = Column(Integer, nullable=False, default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    service = relationship("ExternalService", back_populates="sla_metrics")
    
    __table_args__ = (
        Index("idx_sla_metric_service_type", "external_service_id", "metric_type"),
        Index("idx_sla_metric_compliance", "sla_met", "last_measured_date"),
    )


class ExternalServiceSecurityAssessment(Base):
    """
    Security assessment for external services.
    
    FedRAMP SA-9: Security assessment of external services.
    """
    __tablename__ = "external_service_security_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    external_service_id = Column(
        Integer,
        ForeignKey("external_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Assessment Information
    assessment_name = Column(String(255), nullable=False, index=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assessed_by = Column(String(255), nullable=True)
    
    # Assessment Areas
    security_controls_assessed = Column(JSON, nullable=True)  # List of controls assessed
    security_posture_score = Column(Float, nullable=True)  # 0.0 to 1.0
    risk_level = Column(String(32), nullable=True)
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    critical_findings = Column(Integer, nullable=False, default=0)
    high_findings = Column(Integer, nullable=False, default=0)
    medium_findings = Column(Integer, nullable=False, default=0)
    low_findings = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Status
    status = Column(String(32), nullable=False, default=VendorAssessmentStatus.PENDING.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    service = relationship("ExternalService", back_populates="security_assessments")
    
    __table_args__ = (
        Index("idx_external_assessment_service_status", "external_service_id", "status"),
    )


# ============================================================================
# SA-10: Developer Configuration Management
# ============================================================================

class CMStatus(str, Enum):
    """Configuration management status"""
    ACTIVE = "active"
    LOCKED = "locked"
    MERGED = "merged"
    ARCHIVED = "archived"


class BuildStatus(str, Enum):
    """Build status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReleaseStatus(str, Enum):
    """Release status"""
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    IN_TESTING = "in_testing"
    READY_FOR_RELEASE = "ready_for_release"
    RELEASED = "released"
    DEPRECATED = "deprecated"


class SourceCodeRepository(Base):
    """
    Source code repository tracking.
    
    FedRAMP SA-10: Developer configuration management - source code version control.
    """
    __tablename__ = "source_code_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Repository Information
    repository_name = Column(String(255), nullable=False, index=True)
    repository_url = Column(String(512), nullable=False, unique=True, index=True)
    repository_type = Column(String(32), nullable=False)  # "git", "svn", "mercurial", etc.
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Access Control
    access_restrictions = Column(JSON, nullable=True)  # List of access restrictions
    authorized_users = Column(JSON, nullable=True)  # List of authorized users
    
    # Status
    status = Column(String(32), nullable=False, default=CMStatus.ACTIVE.value, index=True)
    
    # Monitoring
    last_sync_date = Column(DateTime(timezone=True), nullable=True)
    last_commit_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    branches = relationship("CodeBranch", back_populates="repository", cascade="all, delete-orphan")
    builds = relationship("Build", back_populates="repository", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_repository_system_status", "system_name", "status"),
    )


class CodeBranch(Base):
    """
    Code branch tracking.
    
    FedRAMP SA-10: Branch management and version control.
    """
    __tablename__ = "code_branches"
    
    id = Column(Integer, primary_key=True, index=True)
    source_code_repository_id = Column(
        Integer,
        ForeignKey("source_code_repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Branch Information
    branch_name = Column(String(255), nullable=False, index=True)
    branch_type = Column(String(32), nullable=False)  # "main", "develop", "feature", "hotfix", "release"
    
    # Version Control
    base_branch = Column(String(255), nullable=True)
    latest_commit = Column(String(128), nullable=True)
    commit_count = Column(Integer, nullable=False, default=0)
    
    # Status
    status = Column(String(32), nullable=False, default=CMStatus.ACTIVE.value, index=True)
    
    # Protection
    protected = Column(Boolean, nullable=False, default=False)
    requires_review = Column(Boolean, nullable=False, default=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    
    # Dates
    created_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_commit_date = Column(DateTime(timezone=True), nullable=True)
    merged_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    repository = relationship("SourceCodeRepository", back_populates="branches")
    
    __table_args__ = (
        Index("idx_branch_repository_status", "source_code_repository_id", "status"),
        Index("idx_branch_type", "branch_type", "status"),
    )


class Build(Base):
    """
    Build management tracking.
    
    FedRAMP SA-10: Build management and automation.
    """
    __tablename__ = "builds"
    
    id = Column(Integer, primary_key=True, index=True)
    source_code_repository_id = Column(
        Integer,
        ForeignKey("source_code_repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    branch_id = Column(
        Integer,
        ForeignKey("code_branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Build Information
    build_number = Column(String(128), nullable=False, index=True)
    build_type = Column(String(32), nullable=False)  # "automated", "manual", "scheduled"
    
    # Source
    commit_hash = Column(String(128), nullable=True)
    branch_name = Column(String(255), nullable=True)
    
    # Build Details
    build_configuration = Column(JSON, nullable=True)  # Build configuration
    build_output = Column(Text, nullable=True)  # Build output/logs
    build_artifacts = Column(JSON, nullable=True)  # List of build artifacts
    
    # Status
    status = Column(String(32), nullable=False, default=BuildStatus.PENDING.value, index=True)
    
    # Execution
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results
    tests_passed = Column(Integer, nullable=True)
    tests_failed = Column(Integer, nullable=True)
    security_scan_passed = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    repository = relationship("SourceCodeRepository", back_populates="builds")
    
    __table_args__ = (
        Index("idx_build_repository_status", "source_code_repository_id", "status"),
        Index("idx_build_branch_date", "branch_id", "started_at"),
    )


class Release(Base):
    """
    Release management tracking.
    
    FedRAMP SA-10: Release management and deployment.
    """
    __tablename__ = "releases"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Release Information
    release_name = Column(String(255), nullable=False, index=True)
    release_version = Column(String(128), nullable=False, index=True)
    release_description = Column(Text, nullable=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Source
    build_id = Column(Integer, ForeignKey("builds.id", ondelete="SET NULL"), nullable=True, index=True)
    source_branch = Column(String(255), nullable=True)
    
    # Release Details
    release_notes = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)  # List of changes
    dependencies = Column(JSON, nullable=True)  # List of dependencies
    
    # Status
    status = Column(String(32), nullable=False, default=ReleaseStatus.PLANNED.value, index=True)
    
    # Deployment
    deployment_plan = Column(Text, nullable=True)
    deployment_date = Column(DateTime(timezone=True), nullable=True)
    deployed_by = Column(String(255), nullable=True)
    deployment_environment = Column(String(100), nullable=True)  # "development", "staging", "production"
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Rollback
    rollback_available = Column(Boolean, nullable=False, default=False)
    rollback_plan = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_release_system_status", "system_name", "status"),
        Index("idx_release_version", "release_version", "status"),
    )


# ============================================================================
# SA-11: Developer Security Testing
# ============================================================================

class TestType(str, Enum):
    """Security test types"""
    SAST = "sast"  # Static Application Security Testing
    DAST = "dast"  # Dynamic Application Security Testing
    IAST = "iast"  # Interactive Application Security Testing
    SCA = "sca"  # Software Composition Analysis
    PENETRATION = "penetration"
    CODE_REVIEW = "code_review"
    OTHER = "other"


class TestStatus(str, Enum):
    """Test status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityTest(Base):
    """
    Developer security testing record.
    
    FedRAMP SA-11: Developer security testing and validation.
    """
    __tablename__ = "security_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Test Information
    test_name = Column(String(255), nullable=False, index=True)
    test_type = Column(String(32), nullable=False, index=True)
    test_description = Column(Text, nullable=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Source
    build_id = Column(Integer, ForeignKey("builds.id", ondelete="SET NULL"), nullable=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_name = Column(String(255), nullable=True)
    commit_hash = Column(String(128), nullable=True)
    
    # Test Configuration
    test_tool = Column(String(255), nullable=True)  # Tool used for testing
    test_configuration = Column(JSON, nullable=True)  # Test configuration
    
    # Execution
    status = Column(String(32), nullable=False, default=TestStatus.PENDING.value, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results
    vulnerabilities_found = Column(Integer, nullable=False, default=0)
    vulnerabilities_critical = Column(Integer, nullable=False, default=0)
    vulnerabilities_high = Column(Integer, nullable=False, default=0)
    vulnerabilities_medium = Column(Integer, nullable=False, default=0)
    vulnerabilities_low = Column(Integer, nullable=False, default=0)
    
    # Test Output
    test_output = Column(JSON, nullable=True)  # Test results/output
    test_report_url = Column(String(512), nullable=True)  # Link to detailed report
    
    # Pass/Fail
    test_passed = Column(Boolean, nullable=True)
    pass_criteria = Column(JSON, nullable=True)  # Pass criteria
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    test_results = relationship("SecurityTestResult", back_populates="test", cascade="all, delete-orphan")
    remediations = relationship("TestRemediation", back_populates="test", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_security_test_system_type", "system_name", "test_type"),
        Index("idx_security_test_status_date", "status", "started_at"),
    )


class SecurityTestResult(Base):
    """
    Individual security test result/vulnerability finding.
    
    FedRAMP SA-11: Test results tracking and vulnerability identification.
    """
    __tablename__ = "security_test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    security_test_id = Column(
        Integer,
        ForeignKey("security_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Finding Information
    finding_id = Column(String(128), nullable=True, index=True)  # Tool-specific finding ID
    finding_title = Column(String(255), nullable=False, index=True)
    finding_description = Column(Text, nullable=True)
    
    # Vulnerability Details
    vulnerability_type = Column(String(100), nullable=True)  # e.g., "SQL Injection", "XSS"
    cwe_id = Column(String(32), nullable=True)  # CWE identifier
    severity = Column(String(32), nullable=False, index=True)
    
    # Location
    file_path = Column(String(512), nullable=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default="open", index=True)  # "open", "in_progress", "fixed", "false_positive", "accepted"
    
    # Remediation
    remediation_status = Column(String(32), nullable=True)  # "not_started", "in_progress", "completed"
    remediation_notes = Column(Text, nullable=True)
    fixed_in_build = Column(String(128), nullable=True)
    fixed_in_release = Column(String(128), nullable=True)
    
    # Verification
    verified_fixed = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(255), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    test = relationship("SecurityTest", back_populates="test_results")
    
    __table_args__ = (
        Index("idx_test_result_test_status", "security_test_id", "status"),
        Index("idx_test_result_severity", "severity", "status"),
    )


class TestRemediation(Base):
    """
    Test remediation tracking.
    
    FedRAMP SA-11: Vulnerability remediation tracking.
    """
    __tablename__ = "test_remediations"
    
    id = Column(Integer, primary_key=True, index=True)
    security_test_id = Column(
        Integer,
        ForeignKey("security_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    test_result_id = Column(
        Integer,
        ForeignKey("security_test_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Remediation Information
    remediation_plan = Column(Text, nullable=False)
    remediation_actions = Column(JSON, nullable=True)  # List of remediation actions
    
    # Assignment
    assigned_to = Column(String(255), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default="planned", index=True)  # "planned", "in_progress", "completed", "cancelled"
    completion_percentage = Column(Float, nullable=False, default=0.0)
    
    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(255), nullable=True)
    
    # Verification
    verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(255), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    test = relationship("SecurityTest", back_populates="remediations")
    
    __table_args__ = (
        Index("idx_remediation_test_status", "security_test_id", "status"),
    )


# ============================================================================
# SA-12: Supply Chain Risk Management
# ============================================================================

class SupplierRiskLevel(str, Enum):
    """Supplier risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComponentType(str, Enum):
    """Component types"""
    SOFTWARE_LIBRARY = "software_library"
    HARDWARE = "hardware"
    FIRMWARE = "firmware"
    SERVICE = "service"
    OTHER = "other"


class SupplyChainComponent(Base):
    """
    Supply chain component tracking.
    
    FedRAMP SA-12: Supply chain risk management - component tracking.
    """
    __tablename__ = "supply_chain_components"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Component Information
    component_name = Column(String(255), nullable=False, index=True)
    component_type = Column(String(32), nullable=False, index=True)
    component_version = Column(String(128), nullable=True)
    component_description = Column(Text, nullable=True)
    
    # Supplier Information
    supplier_name = Column(String(255), nullable=False, index=True)
    supplier_contact = Column(String(255), nullable=True)
    supplier_country = Column(String(100), nullable=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Provenance
    origin_country = Column(String(100), nullable=True)
    manufacturing_location = Column(String(255), nullable=True)
    supply_chain_path = Column(JSON, nullable=True)  # Supply chain path
    
    # Risk Assessment
    risk_level = Column(String(32), nullable=True, index=True)
    risk_assessment_date = Column(DateTime(timezone=True), nullable=True)
    risk_assessment_notes = Column(Text, nullable=True)
    
    # Security Assessment
    security_assessment_completed = Column(Boolean, nullable=False, default=False)
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_score = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    supplier_assessments = relationship("SupplierSecurityAssessment", back_populates="component", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_component_supplier_risk", "supplier_name", "risk_level"),
        Index("idx_component_system_type", "system_name", "component_type"),
    )


class SupplierSecurityAssessment(Base):
    """
    Supplier security assessment.
    
    FedRAMP SA-12: Supplier security assessment and evaluation.
    """
    __tablename__ = "supplier_security_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    supply_chain_component_id = Column(
        Integer,
        ForeignKey("supply_chain_components.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Assessment Information
    assessment_name = Column(String(255), nullable=False, index=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assessed_by = Column(String(255), nullable=True)
    
    # Assessment Areas
    security_controls_assessed = Column(JSON, nullable=True)  # List of controls assessed
    security_posture_score = Column(Float, nullable=True)  # 0.0 to 1.0
    risk_level = Column(String(32), nullable=True, index=True)
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    critical_findings = Column(Integer, nullable=False, default=0)
    high_findings = Column(Integer, nullable=False, default=0)
    medium_findings = Column(Integer, nullable=False, default=0)
    low_findings = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Third-Party Risk
    third_party_risks = Column(JSON, nullable=True)  # List of third-party risks identified
    
    # Status
    status = Column(String(32), nullable=False, default=VendorAssessmentStatus.PENDING.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    component = relationship("SupplyChainComponent", back_populates="supplier_assessments")
    
    __table_args__ = (
        Index("idx_supplier_assessment_component_status", "supply_chain_component_id", "status"),
        Index("idx_supplier_assessment_risk", "risk_level", "status"),
    )


# ============================================================================
# SA-15: Development Process, Standards, and Tools
# ============================================================================

class ToolStatus(str, Enum):
    """Tool status"""
    APPROVED = "approved"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class StandardStatus(str, Enum):
    """Standard status"""
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class DevelopmentTool(Base):
    """
    Development tool approval and management.
    
    FedRAMP SA-15: Development process, standards, and tools - tool approval.
    """
    __tablename__ = "development_tools"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tool Information
    tool_name = Column(String(255), nullable=False, index=True)
    tool_type = Column(String(100), nullable=False)  # "ide", "build", "test", "security", "ci_cd", etc.
    tool_vendor = Column(String(255), nullable=True)
    tool_version = Column(String(128), nullable=True)
    
    # Tool Details
    tool_description = Column(Text, nullable=True)
    tool_url = Column(String(512), nullable=True)
    
    # Usage
    systems_using = Column(JSON, nullable=True)  # List of systems using this tool
    usage_count = Column(Integer, nullable=False, default=0)
    
    # Security Assessment
    security_assessment_completed = Column(Boolean, nullable=False, default=False)
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_notes = Column(Text, nullable=True)
    
    # Approval
    status = Column(String(32), nullable=False, default=ToolStatus.PENDING_APPROVAL.value, index=True)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Compliance
    compliance_checked = Column(Boolean, nullable=False, default=False)
    compliance_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_tool_type_status", "tool_type", "status"),
    )


class SecureCodingStandard(Base):
    """
    Secure coding standards and compliance.
    
    FedRAMP SA-15: Secure coding standards enforcement.
    """
    __tablename__ = "secure_coding_standards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Standard Information
    standard_name = Column(String(255), nullable=False, index=True)
    standard_type = Column(String(100), nullable=False)  # "language_specific", "framework", "general", etc.
    standard_version = Column(String(128), nullable=True)
    
    # Standard Details
    standard_description = Column(Text, nullable=True)
    standard_reference = Column(String(512), nullable=True)  # URL or document reference
    
    # Requirements
    requirements = Column(JSON, nullable=True)  # List of requirements/rules
    mandatory_requirements = Column(JSON, nullable=True)  # List of mandatory requirements
    
    # Compliance
    compliance_checking_enabled = Column(Boolean, nullable=False, default=False)
    compliance_tool = Column(String(255), nullable=True)  # Tool used for compliance checking
    
    # Status
    status = Column(String(32), nullable=False, default=StandardStatus.ACTIVE.value, index=True)
    
    # Applicability
    applicable_languages = Column(JSON, nullable=True)  # List of applicable programming languages
    applicable_systems = Column(JSON, nullable=True)  # List of applicable systems
    
    # Enforcement
    enforcement_level = Column(String(32), nullable=True)  # "mandatory", "recommended", "optional"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_standard_type_status", "standard_type", "status"),
    )


class ComplianceCheck(Base):
    """
    Compliance checking for development standards.
    
    FedRAMP SA-15: Compliance checking and enforcement.
    """
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Check Information
    check_name = Column(String(255), nullable=False, index=True)
    standard_id = Column(Integer, ForeignKey("secure_coding_standards.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Source
    build_id = Column(Integer, ForeignKey("builds.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_name = Column(String(255), nullable=True)
    commit_hash = Column(String(128), nullable=True)
    
    # Check Details
    check_tool = Column(String(255), nullable=True)
    check_configuration = Column(JSON, nullable=True)
    
    # Execution
    check_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    checked_by = Column(String(255), nullable=True)
    
    # Results
    requirements_checked = Column(Integer, nullable=False, default=0)
    requirements_passed = Column(Integer, nullable=False, default=0)
    requirements_failed = Column(Integer, nullable=False, default=0)
    compliance_percentage = Column(Float, nullable=False, default=0.0)
    
    # Findings
    violations = Column(JSON, nullable=True)  # List of violations
    critical_violations = Column(Integer, nullable=False, default=0)
    high_violations = Column(Integer, nullable=False, default=0)
    medium_violations = Column(Integer, nullable=False, default=0)
    low_violations = Column(Integer, nullable=False, default=0)
    
    # Status
    compliant = Column(Boolean, nullable=False, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_compliance_check_system_date", "system_name", "check_date"),
        Index("idx_compliance_check_standard", "standard_id", "check_date"),
    )


# ============================================================================
# SA-16: Developer-Provided Training
# ============================================================================

class TrainingStatus(str, Enum):
    """Training status"""
    REQUIRED = "required"
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    WAIVED = "waived"


class DeveloperTraining(Base):
    """
    Developer training requirements and tracking.
    
    FedRAMP SA-16: Developer-provided training.
    """
    __tablename__ = "developer_training"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Training Information
    training_name = Column(String(255), nullable=False, index=True)
    training_description = Column(Text, nullable=True)
    training_type = Column(String(100), nullable=False)  # "secure_coding", "security_awareness", "tool_training", etc.
    
    # Requirements
    required_for_roles = Column(JSON, nullable=True)  # List of roles that require this training
    required_for_systems = Column(JSON, nullable=True)  # List of systems that require this training
    mandatory = Column(Boolean, nullable=False, default=True)
    
    # Training Details
    training_provider = Column(String(255), nullable=True)
    training_duration_hours = Column(Float, nullable=True)
    training_format = Column(String(100), nullable=True)  # "online", "in_person", "hybrid"
    training_url = Column(String(512), nullable=True)
    
    # Validity
    valid_for_days = Column(Integer, nullable=True)  # Days until training expires
    requires_refresher = Column(Boolean, nullable=False, default=False)
    refresher_interval_days = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    training_records = relationship("DeveloperTrainingRecord", back_populates="training", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_training_type", "training_type", "mandatory"),
    )


class DeveloperTrainingRecord(Base):
    """
    Developer training completion record.
    
    FedRAMP SA-16: Training completion tracking.
    """
    __tablename__ = "developer_training_records"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_training_id = Column(
        Integer,
        ForeignKey("developer_training.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Developer Information
    developer_name = Column(String(255), nullable=False, index=True)
    developer_email = Column(String(255), nullable=True, index=True)
    developer_role = Column(String(100), nullable=True)
    
    # Training Status
    status = Column(String(32), nullable=False, default=TrainingStatus.REQUIRED.value, index=True)
    
    # Enrollment
    enrolled_date = Column(DateTime(timezone=True), nullable=True)
    started_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Completion Details
    completion_percentage = Column(Float, nullable=False, default=0.0)
    score = Column(Float, nullable=True)  # Test/assessment score if applicable
    passed = Column(Boolean, nullable=True)
    
    # Certification
    certificate_issued = Column(Boolean, nullable=False, default=False)
    certificate_number = Column(String(128), nullable=True)
    certificate_url = Column(String(512), nullable=True)
    
    # Expiration
    expires_date = Column(DateTime(timezone=True), nullable=True)
    is_expired = Column(Boolean, nullable=False, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    training = relationship("DeveloperTraining", back_populates="training_records")
    
    __table_args__ = (
        Index("idx_training_record_training_status", "developer_training_id", "status"),
        Index("idx_training_record_developer", "developer_email", "status"),
        Index("idx_training_record_expires", "expires_date", "is_expired"),
    )


# ============================================================================
# SA-17: Developer Security Architecture
# ============================================================================

class ArchitectureReviewStatus(str, Enum):
    """Architecture review status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


class SecurityDesignPattern(str, Enum):
    """Security design patterns"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    SESSION_MANAGEMENT = "session_management"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    AUDITING = "auditing"
    OTHER = "other"


class DeveloperArchitecture(Base):
    """
    Developer security architecture review.
    
    FedRAMP SA-17: Developer security architecture and design.
    """
    __tablename__ = "developer_architectures"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Architecture Information
    architecture_name = Column(String(255), nullable=False, index=True)
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Architecture Details
    architecture_description = Column(Text, nullable=True)
    architecture_document = Column(String(512), nullable=True)  # Reference to architecture document
    
    # Design Patterns
    security_patterns_used = Column(JSON, nullable=True)  # List of security design patterns
    pattern_implementation = Column(JSON, nullable=True)  # Pattern implementation details
    
    # Threat Modeling
    threat_model = Column(String(512), nullable=True)  # Reference to threat model
    threats_identified = Column(JSON, nullable=True)  # List of threats
    mitigations = Column(JSON, nullable=True)  # List of mitigations
    
    # Security Controls
    security_controls = Column(JSON, nullable=True)  # List of security controls
    control_implementation = Column(JSON, nullable=True)  # Control implementation details
    
    # Review
    review_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by = Column(String(255), nullable=True)
    review_team = Column(JSON, nullable=True)  # List of reviewers
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    critical_findings = Column(Integer, nullable=False, default=0)
    high_findings = Column(Integer, nullable=False, default=0)
    medium_findings = Column(Integer, nullable=False, default=0)
    low_findings = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Status
    status = Column(String(32), nullable=False, default=ArchitectureReviewStatus.PENDING.value, index=True)
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_architecture_system_status", "system_name", "status"),
        Index("idx_architecture_review_date", "review_date", "status"),
    )


# ============================================================================
# SA-21: Developer Screening
# ============================================================================

class ScreeningStatus(str, Enum):
    """Screening status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAIVED = "waived"


class ScreeningType(str, Enum):
    """Screening types"""
    BACKGROUND_CHECK = "background_check"
    CREDIT_CHECK = "credit_check"
    REFERENCE_CHECK = "reference_check"
    EDUCATION_VERIFICATION = "education_verification"
    CERTIFICATION_VERIFICATION = "certification_verification"
    SECURITY_CLEARANCE = "security_clearance"
    OTHER = "other"


class DeveloperScreening(Base):
    """
    Developer screening and background check tracking.
    
    FedRAMP SA-21: Developer screening requirements.
    """
    __tablename__ = "developer_screenings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Developer Information
    developer_name = Column(String(255), nullable=False, index=True)
    developer_email = Column(String(255), nullable=True, index=True)
    developer_role = Column(String(100), nullable=True)
    
    # Screening Information
    screening_type = Column(String(32), nullable=False, index=True)
    screening_requirements = Column(JSON, nullable=True)  # List of screening requirements
    
    # Screening Details
    screening_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    screened_by = Column(String(255), nullable=True)  # Screening agency or person
    screening_agency = Column(String(255), nullable=True)
    
    # Results
    status = Column(String(32), nullable=False, default=ScreeningStatus.PENDING.value, index=True)
    passed = Column(Boolean, nullable=True)
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings
    adverse_findings = Column(Boolean, nullable=False, default=False)
    adverse_findings_description = Column(Text, nullable=True)
    
    # Access Management
    access_granted = Column(Boolean, nullable=False, default=False)
    access_level = Column(String(100), nullable=True)  # Access level granted
    access_granted_date = Column(DateTime(timezone=True), nullable=True)
    access_granted_by = Column(String(255), nullable=True)
    
    # Validity
    valid_until_date = Column(DateTime(timezone=True), nullable=True)
    requires_renewal = Column(Boolean, nullable=False, default=False)
    renewal_interval_days = Column(Integer, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_screening_developer_status", "developer_email", "status"),
        Index("idx_screening_type_status", "screening_type", "status"),
        Index("idx_screening_access", "access_granted", "access_granted_date"),
    )


# ============================================================================
# SA-22: Unsupported System Components
# ============================================================================

class ComponentStatus(str, Enum):
    """Component status"""
    SUPPORTED = "supported"
    END_OF_LIFE = "end_of_life"
    END_OF_SUPPORT = "end_of_support"
    UNSUPPORTED = "unsupported"
    REPLACED = "replaced"


class ReplacementStatus(str, Enum):
    """Replacement status"""
    NOT_PLANNED = "not_planned"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UnsupportedComponent(Base):
    """
    Unsupported system component tracking.
    
    FedRAMP SA-22: Unsupported system components tracking and replacement planning.
    """
    __tablename__ = "unsupported_components"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Component Information
    component_name = Column(String(255), nullable=False, index=True)
    component_type = Column(String(100), nullable=False)  # "software", "hardware", "firmware", "library", etc.
    component_version = Column(String(128), nullable=True)
    component_vendor = Column(String(255), nullable=True)
    
    # System Association
    system_name = Column(String(255), nullable=False, index=True)
    system_id = Column(String(128), nullable=True, index=True)
    
    # Lifecycle Dates
    eol_date = Column(DateTime(timezone=True), nullable=True, index=True)  # End of Life
    eos_date = Column(DateTime(timezone=True), nullable=True, index=True)  # End of Support
    eol_announced_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=ComponentStatus.SUPPORTED.value, index=True)
    
    # Risk Assessment
    risk_level = Column(String(32), nullable=True, index=True)  # "low", "medium", "high", "critical"
    risk_assessment_date = Column(DateTime(timezone=True), nullable=True)
    risk_assessment_notes = Column(Text, nullable=True)
    
    # Vulnerabilities
    known_vulnerabilities = Column(Integer, nullable=False, default=0)
    unpatched_vulnerabilities = Column(Integer, nullable=False, default=0)
    vulnerability_details = Column(JSON, nullable=True)  # List of vulnerabilities
    
    # Replacement Planning
    replacement_required = Column(Boolean, nullable=False, default=False)
    replacement_status = Column(String(32), nullable=True, index=True)
    replacement_component = Column(String(255), nullable=True)
    replacement_plan = Column(Text, nullable=True)
    replacement_target_date = Column(DateTime(timezone=True), nullable=True)
    replacement_completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Mitigation
    mitigation_measures = Column(Text, nullable=True)
    mitigation_effectiveness = Column(String(32), nullable=True)  # "effective", "partial", "ineffective"
    
    # Monitoring
    monitoring_enabled = Column(Boolean, nullable=False, default=False)
    last_monitored_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_unsupported_component_status_risk", "status", "risk_level"),
        Index("idx_unsupported_component_eol", "eol_date", "status"),
        Index("idx_unsupported_component_replacement", "replacement_status", "replacement_target_date"),
    )
