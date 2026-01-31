"""
Configuration Management Control Models for FedRAMP CM-4, CM-7, CM-8, CM-9, CM-10, CM-11 Compliance

FedRAMP Requirements:
- CM-4: Security Impact Analysis
- CM-7: Least Functionality
- CM-8: Component Inventory
- CM-9: Configuration Management Plan
- CM-10: Software Usage Restrictions
- CM-11: User-Installed Software
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

from core.database import Base


class ImpactLevel(str, Enum):
    """Security impact level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class ComponentType(str, Enum):
    """Type of system component"""
    SOFTWARE = "software"
    HARDWARE = "hardware"
    NETWORK = "network"
    SERVICE = "service"
    DATABASE = "database"
    APPLICATION = "application"


class ComponentStatus(str, Enum):
    """Status of component"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class SecurityImpactAnalysis(Base):
    """
    Security impact analysis records (CM-4).
    
    Tracks security impact assessments for configuration changes.
    """
    __tablename__ = "security_impact_analyses"
    __table_args__ = (
        Index('idx_impact_analysis_change', 'change_request_id'),
        Index('idx_impact_analysis_org', 'org_id'),
        Index('idx_impact_analysis_status', 'approval_status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Associated change request
    change_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("configuration_change_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Impact assessment
    impact_level = Column(
        String(50),
        nullable=False,
        index=True,
    )
    impact_description = Column(Text, nullable=False)
    affected_components = Column(JSON, nullable=True)  # List of affected components
    security_risks = Column(JSON, nullable=True)  # Identified security risks
    mitigation_measures = Column(JSON, nullable=True)  # Mitigation measures
    
    # Testing requirements
    security_test_required = Column(Boolean, default=False, nullable=False)
    security_test_requirements = Column(JSON, nullable=True)  # Required security tests
    security_test_results = Column(JSON, nullable=True)  # Test results
    
    # Approval
    approval_status = Column(
        String(50),
        nullable=False,
        default=ApprovalStatus.PENDING.value,
        index=True,
    )
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Created by
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<SecurityImpactAnalysis(id={self.id}, "
            f"impact_level={self.impact_level}, "
            f"approval_status={self.approval_status})>"
        )


class SystemComponent(Base):
    """
    System component inventory records (CM-8).
    
    Tracks all system components (software, hardware, services).
    """
    __tablename__ = "system_components"
    __table_args__ = (
        Index('idx_component_org_type', 'org_id', 'component_type'),
        Index('idx_component_name', 'component_name'),
        Index('idx_component_status', 'status'),
        Index('idx_component_version', 'version'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Component identification
    component_name = Column(String(255), nullable=False, index=True)
    component_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    version = Column(String(100), nullable=True, index=True)
    vendor = Column(String(255), nullable=True)
    
    # Component details
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)  # Physical or logical location
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=ComponentStatus.ACTIVE.value,
        index=True,
    )
    
    # Discovery
    discovered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    discovery_method = Column(String(100), nullable=True)  # automated, manual
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True)  # Component configuration
    dependencies = Column(JSON, nullable=True)  # Dependencies on other components
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<SystemComponent(id={self.id}, "
            f"component_name={self.component_name}, "
            f"component_type={self.component_type}, "
            f"status={self.status})>"
        )


class ServiceInventory(Base):
    """
    Service inventory records (CM-7).
    
    Tracks system services and their status for least functionality.
    """
    __tablename__ = "service_inventory"
    __table_args__ = (
        Index('idx_service_org', 'org_id'),
        Index('idx_service_name', 'service_name'),
        Index('idx_service_status', 'is_enabled'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Service identification
    service_name = Column(String(255), nullable=False, index=True)
    service_type = Column(String(100), nullable=False)  # system_service, application_service, etc.
    description = Column(Text, nullable=True)
    
    # Service status
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    is_required = Column(Boolean, default=False, nullable=False)  # Required for operation
    is_unnecessary = Column(Boolean, default=False, nullable=False, index=True)  # Unnecessary service
    
    # Ports and protocols
    ports = Column(JSON, nullable=True)  # List of ports used
    protocols = Column(JSON, nullable=True)  # List of protocols used
    
    # Restrictions
    port_restrictions = Column(JSON, nullable=True)  # Port restrictions
    protocol_restrictions = Column(JSON, nullable=True)  # Protocol restrictions
    
    # Discovery
    discovered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<ServiceInventory(id={self.id}, "
            f"service_name={self.service_name}, "
            f"is_enabled={self.is_enabled}, "
            f"is_unnecessary={self.is_unnecessary})>"
        )


class ConfigurationManagementPlan(Base):
    """
    Configuration management plan records (CM-9).
    
    Stores and tracks configuration management plans.
    """
    __tablename__ = "configuration_management_plans"
    __table_args__ = (
        Index('idx_cm_plan_org', 'org_id'),
        Index('idx_cm_plan_status', 'status'),
        Index('idx_cm_plan_version', 'version'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Plan identification
    plan_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Plan content
    plan_content = Column(JSON, nullable=False)  # Full plan content
    plan_document = Column(Text, nullable=True)  # Plan document (markdown/text)
    
    # Status
    status = Column(String(50), nullable=False, default="draft")  # draft, active, superseded
    
    # Approval
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Created by
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<ConfigurationManagementPlan(id={self.id}, "
            f"plan_name={self.plan_name}, "
            f"version={self.version}, "
            f"status={self.status})>"
        )


class SoftwareLicense(Base):
    """
    Software license records (CM-10).
    
    Tracks software licenses and usage restrictions.
    """
    __tablename__ = "software_licenses"
    __table_args__ = (
        Index('idx_license_org', 'org_id'),
        Index('idx_license_software', 'software_name'),
        Index('idx_license_status', 'license_status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Software identification
    software_name = Column(String(255), nullable=False, index=True)
    software_version = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)
    
    # License details
    license_type = Column(String(100), nullable=False)  # commercial, open_source, freeware, etc.
    license_key = Column(String(500), nullable=True)  # License key (encrypted)
    license_agreement = Column(Text, nullable=True)  # License agreement text
    
    # Usage restrictions
    max_installations = Column(Integer, nullable=True)  # Maximum allowed installations
    current_installations = Column(Integer, default=0, nullable=False)
    usage_restrictions = Column(JSON, nullable=True)  # Usage restrictions
    
    # License status
    license_status = Column(String(50), nullable=False, default="active")  # active, expired, revoked
    is_compliant = Column(Boolean, default=True, nullable=False, index=True)
    
    # Validity
    issued_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Monitoring
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    usage_monitored = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<SoftwareLicense(id={self.id}, "
            f"software_name={self.software_name}, "
            f"license_status={self.license_status}, "
            f"is_compliant={self.is_compliant})>"
        )


class UserInstalledSoftware(Base):
    """
    User-installed software records (CM-11).
    
    Tracks software installed by users and approval workflow.
    """
    __tablename__ = "user_installed_software"
    __table_args__ = (
        Index('idx_user_software_user', 'user_id', 'org_id'),
        Index('idx_user_software_status', 'approval_status'),
        Index('idx_user_software_installed', 'installed_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization and user
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Software identification
    software_name = Column(String(255), nullable=False)
    software_version = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)
    installation_path = Column(String(1000), nullable=True)
    
    # Installation details
    installed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    installation_method = Column(String(100), nullable=True)  # manual, package_manager, etc.
    installation_reason = Column(Text, nullable=True)  # Why user installed it
    
    # Approval workflow
    approval_status = Column(
        String(50),
        nullable=False,
        default=ApprovalStatus.PENDING.value,
        index=True,
    )
    approval_required = Column(Boolean, default=True, nullable=False)
    
    # Approval details
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Rejection
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason = Column(Text, nullable=True)
    
    # Detection
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    detection_method = Column(String(100), nullable=True)  # automated_scan, manual_report, etc.
    
    # Removal
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    removal_reason = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<UserInstalledSoftware(id={self.id}, "
            f"software_name={self.software_name}, "
            f"user_id={self.user_id}, "
            f"approval_status={self.approval_status})>"
        )
