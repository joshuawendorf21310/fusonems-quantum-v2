"""
Access Control Models for FedRAMP AC Controls

This module contains models for:
- AC-4: Information Flow Enforcement
- AC-6: Least Privilege
- AC-17: Remote Access
- AC-18: Wireless Access
- AC-19: Mobile Device Access
- AC-20: Use of External Systems
- AC-22: Publicly Accessible Content
"""
from datetime import datetime
from enum import Enum as PyEnum
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
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


# ============================================================================
# AC-4: Information Flow Enforcement
# ============================================================================

class FlowDirection(str, PyEnum):
    """Direction of information flow"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class FlowAction(str, PyEnum):
    """Action taken on information flow"""
    ALLOW = "allow"
    DENY = "deny"
    ENCRYPT = "encrypt"
    LOG = "log"
    QUARANTINE = "quarantine"


class NetworkSegment(str, PyEnum):
    """Network segmentation zones"""
    DMZ = "dmz"
    INTERNAL = "internal"
    EXTERNAL = "external"
    MANAGEMENT = "management"
    DATABASE = "database"
    APPLICATION = "application"


class InformationFlowRule(Base):
    """
    AC-4: Information Flow Enforcement Rules
    
    Defines rules for controlling information flow between network segments,
    systems, and data classifications.
    """
    __tablename__ = "information_flow_rules"
    __table_args__ = (
        Index('idx_flow_rule_org', 'org_id'),
        Index('idx_flow_rule_source', 'source_segment'),
        Index('idx_flow_rule_dest', 'destination_segment'),
        Index('idx_flow_rule_active', 'is_active'),
        Index('idx_flow_rule_priority', 'priority'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rule identification
    rule_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False)  # Lower = higher priority
    
    # Flow definition
    source_segment = Column(String(50), nullable=False)  # NetworkSegment
    destination_segment = Column(String(50), nullable=False)  # NetworkSegment
    direction = Column(String(20), nullable=False)  # FlowDirection
    protocol = Column(String(50), nullable=True)  # tcp, udp, http, https, etc.
    port_range = Column(String(50), nullable=True)  # e.g., "80,443" or "8000-9000"
    
    # Data classification
    data_classification = Column(String(50), nullable=True)  # PHI, PII, PUBLIC, INTERNAL
    requires_encryption = Column(Boolean, default=False, nullable=False)
    requires_authentication = Column(Boolean, default=True, nullable=False)
    
    # Action
    action = Column(String(20), nullable=False)  # FlowAction
    action_parameters = Column(JSON, nullable=True)  # Additional action config
    
    # Conditions
    conditions = Column(JSON, nullable=True)  # Additional conditions (time-based, user-based, etc.)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    flow_logs = relationship("InformationFlowLog", back_populates="rule")


class InformationFlowLog(Base):
    """
    AC-4: Information Flow Log
    
    Logs all information flow events for audit and monitoring.
    """
    __tablename__ = "information_flow_logs"
    __table_args__ = (
        Index('idx_flow_log_timestamp', 'timestamp'),
        Index('idx_flow_log_rule', 'rule_id'),
        Index('idx_flow_log_org', 'org_id'),
        Index('idx_flow_log_action', 'action_taken'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("information_flow_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Flow details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    source_segment = Column(String(50), nullable=False)
    destination_segment = Column(String(50), nullable=False)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    protocol = Column(String(50), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Action taken
    action_taken = Column(String(20), nullable=False)  # FlowAction
    action_result = Column(String(50), nullable=False)  # allowed, denied, encrypted, etc.
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    data_size = Column(Integer, nullable=True)  # bytes
    data_classification = Column(String(50), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    rule = relationship("InformationFlowRule", back_populates="flow_logs")


# ============================================================================
# AC-6: Least Privilege
# ============================================================================

class PrivilegeReviewStatus(str, PyEnum):
    """Status of privilege review"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PrivilegeAssignment(Base):
    """
    AC-6: Least Privilege Assignment
    
    Tracks user privilege assignments and ensures least privilege principle.
    """
    __tablename__ = "privilege_assignments"
    __table_args__ = (
        Index('idx_priv_user', 'user_id'),
        Index('idx_priv_org', 'org_id'),
        Index('idx_priv_status', 'status'),
        Index('idx_priv_expires', 'expires_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Privilege details
    privilege_name = Column(String(255), nullable=False)
    privilege_type = Column(String(50), nullable=False)  # role, permission, capability, etc.
    resource_type = Column(String(100), nullable=True)  # system, module, data, etc.
    resource_id = Column(String(255), nullable=True)
    
    # Justification
    justification = Column(Text, nullable=False)
    business_need = Column(Text, nullable=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=PrivilegeReviewStatus.PENDING.value)  # PrivilegeReviewStatus
    granted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=90, nullable=False)  # Default 90 days
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    escalations = relationship("PrivilegeEscalation", back_populates="privilege")


class PrivilegeEscalation(Base):
    """
    AC-6: Privilege Escalation Tracking
    
    Tracks temporary privilege escalations for specific tasks.
    """
    __tablename__ = "privilege_escalations"
    __table_args__ = (
        Index('idx_escalation_user', 'user_id'),
        Index('idx_escalation_org', 'org_id'),
        Index('idx_escalation_active', 'is_active'),
        Index('idx_escalation_expires', 'expires_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    privilege_id = Column(Integer, ForeignKey("privilege_assignments.id", ondelete="SET NULL"), nullable=True)
    
    # Escalation details
    escalated_privilege = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    task_description = Column(Text, nullable=True)
    
    # Time limits
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Approval
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    privilege = relationship("PrivilegeAssignment", back_populates="escalations")


# ============================================================================
# AC-17: Remote Access
# ============================================================================

class RemoteAccessMethod(str, PyEnum):
    """Remote access methods"""
    VPN = "vpn"
    RDP = "rdp"
    SSH = "ssh"
    HTTPS = "https"
    CITRIX = "citrix"
    VDI = "vdi"


class RemoteAccessStatus(str, PyEnum):
    """Remote access session status"""
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RemoteAccessPolicy(Base):
    """
    AC-17: Remote Access Policy
    
    Defines policies for remote access including VPN requirements,
    geographic restrictions, and access controls.
    """
    __tablename__ = "remote_access_policies"
    __table_args__ = (
        Index('idx_remote_policy_org', 'org_id'),
        Index('idx_remote_policy_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Policy details
    policy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Access method requirements
    allowed_methods = Column(JSON, nullable=False)  # List of RemoteAccessMethod
    requires_vpn = Column(Boolean, default=True, nullable=False)
    requires_mfa = Column(Boolean, default=True, nullable=False)
    
    # Geographic restrictions
    allowed_countries = Column(JSON, nullable=True)  # ISO country codes
    allowed_regions = Column(JSON, nullable=True)  # Geographic regions
    blocked_ips = Column(JSON, nullable=True)  # Blocked IP ranges
    
    # Time restrictions
    allowed_hours = Column(JSON, nullable=True)  # e.g., {"start": "08:00", "end": "18:00", "timezone": "UTC"}
    allowed_days = Column(JSON, nullable=True)  # Days of week
    
    # Session controls
    max_session_duration_minutes = Column(Integer, default=480, nullable=False)  # 8 hours default
    idle_timeout_minutes = Column(Integer, default=30, nullable=False)
    max_concurrent_sessions = Column(Integer, default=3, nullable=False)
    
    # Device requirements
    requires_trusted_device = Column(Boolean, default=False, nullable=False)
    requires_device_encryption = Column(Boolean, default=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RemoteAccessSession(Base):
    """
    AC-17: Remote Access Session
    
    Tracks all remote access sessions for monitoring and audit.
    """
    __tablename__ = "remote_access_sessions"
    __table_args__ = (
        Index('idx_remote_session_user', 'user_id'),
        Index('idx_remote_session_org', 'org_id'),
        Index('idx_remote_session_status', 'status'),
        Index('idx_remote_session_start', 'started_at'),
        Index('idx_remote_session_ip', 'client_ip'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(Integer, ForeignKey("remote_access_policies.id", ondelete="SET NULL"), nullable=True)
    
    # Session details
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    access_method = Column(String(50), nullable=False)  # RemoteAccessMethod
    status = Column(String(20), nullable=False, default=RemoteAccessStatus.ACTIVE.value)  # RemoteAccessStatus
    
    # Connection info
    client_ip = Column(String(45), nullable=False, index=True)
    client_location = Column(JSON, nullable=True)  # Country, region, city
    user_agent = Column(Text, nullable=True)
    device_id = Column(String(255), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # VPN info (if applicable)
    vpn_connection_id = Column(String(255), nullable=True)
    vpn_server = Column(String(255), nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Activity tracking
    bytes_sent = Column(Integer, default=0, nullable=False)
    bytes_received = Column(Integer, default=0, nullable=False)
    actions_performed = Column(JSON, nullable=True)  # List of actions
    
    # Termination
    termination_reason = Column(String(255), nullable=True)
    terminated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)


# ============================================================================
# AC-18: Wireless Access
# ============================================================================

class WirelessSecurityStandard(str, PyEnum):
    """Wireless security standards"""
    WPA3 = "wpa3"
    WPA2 = "wpa2"
    WPA = "wpa"
    WEP = "wep"  # Not recommended


class WirelessDeviceStatus(str, PyEnum):
    """Wireless device status"""
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class WirelessNetworkPolicy(Base):
    """
    AC-18: Wireless Network Policy
    
    Defines policies for wireless network access including encryption
    requirements and device authentication.
    """
    __tablename__ = "wireless_network_policies"
    __table_args__ = (
        Index('idx_wireless_policy_org', 'org_id'),
        Index('idx_wireless_policy_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Policy details
    policy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ssid = Column(String(255), nullable=True)  # Network SSID
    
    # Security requirements
    minimum_security_standard = Column(String(20), nullable=False, default=WirelessSecurityStandard.WPA2.value)
    requires_encryption = Column(Boolean, default=True, nullable=False)
    requires_authentication = Column(Boolean, default=True, nullable=False)
    requires_certificate = Column(Boolean, default=False, nullable=False)
    
    # Device requirements
    requires_device_registration = Column(Boolean, default=True, nullable=False)
    allowed_device_types = Column(JSON, nullable=True)  # laptop, mobile, iot, etc.
    
    # Network isolation
    network_segment = Column(String(50), nullable=True)  # guest, internal, management
    allows_internet_access = Column(Boolean, default=False, nullable=False)
    allows_internal_access = Column(Boolean, default=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WirelessDevice(Base):
    """
    AC-18: Wireless Device Registration
    
    Tracks registered wireless devices and their compliance status.
    """
    __tablename__ = "wireless_devices"
    __table_args__ = (
        Index('idx_wireless_device_mac', 'mac_address'),
        Index('idx_wireless_device_org', 'org_id'),
        Index('idx_wireless_device_status', 'status'),
        Index('idx_wireless_device_user', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(Integer, ForeignKey("wireless_network_policies.id", ondelete="SET NULL"), nullable=True)
    
    # Device identification
    device_name = Column(String(255), nullable=False)
    mac_address = Column(String(17), nullable=False, unique=True, index=True)  # Format: XX:XX:XX:XX:XX:XX
    device_type = Column(String(50), nullable=False)  # laptop, mobile, tablet, iot, etc.
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    
    # Security
    encryption_support = Column(JSON, nullable=True)  # Supported encryption standards
    certificate_installed = Column(Boolean, default=False, nullable=False)
    certificate_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=WirelessDeviceStatus.REGISTERED.value)
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Registration
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WirelessConnectionLog(Base):
    """
    AC-18: Wireless Connection Log
    
    Logs all wireless network connections for audit and monitoring.
    """
    __tablename__ = "wireless_connection_logs"
    __table_args__ = (
        Index('idx_wireless_log_timestamp', 'timestamp'),
        Index('idx_wireless_log_device', 'device_id'),
        Index('idx_wireless_log_org', 'org_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("wireless_devices.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(Integer, ForeignKey("wireless_network_policies.id", ondelete="SET NULL"), nullable=True)
    
    # Connection details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    ssid = Column(String(255), nullable=True)
    mac_address = Column(String(17), nullable=False)
    ip_address = Column(String(45), nullable=True)
    
    # Security
    security_standard_used = Column(String(20), nullable=True)
    encryption_enabled = Column(Boolean, nullable=True)
    authentication_method = Column(String(50), nullable=True)
    
    # Connection status
    connected = Column(Boolean, nullable=False)
    connection_duration_seconds = Column(Integer, nullable=True)
    bytes_sent = Column(Integer, default=0, nullable=False)
    bytes_received = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)


# ============================================================================
# AC-19: Mobile Device Access
# ============================================================================

class MobileDeviceType(str, PyEnum):
    """Mobile device types"""
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    LAPTOP = "laptop"
    WEARABLE = "wearable"


class MobileDeviceComplianceStatus(str, PyEnum):
    """Mobile device compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    EXEMPT = "exempt"


class MobileDevice(Base):
    """
    AC-19: Mobile Device Registration
    
    Tracks mobile devices and their compliance with security policies.
    """
    __tablename__ = "mobile_devices"
    __table_args__ = (
        Index('idx_mobile_device_org', 'org_id'),
        Index('idx_mobile_device_user', 'user_id'),
        Index('idx_mobile_device_imei', 'imei'),
        Index('idx_mobile_device_status', 'compliance_status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Device identification
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(20), nullable=False)  # MobileDeviceType
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    imei = Column(String(15), nullable=True, unique=True, index=True)  # International Mobile Equipment Identity
    serial_number = Column(String(255), nullable=True, unique=True, index=True)
    os_type = Column(String(50), nullable=False)  # iOS, Android, Windows, etc.
    os_version = Column(String(50), nullable=True)
    
    # MDM integration
    mdm_enrolled = Column(Boolean, default=False, nullable=False)
    mdm_device_id = Column(String(255), nullable=True)
    mdm_managed = Column(Boolean, default=False, nullable=False)
    mdm_last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Compliance
    compliance_status = Column(String(20), nullable=False, default=MobileDeviceComplianceStatus.PENDING.value)
    last_compliance_check = Column(DateTime(timezone=True), nullable=True)
    compliance_issues = Column(JSON, nullable=True)  # List of compliance violations
    
    # Security features
    encryption_enabled = Column(Boolean, nullable=True)
    screen_lock_enabled = Column(Boolean, nullable=True)
    biometric_enabled = Column(Boolean, nullable=True)
    remote_wipe_capable = Column(Boolean, default=True, nullable=False)
    jailbroken_rooted = Column(Boolean, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Registration
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    access_logs = relationship("MobileDeviceAccessLog", back_populates="device")
    wipe_operations = relationship("MobileDeviceWipe", back_populates="device")


class MobileDeviceAccessLog(Base):
    """
    AC-19: Mobile Device Access Log
    
    Logs access attempts and activities from mobile devices.
    """
    __tablename__ = "mobile_device_access_logs"
    __table_args__ = (
        Index('idx_mobile_log_timestamp', 'timestamp'),
        Index('idx_mobile_log_device', 'device_id'),
        Index('idx_mobile_log_org', 'org_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Access details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    action = Column(String(100), nullable=False)  # login, data_access, api_call, etc.
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    # Connection info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)  # GPS coordinates, city, etc.
    
    # Result
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("MobileDevice", back_populates="access_logs")


class MobileDeviceWipe(Base):
    """
    AC-19: Mobile Device Wipe Operation
    
    Tracks remote wipe operations on mobile devices.
    """
    __tablename__ = "mobile_device_wipes"
    __table_args__ = (
        Index('idx_mobile_wipe_device', 'device_id'),
        Index('idx_mobile_wipe_org', 'org_id'),
        Index('idx_mobile_wipe_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Wipe details
    wipe_type = Column(String(50), nullable=False)  # full, selective, account_only
    reason = Column(Text, nullable=False)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False)  # pending, in_progress, completed, failed
    initiated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Result
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("MobileDevice", back_populates="wipe_operations")


# ============================================================================
# AC-20: Use of External Systems
# ============================================================================

class ExternalSystemType(str, PyEnum):
    """External system types"""
    CLOUD_SERVICE = "cloud_service"
    API_INTEGRATION = "api_integration"
    THIRD_PARTY_SOFTWARE = "third_party_software"
    DATA_SHARING = "data_sharing"
    VENDOR_SYSTEM = "vendor_system"


class ExternalSystemStatus(str, PyEnum):
    """External system connection status"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ExternalSystem(Base):
    """
    AC-20: External System Registration
    
    Tracks external systems and their security assessments.
    """
    __tablename__ = "external_systems"
    __table_args__ = (
        Index('idx_external_system_org', 'org_id'),
        Index('idx_external_system_status', 'status'),
        Index('idx_external_system_type', 'system_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    system_type = Column(String(50), nullable=False)  # ExternalSystemType
    vendor_name = Column(String(255), nullable=True)
    vendor_contact = Column(Text, nullable=True)
    
    # Connection details
    endpoint_url = Column(String(1000), nullable=True)
    api_key_hash = Column(String(255), nullable=True)  # Hashed API key
    connection_method = Column(String(50), nullable=True)  # api, sftp, vpn, etc.
    
    # Data classification
    data_types_accessed = Column(JSON, nullable=True)  # PHI, PII, financial, etc.
    data_classification = Column(String(50), nullable=False)  # Highest classification
    
    # Security assessment
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_result = Column(String(20), nullable=True)  # approved, rejected, conditional
    security_assessment_notes = Column(Text, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Compliance
    has_baa = Column(Boolean, nullable=True)  # Business Associate Agreement
    baa_expires_at = Column(DateTime(timezone=True), nullable=True)
    has_soc2 = Column(Boolean, nullable=True)
    soc2_report_date = Column(DateTime(timezone=True), nullable=True)
    fedramp_authorized = Column(Boolean, nullable=True)
    
    # Approval workflow
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=ExternalSystemStatus.PENDING_APPROVAL.value)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=365, nullable=False)  # Annual review
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    connections = relationship("ExternalSystemConnection", back_populates="system")


class ExternalSystemConnection(Base):
    """
    AC-20: External System Connection Log
    
    Logs all connections to external systems for audit and monitoring.
    """
    __tablename__ = "external_system_connections"
    __table_args__ = (
        Index('idx_external_conn_timestamp', 'timestamp'),
        Index('idx_external_conn_system', 'system_id'),
        Index('idx_external_conn_org', 'org_id'),
        Index('idx_external_conn_user', 'user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("external_systems.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Connection details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    action = Column(String(100), nullable=False)  # connect, data_transfer, api_call, etc.
    endpoint = Column(String(1000), nullable=True)
    
    # Data details
    data_type = Column(String(50), nullable=True)
    data_classification = Column(String(50), nullable=True)
    data_size_bytes = Column(Integer, nullable=True)
    records_count = Column(Integer, nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Connection info
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    system = relationship("ExternalSystem", back_populates="connections")


# ============================================================================
# AC-22: Publicly Accessible Content
# ============================================================================

class PublicContentType(str, PyEnum):
    """Types of publicly accessible content"""
    WEB_PAGE = "web_page"
    API_ENDPOINT = "api_endpoint"
    DOCUMENT = "document"
    MEDIA = "media"
    FORM = "form"


class PublicContentStatus(str, PyEnum):
    """Public content status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class PublicContent(Base):
    """
    AC-22: Publicly Accessible Content
    
    Tracks all content that is publicly accessible and requires review.
    """
    __tablename__ = "public_content"
    __table_args__ = (
        Index('idx_public_content_org', 'org_id'),
        Index('idx_public_content_status', 'status'),
        Index('idx_public_content_type', 'content_type'),
        Index('idx_public_content_url', 'url'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content identification
    content_name = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # PublicContentType
    url = Column(String(2000), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Content details
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash of content
    file_path = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Classification
    contains_phi = Column(Boolean, default=False, nullable=False)
    contains_pii = Column(Boolean, default=False, nullable=False)
    contains_sensitive_data = Column(Boolean, default=False, nullable=False)
    data_classification = Column(String(50), nullable=False)  # PUBLIC, INTERNAL, CONFIDENTIAL, etc.
    
    # Review workflow
    status = Column(String(20), nullable=False, default=PublicContentStatus.DRAFT.value)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_for_review_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Publishing
    published_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=90, nullable=False)  # Quarterly review
    
    # Access tracking
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    access_logs = relationship("PublicContentAccessLog", back_populates="content")


class PublicContentAccessLog(Base):
    """
    AC-22: Public Content Access Log
    
    Logs all access to publicly accessible content for monitoring.
    """
    __tablename__ = "public_content_access_logs"
    __table_args__ = (
        Index('idx_public_log_timestamp', 'timestamp'),
        Index('idx_public_log_content', 'content_id'),
        Index('idx_public_log_org', 'org_id'),
        Index('idx_public_log_ip', 'ip_address'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("public_content.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Access details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(2000), nullable=True)
    
    # Location
    country = Column(String(2), nullable=True)  # ISO country code
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Request details
    request_method = Column(String(10), nullable=True)  # GET, POST, etc.
    response_status = Column(Integer, nullable=True)  # HTTP status code
    bytes_transferred = Column(Integer, nullable=True)
    
    # User identification (if authenticated)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    content = relationship("PublicContent", back_populates="access_logs")
