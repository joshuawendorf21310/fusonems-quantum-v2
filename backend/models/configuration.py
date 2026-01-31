"""
Configuration Management Models for FedRAMP CM-2, CM-3, CM-6 Compliance

FedRAMP Requirements:
- CM-2: Baseline Configurations - Establish and maintain baseline configurations
- CM-3: Configuration Change Control - Track and approve configuration changes
- CM-6: Configuration Settings - Establish and enforce security configuration settings

This module provides database models for:
- Configuration baselines (CM-2)
- Configuration change requests and approvals (CM-3)
- Configuration compliance status tracking (CM-6)
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


class ConfigurationBaselineStatus(str, Enum):
    """Status of a configuration baseline"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class ChangeRequestStatus(str, Enum):
    """Status of a configuration change request"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class ChangeRequestPriority(str, Enum):
    """Priority level for configuration changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ComplianceStatus(str, Enum):
    """Configuration compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"
    EXEMPT = "exempt"


class DriftSeverity(str, Enum):
    """Severity of configuration drift"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfigurationBaseline(Base):
    """
    Configuration baseline records (CM-2).
    
    Stores snapshots of system configuration at specific points in time.
    Baselines serve as reference points for detecting configuration drift.
    """
    __tablename__ = "configuration_baselines"
    __table_args__ = (
        Index('idx_baseline_org_status', 'org_id', 'status'),
        Index('idx_baseline_created', 'created_at'),
        Index('idx_baseline_name', 'name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Baseline identification
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)  # e.g., "1.0", "2.1"
    
    # Baseline status
    status = Column(
        String(50),
        nullable=False,
        default=ConfigurationBaselineStatus.DRAFT.value,
        index=True,
    )
    
    # Configuration snapshot - stores the actual configuration as JSON
    configuration_snapshot = Column(JSON, nullable=False)  # Full configuration state
    
    # Configuration scope - what components are included
    scope = Column(JSON, nullable=True)  # e.g., ["database", "api", "frontend"]
    
    # Metadata
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_email = Column(String(255), nullable=True)  # Denormalized for audit
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Baseline activation
    activated_at = Column(DateTime(timezone=True), nullable=True)
    activated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Archival
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archive_reason = Column(Text, nullable=True)
    
    # Relationships
    change_requests = relationship(
        "ConfigurationChangeRequest",
        back_populates="baseline",
        foreign_keys="ConfigurationChangeRequest.baseline_id",
    )
    compliance_checks = relationship(
        "ConfigurationComplianceStatus",
        back_populates="baseline",
    )
    
    def __repr__(self):
        return (
            f"<ConfigurationBaseline(id={self.id}, "
            f"name={self.name}, "
            f"version={self.version}, "
            f"status={self.status})>"
        )


class ConfigurationChangeRequest(Base):
    """
    Configuration change requests (CM-3).
    
    Tracks all proposed configuration changes with approval workflow.
    """
    __tablename__ = "configuration_change_requests"
    __table_args__ = (
        Index('idx_change_req_org_status', 'org_id', 'status'),
        Index('idx_change_req_baseline', 'baseline_id'),
        Index('idx_change_req_created', 'created_at'),
        Index('idx_change_req_priority', 'priority'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Change request identification
    change_number = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "CHG-2026-001"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Associated baseline
    baseline_id = Column(
        UUID(as_uuid=True),
        ForeignKey("configuration_baselines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Change details
    configuration_changes = Column(JSON, nullable=False)  # What is changing
    affected_components = Column(JSON, nullable=True)  # Which components are affected
    change_reason = Column(Text, nullable=False)  # Why is this change needed
    
    # Change classification
    priority = Column(
        String(50),
        nullable=False,
        default=ChangeRequestPriority.MEDIUM.value,
        index=True,
    )
    risk_level = Column(String(50), nullable=True)  # low, medium, high, critical
    impact_assessment = Column(Text, nullable=True)  # Impact analysis
    
    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default=ChangeRequestStatus.PENDING.value,
        index=True,
    )
    
    # Requestor
    requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    requested_by_email = Column(String(255), nullable=True)  # Denormalized
    
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Implementation tracking
    scheduled_implementation_date = Column(DateTime(timezone=True), nullable=True)
    actual_implementation_date = Column(DateTime(timezone=True), nullable=True)
    implemented_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Rollback tracking
    rollback_date = Column(DateTime(timezone=True), nullable=True)
    rollback_reason = Column(Text, nullable=True)
    rolled_back_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    baseline = relationship(
        "ConfigurationBaseline",
        back_populates="change_requests",
        foreign_keys=[baseline_id],
    )
    approvals = relationship(
        "ConfigurationChangeApproval",
        back_populates="change_request",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return (
            f"<ConfigurationChangeRequest(id={self.id}, "
            f"change_number={self.change_number}, "
            f"status={self.status}, "
            f"priority={self.priority})>"
        )


class ConfigurationChangeApproval(Base):
    """
    Configuration change approvals (CM-3).
    
    Tracks approval workflow for configuration changes.
    Supports multi-level approval workflows.
    """
    __tablename__ = "configuration_change_approvals"
    __table_args__ = (
        Index('idx_approval_change_req', 'change_request_id'),
        Index('idx_approval_approver', 'approver_user_id'),
        Index('idx_approval_status', 'approval_status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Associated change request
    change_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("configuration_change_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Approval level (for multi-level approvals)
    approval_level = Column(Integer, nullable=False, default=1)  # 1 = first level, 2 = second, etc.
    approval_role_required = Column(String(100), nullable=True)  # e.g., "admin", "security_officer"
    
    # Approver
    approver_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approver_email = Column(String(255), nullable=True)  # Denormalized
    
    # Approval decision
    approval_status = Column(String(50), nullable=False)  # approved, rejected, pending
    approval_comment = Column(Text, nullable=True)
    
    # Timestamps
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    change_request = relationship(
        "ConfigurationChangeRequest",
        back_populates="approvals",
    )
    
    def __repr__(self):
        return (
            f"<ConfigurationChangeApproval(id={self.id}, "
            f"change_request_id={self.change_request_id}, "
            f"approval_level={self.approval_level}, "
            f"approval_status={self.approval_status})>"
        )


class ConfigurationComplianceStatus(Base):
    """
    Configuration compliance status tracking (CM-6).
    
    Tracks compliance status of current configuration against baselines
    and security configuration requirements.
    """
    __tablename__ = "configuration_compliance_status"
    __table_args__ = (
        Index('idx_compliance_org_status', 'org_id', 'compliance_status'),
        Index('idx_compliance_baseline', 'baseline_id'),
        Index('idx_compliance_component', 'component_name'),
        Index('idx_compliance_checked', 'last_checked_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Associated baseline (optional - can check against specific baseline)
    baseline_id = Column(
        UUID(as_uuid=True),
        ForeignKey("configuration_baselines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Component being checked
    component_name = Column(String(255), nullable=False, index=True)  # e.g., "database", "api_server"
    component_type = Column(String(100), nullable=True)  # e.g., "service", "database", "infrastructure"
    
    # Compliance status
    compliance_status = Column(
        String(50),
        nullable=False,
        default=ComplianceStatus.UNKNOWN.value,
        index=True,
    )
    
    # Current configuration
    current_configuration = Column(JSON, nullable=True)  # Current state
    expected_configuration = Column(JSON, nullable=True)  # Expected/baseline state
    
    # Drift detection
    has_drift = Column(Boolean, default=False, nullable=False, index=True)
    drift_details = Column(JSON, nullable=True)  # Details of configuration drift
    drift_severity = Column(String(50), nullable=True)  # low, medium, high, critical
    
    # Compliance check details
    compliance_rules_checked = Column(JSON, nullable=True)  # Which rules were checked
    compliance_violations = Column(JSON, nullable=True)  # List of violations found
    remediation_suggestions = Column(JSON, nullable=True)  # Suggested fixes
    
    # Check metadata
    last_checked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    checked_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    check_method = Column(String(100), nullable=True)  # "automated", "manual", "scheduled"
    
    # Next check
    next_check_due_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    baseline = relationship(
        "ConfigurationBaseline",
        back_populates="compliance_checks",
    )
    
    def __repr__(self):
        return (
            f"<ConfigurationComplianceStatus(id={self.id}, "
            f"component_name={self.component_name}, "
            f"compliance_status={self.compliance_status}, "
            f"has_drift={self.has_drift})>"
        )
