"""
Maintenance Models for FedRAMP MA-2 through MA-6 Compliance

FedRAMP Requirements:
- MA-2: Controlled Maintenance - Control maintenance activities
- MA-3: Maintenance Tools - Control maintenance tools
- MA-4: Nonlocal Maintenance - Control remote maintenance
- MA-5: Maintenance Personnel - Control maintenance personnel
- MA-6: Timely Maintenance - Ensure timely maintenance

This module provides database models for all Maintenance controls.
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
# ENUMS
# ============================================================================

class MaintenanceStatus(str, Enum):
    """Maintenance status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    DEFERRED = "deferred"


class MaintenanceType(str, Enum):
    """Maintenance types"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    UPGRADE = "upgrade"
    PATCH = "patch"
    ROUTINE = "routine"


class MaintenancePriority(str, Enum):
    """Maintenance priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ApprovalStatus(str, Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class ToolStatus(str, Enum):
    """Tool status"""
    APPROVED = "approved"
    PENDING_APPROVAL = "pending_approval"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RemoteMaintenanceStatus(str, Enum):
    """Remote maintenance session status"""
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    COMPLETED = "completed"


class PersonnelAuthorizationStatus(str, Enum):
    """Personnel authorization status"""
    AUTHORIZED = "authorized"
    PENDING = "pending"
    REVOKED = "revoked"
    EXPIRED = "expired"


class EscortRequired(str, Enum):
    """Escort requirement"""
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    CONDITIONAL = "conditional"


class SLAStatus(str, Enum):
    """SLA compliance status"""
    ON_TIME = "on_time"
    AT_RISK = "at_risk"
    OVERDUE = "overdue"
    COMPLETED = "completed"


# ============================================================================
# MA-2: CONTROLLED MAINTENANCE
# ============================================================================

class ControlledMaintenance(Base):
    """
    Controlled maintenance records (MA-2).
    
    Tracks maintenance scheduling, approval workflow, and logging.
    """
    __tablename__ = "controlled_maintenance"
    __table_args__ = (
        Index('idx_controlled_maint_org_status', 'org_id', 'maintenance_status'),
        Index('idx_controlled_maint_type', 'maintenance_type'),
        Index('idx_controlled_maint_dates', 'scheduled_start_date', 'scheduled_end_date'),
        Index('idx_controlled_maint_priority', 'priority'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Maintenance identification
    maintenance_number = Column(String(100), nullable=False, unique=True, index=True)  # e.g., "MAINT-2026-001"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Maintenance classification
    maintenance_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    priority = Column(
        String(50),
        nullable=False,
        default=MaintenancePriority.MEDIUM.value,
        index=True,
    )
    
    # System/component being maintained
    system_name = Column(String(255), nullable=False)
    component_name = Column(String(255), nullable=True)
    component_type = Column(String(100), nullable=True)  # server, network, application, etc.
    
    # Scheduling
    scheduled_start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    maintenance_status = Column(
        String(50),
        nullable=False,
        default=MaintenanceStatus.SCHEDULED.value,
        index=True,
    )
    
    # Approval workflow
    approval_required = Column(Boolean, default=True, nullable=False)
    approval_status = Column(
        String(50),
        nullable=True,
        default=ApprovalStatus.PENDING.value,
    )
    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_comment = Column(Text, nullable=True)
    
    # Requestor
    requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    requested_by_email = Column(String(255), nullable=True)  # Denormalized
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Maintenance personnel
    assigned_personnel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_personnel.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Impact assessment
    impact_assessment = Column(Text, nullable=True)
    downtime_expected = Column(Boolean, default=False, nullable=False)
    downtime_duration_minutes = Column(Integer, nullable=True)
    
    # Maintenance log
    maintenance_log = Column(JSON, nullable=True)  # Array of log entries
    maintenance_notes = Column(Text, nullable=True)
    
    # Completion
    completed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completion_notes = Column(Text, nullable=True)
    
    # Relationships
    personnel = relationship("MaintenancePersonnel", back_populates="maintenance_records")
    tool_usage = relationship("MaintenanceToolUsage", back_populates="maintenance")
    
    def __repr__(self):
        return (
            f"<ControlledMaintenance(id={self.id}, "
            f"maintenance_number={self.maintenance_number}, "
            f"maintenance_status={self.maintenance_status})>"
        )


# ============================================================================
# MA-3: MAINTENANCE TOOLS
# ============================================================================

class MaintenanceTool(Base):
    """
    Maintenance tool inventory (MA-3).
    
    Tracks maintenance tools, authorization, and usage.
    """
    __tablename__ = "maintenance_tools"
    __table_args__ = (
        Index('idx_maint_tool_org_status', 'org_id', 'tool_status'),
        Index('idx_maint_tool_name', 'tool_name'),
        Index('idx_maint_tool_type', 'tool_type'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Tool identification
    tool_name = Column(String(255), nullable=False, index=True)
    tool_type = Column(String(100), nullable=False, index=True)  # software, hardware, diagnostic, etc.
    tool_version = Column(String(100), nullable=True)
    tool_manufacturer = Column(String(255), nullable=True)
    tool_serial_number = Column(String(255), nullable=True, unique=True)
    
    # Tool description
    tool_description = Column(Text, nullable=True)
    tool_capabilities = Column(JSON, nullable=True)  # What the tool can do
    
    # Authorization
    tool_status = Column(
        String(50),
        nullable=False,
        default=ToolStatus.PENDING_APPROVAL.value,
        index=True,
    )
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    authorization_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security considerations
    security_risks = Column(JSON, nullable=True)  # Known security risks
    security_mitigations = Column(Text, nullable=True)  # How risks are mitigated
    requires_approval = Column(Boolean, default=True, nullable=False)
    
    # Usage restrictions
    usage_restrictions = Column(Text, nullable=True)
    allowed_systems = Column(JSON, nullable=True)  # Systems where tool can be used
    restricted_systems = Column(JSON, nullable=True)  # Systems where tool cannot be used
    
    # Inventory
    location = Column(String(255), nullable=True)
    assigned_to_personnel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_personnel.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    usage_records = relationship("MaintenanceToolUsage", back_populates="tool")
    
    def __repr__(self):
        return (
            f"<MaintenanceTool(id={self.id}, "
            f"tool_name={self.tool_name}, "
            f"tool_status={self.tool_status})>"
        )


class MaintenanceToolUsage(Base):
    """
    Maintenance tool usage records (MA-3).
    
    Tracks when and how maintenance tools are used.
    """
    __tablename__ = "maintenance_tool_usage"
    __table_args__ = (
        Index('idx_tool_usage_tool', 'tool_id'),
        Index('idx_tool_usage_maint', 'maintenance_id'),
        Index('idx_tool_usage_dates', 'usage_start_date', 'usage_end_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Tool reference
    tool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Maintenance reference
    maintenance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("controlled_maintenance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Usage details
    usage_purpose = Column(Text, nullable=False)
    system_used_on = Column(String(255), nullable=False)
    
    # Personnel
    used_by_personnel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_personnel.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Dates
    usage_start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    usage_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Results
    usage_results = Column(Text, nullable=True)
    issues_encountered = Column(Text, nullable=True)
    
    # Relationships
    tool = relationship("MaintenanceTool", back_populates="usage_records")
    maintenance = relationship("ControlledMaintenance", back_populates="tool_usage")
    
    def __repr__(self):
        return (
            f"<MaintenanceToolUsage(id={self.id}, "
            f"tool_id={self.tool_id}, "
            f"maintenance_id={self.maintenance_id})>"
        )


# ============================================================================
# MA-4: NONLOCAL MAINTENANCE
# ============================================================================

class NonlocalMaintenance(Base):
    """
    Nonlocal (remote) maintenance records (MA-4).
    
    Tracks remote maintenance authorization, session monitoring, and access controls.
    """
    __tablename__ = "nonlocal_maintenance"
    __table_args__ = (
        Index('idx_nonlocal_maint_org_status', 'org_id', 'session_status'),
        Index('idx_nonlocal_maint_personnel', 'personnel_id'),
        Index('idx_nonlocal_maint_dates', 'session_start_date', 'session_end_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Session identification
    session_number = Column(String(100), nullable=False, unique=True, index=True)  # e.g., "REMOTE-2026-001"
    session_purpose = Column(Text, nullable=False)
    
    # Maintenance reference
    maintenance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("controlled_maintenance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # System being maintained
    system_name = Column(String(255), nullable=False)
    system_ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    system_hostname = Column(String(255), nullable=True)
    
    # Personnel
    personnel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_personnel.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    
    # Authorization
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    authorized_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    authorization_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access method
    access_method = Column(String(100), nullable=False)  # SSH, RDP, VPN, etc.
    access_protocol = Column(String(50), nullable=True)  # TLS, IPsec, etc.
    encryption_required = Column(Boolean, default=True, nullable=False)
    encryption_method = Column(String(100), nullable=True)
    
    # Session details
    session_status = Column(
        String(50),
        nullable=False,
        default=RemoteMaintenanceStatus.ACTIVE.value,
        index=True,
    )
    session_start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    session_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Monitoring
    session_monitored = Column(Boolean, default=True, nullable=False)
    session_log_path = Column(String(500), nullable=True)  # Path to session log
    session_recording_path = Column(String(500), nullable=True)  # Path to session recording
    
    # Access controls
    allowed_commands = Column(JSON, nullable=True)  # Commands allowed during session
    restricted_commands = Column(JSON, nullable=True)  # Commands restricted
    allowed_files = Column(JSON, nullable=True)  # Files that can be accessed
    restricted_files = Column(JSON, nullable=True)  # Files that cannot be accessed
    
    # Termination
    terminated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    termination_reason = Column(Text, nullable=True)
    
    # Relationships
    personnel = relationship("MaintenancePersonnel", back_populates="remote_sessions")
    
    def __repr__(self):
        return (
            f"<NonlocalMaintenance(id={self.id}, "
            f"session_number={self.session_number}, "
            f"session_status={self.session_status})>"
        )


# ============================================================================
# MA-5: MAINTENANCE PERSONNEL
# ============================================================================

class MaintenancePersonnel(Base):
    """
    Maintenance personnel records (MA-5).
    
    Tracks personnel authorization, escort requirements, and activity logging.
    """
    __tablename__ = "maintenance_personnel"
    __table_args__ = (
        Index('idx_maint_personnel_org_status', 'org_id', 'authorization_status'),
        Index('idx_maint_personnel_name', 'personnel_name'),
        Index('idx_maint_personnel_company', 'company_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Personnel identification
    personnel_name = Column(String(255), nullable=False, index=True)
    personnel_email = Column(String(255), nullable=True)
    personnel_phone = Column(String(50), nullable=True)
    
    # Company/affiliation
    company_name = Column(String(255), nullable=True, index=True)
    company_contact = Column(String(255), nullable=True)
    company_phone = Column(String(50), nullable=True)
    
    # Authorization
    authorization_status = Column(
        String(50),
        nullable=False,
        default=PersonnelAuthorizationStatus.PENDING.value,
        index=True,
    )
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    authorization_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Background checks
    background_check_completed = Column(Boolean, default=False, nullable=False)
    background_check_date = Column(DateTime(timezone=True), nullable=True)
    background_check_results = Column(Text, nullable=True)
    
    # Access level
    access_level = Column(String(50), nullable=True)  # read-only, read-write, full, etc.
    allowed_systems = Column(JSON, nullable=True)  # Systems personnel can access
    restricted_systems = Column(JSON, nullable=True)  # Systems personnel cannot access
    
    # Escort requirements
    escort_required = Column(
        String(50),
        nullable=False,
        default=EscortRequired.REQUIRED.value,
    )
    escort_personnel_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Activity logging
    activity_logged = Column(Boolean, default=True, nullable=False)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Relationships
    maintenance_records = relationship("ControlledMaintenance", back_populates="personnel")
    remote_sessions = relationship("NonlocalMaintenance", back_populates="personnel")
    
    def __repr__(self):
        return (
            f"<MaintenancePersonnel(id={self.id}, "
            f"personnel_name={self.personnel_name}, "
            f"authorization_status={self.authorization_status})>"
        )


# ============================================================================
# MA-6: TIMELY MAINTENANCE
# ============================================================================

class TimelyMaintenance(Base):
    """
    Timely maintenance records (MA-6).
    
    Tracks maintenance SLAs, preventive maintenance scheduling, and compliance.
    """
    __tablename__ = "timely_maintenance"
    __table_args__ = (
        Index('idx_timely_maint_org_system', 'org_id', 'system_name'),
        Index('idx_timely_maint_sla_status', 'sla_status'),
        Index('idx_timely_maint_due_date', 'maintenance_due_date'),
        Index('idx_timely_maint_type', 'maintenance_type'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # System/component
    system_name = Column(String(255), nullable=False, index=True)
    component_name = Column(String(255), nullable=True)
    component_type = Column(String(100), nullable=True)
    
    # Maintenance type
    maintenance_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # SLA tracking
    sla_hours = Column(Integer, nullable=False)  # Hours within which maintenance must be completed
    maintenance_due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    maintenance_completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # SLA compliance
    sla_status = Column(
        String(50),
        nullable=True,
        index=True,
    )
    sla_met = Column(Boolean, nullable=True)  # True if completed within SLA
    sla_variance_hours = Column(Integer, nullable=True)  # Hours early/late
    
    # Preventive maintenance schedule
    preventive_schedule_days = Column(Integer, nullable=True)  # Days between preventive maintenance
    last_preventive_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_preventive_maintenance_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Maintenance reference
    maintenance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("controlled_maintenance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Compliance tracking
    compliance_status = Column(String(50), nullable=True)  # compliant, non_compliant, at_risk
    compliance_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return (
            f"<TimelyMaintenance(id={self.id}, "
            f"system_name={self.system_name}, "
            f"sla_status={self.sla_status})>"
        )
