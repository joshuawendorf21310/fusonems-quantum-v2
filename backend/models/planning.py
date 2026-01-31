"""
Planning (PL) Models for FedRAMP Compliance

This module provides models for:
- PL-2: System Security Plan (SSP)
- PL-4: Rules of Behavior
- PL-7: Security Concept of Operations (CONOPS)
- PL-8: Information Security Architecture
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


# ============================================================================
# PL-2: System Security Plan (SSP)
# ============================================================================

class SSPStatus(str, Enum):
    """SSP document status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class ControlFamily(str, Enum):
    """FedRAMP control families"""
    AC = "AC"  # Access Control
    AT = "AT"  # Awareness and Training
    AU = "AU"  # Audit and Accountability
    CA = "CA"  # Assessment and Authorization
    CM = "CM"  # Configuration Management
    CP = "CP"  # Contingency Planning
    IA = "IA"  # Identification and Authentication
    IR = "IR"  # Incident Response
    MA = "MA"  # Maintenance
    MP = "MP"  # Media Protection
    PE = "PE"  # Physical and Environmental Protection
    PL = "PL"  # Planning
    PS = "PS"  # Personnel Security
    RA = "RA"  # Risk Assessment
    SA = "SA"  # System and Services Acquisition
    SC = "SC"  # System and Communications Protection
    SI = "SI"  # System and Information Integrity
    SR = "SR"  # Supply Chain Risk Management


class SystemSecurityPlan(Base):
    """
    PL-2: System Security Plan (SSP)
    
    Comprehensive security plan documenting all security controls,
    implementation details, and system architecture.
    """
    __tablename__ = "system_security_plans"
    __table_args__ = (
        Index('idx_ssp_org_status', 'org_id', 'status'),
        Index('idx_ssp_version', 'version'),
        Index('idx_ssp_active', 'is_active'),
        Index('idx_ssp_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # SSP identification
    ssp_name = Column(String(255), nullable=False, index=True)
    system_name = Column(String(255), nullable=False)
    system_id = Column(String(128), nullable=True, unique=True, index=True)
    version = Column(String(50), nullable=False, index=True)  # e.g., "1.0", "2.1"
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=SSPStatus.DRAFT.value,
        index=True,
    )
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # System information
    system_description = Column(Text, nullable=True)
    system_owner = Column(String(255), nullable=True)
    system_administrator = Column(String(255), nullable=True)
    information_system_security_officer = Column(String(255), nullable=True)
    
    # System boundaries
    authorization_boundary = Column(Text, nullable=True)
    system_boundary_diagram_url = Column(String(1000), nullable=True)
    network_diagram_url = Column(String(1000), nullable=True)
    
    # Control implementations - stores control details per family
    control_implementations = Column(JSON, nullable=False, default=dict)  # {family: {control_id: implementation_details}}
    
    # Evidence collection
    evidence_artifacts = Column(JSON, nullable=True)  # List of evidence document references
    evidence_summary = Column(Text, nullable=True)
    
    # Document content
    ssp_content = Column(Text, nullable=True)  # Full SSP text (can be generated)
    ssp_document_url = Column(String(1000), nullable=True)  # URL to generated PDF/document
    
    # Approval workflow
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Review and updates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    control_sections = relationship("SSPControlSection", back_populates="ssp", cascade="all, delete-orphan")
    versions = relationship("SSPVersion", back_populates="ssp", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<SystemSecurityPlan(id={self.id}, "
            f"ssp_name={self.ssp_name}, "
            f"version={self.version}, "
            f"status={self.status})>"
        )


class SSPControlSection(Base):
    """
    PL-2: Individual control section within SSP
    
    Stores detailed implementation details for each control.
    """
    __tablename__ = "ssp_control_sections"
    __table_args__ = (
        Index('idx_ssp_section_ssp', 'ssp_id'),
        Index('idx_ssp_section_control', 'control_family', 'control_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    ssp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("system_security_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Control identification
    control_family = Column(String(10), nullable=False, index=True)  # AC, AT, AU, etc.
    control_id = Column(String(50), nullable=False, index=True)  # e.g., "AC-2", "AC-2(1)"
    control_title = Column(String(255), nullable=True)
    
    # Implementation details
    implementation_description = Column(Text, nullable=False)
    implementation_status = Column(String(50), nullable=False, default="planned")  # planned, partial, implemented, alternative
    implementation_narrative = Column(Text, nullable=True)
    
    # Control parameters
    control_parameters = Column(JSON, nullable=True)  # Control-specific parameters
    
    # Related controls
    related_controls = Column(JSON, nullable=True)  # List of related control IDs
    
    # Evidence
    evidence_references = Column(JSON, nullable=True)  # List of evidence document IDs/URLs
    test_procedures = Column(Text, nullable=True)
    test_results = Column(JSON, nullable=True)
    
    # Responsibility
    responsible_role = Column(String(100), nullable=True)
    responsible_party = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    ssp = relationship("SystemSecurityPlan", back_populates="control_sections")
    
    def __repr__(self):
        return (
            f"<SSPControlSection(id={self.id}, "
            f"control_family={self.control_family}, "
            f"control_id={self.control_id})>"
        )


class SSPVersion(Base):
    """
    PL-2: SSP version history
    
    Tracks version history and changes between SSP versions.
    """
    __tablename__ = "ssp_versions"
    __table_args__ = (
        Index('idx_ssp_version_ssp', 'ssp_id'),
        Index('idx_ssp_version_number', 'version_number'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    ssp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("system_security_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    version_number = Column(String(50), nullable=False, index=True)
    change_summary = Column(Text, nullable=True)
    changes_made = Column(JSON, nullable=True)  # List of changes
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    ssp = relationship("SystemSecurityPlan", back_populates="versions")
    
    def __repr__(self):
        return (
            f"<SSPVersion(id={self.id}, "
            f"ssp_id={self.ssp_id}, "
            f"version_number={self.version_number})>"
        )


# ============================================================================
# PL-4: Rules of Behavior
# ============================================================================

class RulesOfBehaviorStatus(str, Enum):
    """Rules of Behavior document status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class RulesOfBehavior(Base):
    """
    PL-4: Rules of Behavior
    
    Establishes rules of behavior for system users.
    """
    __tablename__ = "rules_of_behavior"
    __table_args__ = (
        Index('idx_rob_org_status', 'org_id', 'status'),
        Index('idx_rob_active', 'is_active'),
        Index('idx_rob_version', 'version'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Document identification
    title = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=RulesOfBehaviorStatus.DRAFT.value,
        index=True,
    )
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # Content
    rules_content = Column(Text, nullable=False)  # Full rules text
    rules_document_url = Column(String(1000), nullable=True)  # Generated PDF URL
    
    # Rules sections
    rules_sections = Column(JSON, nullable=True)  # Structured rules by category
    
    # Approval
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Review
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    acknowledgments = relationship("RulesOfBehaviorAcknowledgment", back_populates="rules", cascade="all, delete-orphan")
    versions = relationship("RulesOfBehaviorVersion", back_populates="rules", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<RulesOfBehavior(id={self.id}, "
            f"title={self.title}, "
            f"version={self.version})>"
        )


class RulesOfBehaviorAcknowledgment(Base):
    """
    PL-4: User acknowledgment of Rules of Behavior
    
    Tracks user acknowledgments of rules.
    """
    __tablename__ = "rules_of_behavior_acknowledgments"
    __table_args__ = (
        Index('idx_rob_ack_rules', 'rules_id'),
        Index('idx_rob_ack_user', 'user_id'),
        Index('idx_rob_ack_acknowledged', 'acknowledged_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    rules_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules_of_behavior.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Acknowledgment details
    acknowledged_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    acknowledgment_ip_address = Column(String(45), nullable=True)
    acknowledgment_user_agent = Column(Text, nullable=True)
    
    # Version tracking
    rules_version = Column(String(50), nullable=False)  # Version user acknowledged
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    rules = relationship("RulesOfBehavior", back_populates="acknowledgments")
    user = relationship("User", lazy="select")
    
    def __repr__(self):
        return (
            f"<RulesOfBehaviorAcknowledgment(id={self.id}, "
            f"rules_id={self.rules_id}, "
            f"user_id={self.user_id})>"
        )


class RulesOfBehaviorVersion(Base):
    """
    PL-4: Rules of Behavior version history
    """
    __tablename__ = "rules_of_behavior_versions"
    __table_args__ = (
        Index('idx_rob_version_rules', 'rules_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    rules_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules_of_behavior.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    version_number = Column(String(50), nullable=False)
    change_summary = Column(Text, nullable=True)
    changes_made = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    rules = relationship("RulesOfBehavior", back_populates="versions")
    
    def __repr__(self):
        return f"<RulesOfBehaviorVersion(id={self.id}, version_number={self.version_number})>"


# ============================================================================
# PL-7: Security Concept of Operations (CONOPS)
# ============================================================================

class CONOPSStatus(str, Enum):
    """CONOPS document status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SecurityCONOPS(Base):
    """
    PL-7: Security Concept of Operations (CONOPS)
    
    Documents operational security procedures and system architecture.
    """
    __tablename__ = "security_conops"
    __table_args__ = (
        Index('idx_conops_org_status', 'org_id', 'status'),
        Index('idx_conops_active', 'is_active'),
        Index('idx_conops_version', 'version'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Document identification
    title = Column(String(255), nullable=False)
    system_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=CONOPSStatus.DRAFT.value,
        index=True,
    )
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # Content sections
    system_overview = Column(Text, nullable=True)
    operational_environment = Column(Text, nullable=True)
    operational_procedures = Column(Text, nullable=True)
    security_procedures = Column(Text, nullable=True)
    system_architecture = Column(Text, nullable=True)
    architecture_diagram_url = Column(String(1000), nullable=True)
    
    # Full document content
    conops_content = Column(Text, nullable=True)
    conops_document_url = Column(String(1000), nullable=True)  # Generated PDF URL
    
    # Operational procedures
    operational_procedures_list = Column(JSON, nullable=True)  # Structured procedures
    
    # Approval
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
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
            f"<SecurityCONOPS(id={self.id}, "
            f"title={self.title}, "
            f"version={self.version})>"
        )


# ============================================================================
# PL-8: Information Security Architecture
# ============================================================================

class SecurityArchitectureStatus(str, Enum):
    """Security Architecture document status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class InformationSecurityArchitecture(Base):
    """
    PL-8: Information Security Architecture
    
    Documents security architecture, component relationships, and security boundaries.
    """
    __tablename__ = "information_security_architectures"
    __table_args__ = (
        Index('idx_arch_org_status', 'org_id', 'status'),
        Index('idx_arch_active', 'is_active'),
        Index('idx_arch_version', 'version'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Document identification
    title = Column(String(255), nullable=False)
    system_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=SecurityArchitectureStatus.DRAFT.value,
        index=True,
    )
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # Architecture components
    components = Column(JSON, nullable=False, default=list)  # List of architecture components
    component_relationships = Column(JSON, nullable=True)  # Component relationship mapping
    security_boundaries = Column(Text, nullable=True)
    security_boundary_diagram_url = Column(String(1000), nullable=True)
    
    # Architecture diagrams
    architecture_diagram_url = Column(String(1000), nullable=True)
    network_diagram_url = Column(String(1000), nullable=True)
    data_flow_diagram_url = Column(String(1000), nullable=True)
    
    # Security controls mapping
    security_controls = Column(JSON, nullable=True)  # Controls implemented per component
    
    # Full document content
    architecture_content = Column(Text, nullable=True)
    architecture_document_url = Column(String(1000), nullable=True)  # Generated PDF URL
    
    # Approval
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, nullable=False, default=365)
    
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
            f"<InformationSecurityArchitecture(id={self.id}, "
            f"title={self.title}, "
            f"version={self.version})>"
        )
