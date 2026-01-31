"""
Physical & Environmental (PE) FedRAMP Controls Models

This module contains models for:
- PE-2: Physical Access Authorizations
- PE-3: Physical Access Control
- PE-4: Access Control for Transmission Medium
- PE-5: Access Control for Output Devices
- PE-6: Monitoring Physical Access
- PE-8: Visitor Access Records
- PE-9: Power Equipment & Cabling
- PE-10: Emergency Shutoff
- PE-11: Emergency Power
- PE-12: Emergency Lighting
- PE-13: Fire Protection
- PE-14: Temperature and Humidity
- PE-15: Water Damage Protection
- PE-16: Delivery and Removal
- PE-17: Alternate Work Site
- PE-18: Location of Information System Components
- PE-19: Information Leakage
- PE-20: Asset Monitoring and Tracking
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
    Numeric,
    String,
    Text,
    func,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


# ============================================================================
# PE-2: Physical Access Authorizations
# ============================================================================

class AuthorizationStatus(str, PyEnum):
    """Physical access authorization status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"
    EXPIRED = "expired"


class BadgeType(str, PyEnum):
    """Badge/credential types"""
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    VISITOR = "visitor"
    VENDOR = "vendor"
    EMERGENCY = "emergency"


class PhysicalAccessAuthorization(Base):
    """
    PE-2: Physical Access Authorization
    
    Tracks physical access authorizations, badge assignments, and access levels.
    """
    __tablename__ = "physical_access_authorizations"
    __table_args__ = (
        Index('idx_pe2_org', 'org_id'),
        Index('idx_pe2_user', 'user_id'),
        Index('idx_pe2_status', 'status'),
        Index('idx_pe2_expires', 'expires_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Authorization details
    authorization_type = Column(String(50), nullable=False)  # permanent, temporary, emergency
    access_level = Column(String(50), nullable=False)  # full, restricted, escorted_only
    authorized_areas = Column(JSON, nullable=False)  # List of area IDs or names
    authorized_hours = Column(JSON, nullable=True)  # Time restrictions
    authorized_days = Column(JSON, nullable=True)  # Day restrictions
    
    # Badge/Credential
    badge_number = Column(String(50), nullable=True, unique=True, index=True)
    badge_type = Column(String(20), nullable=False)  # BadgeType
    credential_type = Column(String(50), nullable=False)  # card, fob, biometric, pin
    credential_id = Column(String(255), nullable=True)  # RFID, biometric template ID, etc.
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=AuthorizationStatus.PENDING.value)
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Approval workflow
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=365, nullable=False)  # Annual review
    
    # Metadata
    justification = Column(Text, nullable=True)
    special_conditions = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    access_logs = relationship("PhysicalAccessLog", back_populates="authorization")


# ============================================================================
# PE-3: Physical Access Control
# ============================================================================

class AccessPointType(str, PyEnum):
    """Access point types"""
    DOOR = "door"
    GATE = "gate"
    ELEVATOR = "elevator"
    PARKING = "parking"
    SERVER_ROOM = "server_room"
    DATA_CENTER = "data_center"


class AccessControlMethod(str, PyEnum):
    """Access control methods"""
    CARD_READER = "card_reader"
    BIOMETRIC = "biometric"
    PIN = "pin"
    KEY = "key"
    MANUAL = "manual"
    REMOTE = "remote"


class AccessPoint(Base):
    """
    PE-3: Physical Access Control - Access Points
    
    Defines physical access points and their security controls.
    """
    __tablename__ = "access_points"
    __table_args__ = (
        Index('idx_pe3_org', 'org_id'),
        Index('idx_pe3_type', 'access_point_type'),
        Index('idx_pe3_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Access point identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    access_point_type = Column(String(20), nullable=False)  # AccessPointType
    area_id = Column(String(100), nullable=True)  # Security zone/area identifier
    
    # Access control methods
    primary_method = Column(String(20), nullable=False)  # AccessControlMethod
    secondary_methods = Column(JSON, nullable=True)  # List of additional methods
    requires_dual_auth = Column(Boolean, default=False, nullable=False)
    requires_escort = Column(Boolean, default=False, nullable=False)
    
    # Monitoring
    has_surveillance = Column(Boolean, default=False, nullable=False)
    camera_ids = Column(JSON, nullable=True)  # Associated camera IDs
    has_alarm = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    
    # IoT/Sensor integration
    device_id = Column(String(255), nullable=True)  # IoT device identifier
    sensor_data_endpoint = Column(String(1000), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    access_events = relationship("PhysicalAccessLog", back_populates="access_point")


class PhysicalAccessLog(Base):
    """
    PE-3: Physical Access Control - Access Log
    
    Logs all physical access attempts and events.
    """
    __tablename__ = "physical_access_logs"
    __table_args__ = (
        Index('idx_pe3_log_timestamp', 'timestamp'),
        Index('idx_pe3_log_user', 'user_id'),
        Index('idx_pe3_log_point', 'access_point_id'),
        Index('idx_pe3_log_result', 'access_result'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    authorization_id = Column(Integer, ForeignKey("physical_access_authorizations.id", ondelete="SET NULL"), nullable=True)
    access_point_id = Column(Integer, ForeignKey("access_points.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Access event details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    access_method = Column(String(20), nullable=False)  # AccessControlMethod
    credential_id = Column(String(255), nullable=True)
    badge_number = Column(String(50), nullable=True)
    
    # Result
    access_result = Column(String(20), nullable=False)  # granted, denied, tailgating_detected
    denial_reason = Column(String(255), nullable=True)
    
    # Tailgating detection
    tailgating_detected = Column(Boolean, default=False, nullable=False)
    tailgating_severity = Column(String(20), nullable=True)  # low, medium, high
    
    # Location
    location = Column(String(255), nullable=True)
    gps_coordinates = Column(JSON, nullable=True)  # lat, lon
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    authorization = relationship("PhysicalAccessAuthorization", back_populates="access_logs")
    access_point = relationship("AccessPoint", back_populates="access_events")


# ============================================================================
# PE-4: Access Control for Transmission Medium
# ============================================================================

class TransmissionMediumType(str, PyEnum):
    """Transmission medium types"""
    FIBER_OPTIC = "fiber_optic"
    COPPER_CABLE = "copper_cable"
    WIRELESS = "wireless"
    CONDUIT = "conduit"
    PATCH_PANEL = "patch_panel"


class PhysicalNetworkSecurity(Base):
    """
    PE-4: Access Control for Transmission Medium
    
    Tracks physical network infrastructure security and protection.
    """
    __tablename__ = "transmission_medium_security"
    __table_args__ = (
        Index('idx_pe4_org', 'org_id'),
        Index('idx_pe4_type', 'medium_type'),
        Index('idx_pe4_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Medium identification
    identifier = Column(String(255), nullable=False, unique=True)
    medium_type = Column(String(20), nullable=False)  # TransmissionMediumType
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    route_path = Column(JSON, nullable=True)  # Physical path coordinates
    
    # Protection measures
    is_encrypted = Column(Boolean, default=True, nullable=False)
    has_physical_protection = Column(Boolean, default=True, nullable=False)
    protection_type = Column(JSON, nullable=True)  # conduit, armored, buried, etc.
    has_tamper_detection = Column(Boolean, default=False, nullable=False)
    
    # Access control
    access_restricted = Column(Boolean, default=True, nullable=False)
    authorized_personnel = Column(JSON, nullable=True)  # List of user IDs
    requires_escort = Column(Boolean, default=False, nullable=False)
    
    # Inspection and maintenance
    last_inspection = Column(DateTime(timezone=True), nullable=True)
    next_inspection_due = Column(DateTime(timezone=True), nullable=True)
    inspection_frequency_days = Column(Integer, default=90, nullable=False)  # Quarterly
    inspection_results = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), nullable=False, default="operational")  # operational, maintenance, compromised
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================================
# PE-5: Access Control for Output Devices
# ============================================================================

class OutputDeviceType(str, PyEnum):
    """Output device types"""
    PRINTER = "printer"
    SCANNER = "scanner"
    FAX = "fax"
    COPIER = "copier"
    DISPLAY = "display"
    PROJECTOR = "projector"


class OutputDevice(Base):
    """
    PE-5: Access Control for Output Devices
    
    Tracks output devices and their access controls.
    """
    __tablename__ = "output_devices"
    __table_args__ = (
        Index('idx_pe5_org', 'org_id'),
        Index('idx_pe5_type', 'device_type'),
        Index('idx_pe5_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Device identification
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(20), nullable=False)  # OutputDeviceType
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    location = Column(String(255), nullable=False)
    
    # Access control
    requires_authentication = Column(Boolean, default=True, nullable=False)
    authentication_method = Column(String(50), nullable=True)  # card, pin, biometric
    authorized_users = Column(JSON, nullable=True)  # List of user IDs
    access_restricted = Column(Boolean, default=True, nullable=False)
    
    # Output monitoring
    logs_output = Column(Boolean, default=True, nullable=False)
    requires_secure_pickup = Column(Boolean, default=False, nullable=False)
    secure_pickup_location = Column(String(255), nullable=True)
    
    # Secure disposal
    has_secure_disposal = Column(Boolean, default=False, nullable=False)
    disposal_method = Column(String(50), nullable=True)  # shredding, degaussing, destruction
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    output_logs = relationship("OutputDeviceLog", back_populates="device")


class OutputDeviceLog(Base):
    """
    PE-5: Output Device Access Log
    
    Logs all output device usage and access.
    """
    __tablename__ = "output_device_logs"
    __table_args__ = (
        Index('idx_pe5_log_timestamp', 'timestamp'),
        Index('idx_pe5_log_device', 'device_id'),
        Index('idx_pe5_log_user', 'user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("output_devices.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Usage details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    action = Column(String(50), nullable=False)  # print, scan, copy, fax, access
    document_type = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    data_classification = Column(String(50), nullable=True)  # PHI, PII, PUBLIC, etc.
    
    # Access result
    access_granted = Column(Boolean, nullable=False)
    denial_reason = Column(String(255), nullable=True)
    
    # Pickup/disposal
    picked_up = Column(Boolean, nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    disposed_securely = Column(Boolean, nullable=True)
    disposal_method = Column(String(50), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("OutputDevice", back_populates="output_logs")


# ============================================================================
# PE-6: Monitoring Physical Access
# ============================================================================

class SurveillanceSystemType(str, PyEnum):
    """Surveillance system types"""
    CCTV = "cctv"
    IP_CAMERA = "ip_camera"
    MOTION_SENSOR = "motion_sensor"
    INFRARED = "infrared"
    THERMAL = "thermal"


class SurveillanceSystem(Base):
    """
    PE-6: Monitoring Physical Access - Surveillance System
    
    Tracks surveillance systems and cameras.
    """
    __tablename__ = "surveillance_systems"
    __table_args__ = (
        Index('idx_pe6_org', 'org_id'),
        Index('idx_pe6_type', 'system_type'),
        Index('idx_pe6_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    system_type = Column(String(20), nullable=False)  # SurveillanceSystemType
    location = Column(String(255), nullable=False)
    coverage_area = Column(JSON, nullable=True)  # Area description or coordinates
    
    # Camera/Device details
    device_id = Column(String(255), nullable=True, unique=True)
    ip_address = Column(String(45), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    
    # Recording settings
    records_continuously = Column(Boolean, default=True, nullable=False)
    motion_activated = Column(Boolean, default=False, nullable=False)
    retention_days = Column(Integer, default=90, nullable=False)  # Video retention period
    storage_location = Column(String(500), nullable=True)
    
    # Access and monitoring
    monitored_by = Column(JSON, nullable=True)  # List of user IDs or security team
    has_live_monitoring = Column(Boolean, default=False, nullable=False)
    alert_on_motion = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    incidents = relationship("SurveillanceIncident", back_populates="system")


class SurveillanceIncident(Base):
    """
    PE-6: Surveillance Incident Detection
    
    Tracks incidents detected by surveillance systems.
    """
    __tablename__ = "surveillance_incidents"
    __table_args__ = (
        Index('idx_pe6_inc_timestamp', 'detected_at'),
        Index('idx_pe6_inc_system', 'system_id'),
        Index('idx_pe6_inc_severity', 'severity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("surveillance_systems.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Incident details
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    incident_type = Column(String(50), nullable=False)  # unauthorized_access, motion, tampering, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=True)
    
    # Video evidence
    video_start_time = Column(DateTime(timezone=True), nullable=True)
    video_end_time = Column(DateTime(timezone=True), nullable=True)
    video_file_path = Column(String(1000), nullable=True)
    
    # Response
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    response_action = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    system = relationship("SurveillanceSystem", back_populates="incidents")


# ============================================================================
# PE-8: Visitor Access Records
# ============================================================================

class VisitorStatus(str, PyEnum):
    """Visitor status"""
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    EXPIRED = "expired"
    REVOKED = "revoked"


class VisitorAccessRecord(Base):
    """
    PE-8: Visitor Access Records
    
    Tracks visitor access, escorts, and access logs.
    """
    __tablename__ = "visitor_access_records"
    __table_args__ = (
        Index('idx_pe8_org', 'org_id'),
        Index('idx_pe8_status', 'status'),
        Index('idx_pe8_checkin', 'check_in_time'),
        Index('idx_pe8_visitor', 'visitor_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Visitor information
    visitor_name = Column(String(255), nullable=False, index=True)
    visitor_company = Column(String(255), nullable=True)
    visitor_email = Column(String(255), nullable=True)
    visitor_phone = Column(String(50), nullable=True)
    visitor_id_number = Column(String(255), nullable=True)  # Driver's license, passport, etc.
    
    # Visit details
    purpose = Column(Text, nullable=False)
    host_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Employee hosting visitor
    authorized_areas = Column(JSON, nullable=False)  # List of areas visitor can access
    requires_escort = Column(Boolean, default=True, nullable=False)
    escort_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Badge/Credential
    badge_number = Column(String(50), nullable=True)
    badge_issued_at = Column(DateTime(timezone=True), nullable=True)
    badge_returned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Visit timing
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True, index=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=VisitorStatus.SCHEDULED.value)
    
    # Registration
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_out_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Special conditions
    special_instructions = Column(Text, nullable=True)
    nda_required = Column(Boolean, default=False, nullable=False)
    nda_signed = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    access_logs = relationship("VisitorAccessLog", back_populates="visitor_record")


class VisitorAccessLog(Base):
    """
    PE-8: Visitor Access Log
    
    Logs all visitor access events.
    """
    __tablename__ = "visitor_access_logs"
    __table_args__ = (
        Index('idx_pe8_log_timestamp', 'timestamp'),
        Index('idx_pe8_log_visitor', 'visitor_record_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    visitor_record_id = Column(Integer, ForeignKey("visitor_access_records.id", ondelete="CASCADE"), nullable=True, index=True)
    access_point_id = Column(Integer, ForeignKey("access_points.id", ondelete="SET NULL"), nullable=True)
    
    # Access event
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    action = Column(String(50), nullable=False)  # entry, exit, area_access
    location = Column(String(255), nullable=True)
    access_granted = Column(Boolean, nullable=False)
    
    # Escort tracking
    escorted = Column(Boolean, nullable=True)
    escort_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    visitor_record = relationship("VisitorAccessRecord", back_populates="access_logs")


# ============================================================================
# PE-9: Power Equipment & Cabling
# ============================================================================

class PowerEquipmentType(str, PyEnum):
    """Power equipment types"""
    UPS = "ups"
    PDU = "pdu"
    GENERATOR = "generator"
    TRANSFORMER = "transformer"
    BATTERY_BACKUP = "battery_backup"
    POWER_DISTRIBUTION = "power_distribution"


class PowerEquipment(Base):
    """
    PE-9: Power Equipment & Cabling
    
    Tracks power equipment, UPS systems, and power events.
    """
    __tablename__ = "power_equipment"
    __table_args__ = (
        Index('idx_pe9_org', 'org_id'),
        Index('idx_pe9_type', 'equipment_type'),
        Index('idx_pe9_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Equipment identification
    equipment_name = Column(String(255), nullable=False)
    equipment_type = Column(String(20), nullable=False)  # PowerEquipmentType
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    location = Column(String(255), nullable=False)
    
    # Power specifications
    capacity_kw = Column(Numeric(10, 2), nullable=True)
    voltage = Column(String(50), nullable=True)
    phase = Column(String(20), nullable=True)  # single, three
    
    # UPS/Battery specific
    battery_capacity_ah = Column(Numeric(10, 2), nullable=True)
    runtime_minutes = Column(Numeric(10, 2), nullable=True)
    battery_age_months = Column(Integer, nullable=True)
    last_battery_replacement = Column(DateTime(timezone=True), nullable=True)
    
    # Status and monitoring
    is_active = Column(Boolean, default=True, nullable=False)
    operational_status = Column(String(20), nullable=False, default="operational")  # operational, maintenance, failed
    last_status_check = Column(DateTime(timezone=True), nullable=True)
    
    # IoT/Sensor integration
    device_id = Column(String(255), nullable=True)
    monitoring_endpoint = Column(String(1000), nullable=True)
    supports_snmp = Column(Boolean, default=False, nullable=False)
    
    # Maintenance
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    maintenance_frequency_days = Column(Integer, default=90, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    power_events = relationship("PowerEvent", back_populates="equipment")


class PowerEvent(Base):
    """
    PE-9: Power Event Log
    
    Logs power events, outages, and equipment status changes.
    """
    __tablename__ = "power_events"
    __table_args__ = (
        Index('idx_pe9_event_timestamp', 'timestamp'),
        Index('idx_pe9_event_equipment', 'equipment_id'),
        Index('idx_pe9_event_type', 'event_type'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey("power_equipment.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Event details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    event_type = Column(String(50), nullable=False)  # outage, surge, brownout, battery_test, maintenance
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Power metrics
    voltage_reading = Column(Numeric(10, 2), nullable=True)
    current_reading = Column(Numeric(10, 2), nullable=True)
    load_percentage = Column(Numeric(5, 2), nullable=True)
    battery_level_percent = Column(Numeric(5, 2), nullable=True)
    runtime_remaining_minutes = Column(Numeric(10, 2), nullable=True)
    
    # Duration
    duration_seconds = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Impact
    systems_affected = Column(JSON, nullable=True)  # List of affected systems
    impact_description = Column(Text, nullable=True)
    
    # Response
    responded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    response_action = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    equipment = relationship("PowerEquipment", back_populates="power_events")


# ============================================================================
# PE-10: Emergency Shutoff
# ============================================================================

class EmergencyShutoffLocation(Base):
    """
    PE-10: Emergency Shutoff
    
    Tracks emergency shutoff locations, procedures, and tests.
    """
    __tablename__ = "emergency_shutoff_locations"
    __table_args__ = (
        Index('idx_pe10_org', 'org_id'),
        Index('idx_pe10_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location identification
    location_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Shutoff type
    shutoff_type = Column(String(50), nullable=False)  # power, gas, water, hvac, network
    affects_systems = Column(JSON, nullable=False)  # List of affected systems
    
    # Procedure documentation
    procedure_document_path = Column(String(1000), nullable=True)
    procedure_steps = Column(JSON, nullable=True)  # Step-by-step procedure
    authorized_personnel = Column(JSON, nullable=True)  # List of user IDs authorized to operate
    
    # Safety requirements
    requires_ppe = Column(Boolean, default=False, nullable=False)
    ppe_requirements = Column(JSON, nullable=True)
    safety_warnings = Column(Text, nullable=True)
    
    # Testing
    last_test_date = Column(DateTime(timezone=True), nullable=True)
    next_test_due = Column(DateTime(timezone=True), nullable=True)
    test_frequency_days = Column(Integer, default=90, nullable=False)  # Quarterly testing
    test_results = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_operational = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    activations = relationship("EmergencyShutoffActivation", back_populates="location")


class EmergencyShutoffActivation(Base):
    """
    PE-10: Emergency Shutoff Activation Log
    
    Logs all emergency shutoff activations.
    """
    __tablename__ = "emergency_shutoff_activations"
    __table_args__ = (
        Index('idx_pe10_act_timestamp', 'activated_at'),
        Index('idx_pe10_act_location', 'location_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("emergency_shutoff_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Activation details
    activated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    activation_reason = Column(Text, nullable=False)
    is_emergency = Column(Boolean, default=True, nullable=False)
    
    # Duration
    restored_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Impact
    systems_affected = Column(JSON, nullable=True)
    impact_description = Column(Text, nullable=True)
    
    # Restoration
    restored_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restoration_notes = Column(Text, nullable=True)
    
    # Approval
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    location = relationship("EmergencyShutoffLocation", back_populates="activations")


# ============================================================================
# PE-11: Emergency Power
# ============================================================================

class EmergencyPowerSystem(Base):
    """
    PE-11: Emergency Power
    
    Tracks emergency power systems, generators, and battery backups.
    """
    __tablename__ = "emergency_power_systems"
    __table_args__ = (
        Index('idx_pe11_org', 'org_id'),
        Index('idx_pe11_type', 'system_type'),
        Index('idx_pe11_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    system_type = Column(String(50), nullable=False)  # generator, battery, ups, fuel_cell
    location = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Generator specific
    generator_capacity_kw = Column(Numeric(10, 2), nullable=True)
    fuel_type = Column(String(50), nullable=True)  # diesel, natural_gas, propane
    fuel_capacity_gallons = Column(Numeric(10, 2), nullable=True)
    runtime_hours = Column(Numeric(10, 2), nullable=True)
    
    # Battery specific
    battery_capacity_ah = Column(Numeric(10, 2), nullable=True)
    battery_voltage = Column(String(50), nullable=True)
    battery_count = Column(Integer, nullable=True)
    battery_age_months = Column(Integer, nullable=True)
    
    # Status and monitoring
    is_active = Column(Boolean, default=True, nullable=False)
    operational_status = Column(String(20), nullable=False, default="operational")
    last_status_check = Column(DateTime(timezone=True), nullable=True)
    
    # IoT/Sensor integration
    device_id = Column(String(255), nullable=True)
    monitoring_endpoint = Column(String(1000), nullable=True)
    
    # Testing schedule
    last_test_date = Column(DateTime(timezone=True), nullable=True)
    next_test_due = Column(DateTime(timezone=True), nullable=True)
    test_frequency_days = Column(Integer, default=30, nullable=False)  # Monthly testing
    test_duration_minutes = Column(Integer, default=30, nullable=False)
    
    # Maintenance
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    maintenance_frequency_days = Column(Integer, default=90, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tests = relationship("EmergencyPowerTest", back_populates="system")
    activations = relationship("EmergencyPowerActivation", back_populates="system")


class EmergencyPowerTest(Base):
    """
    PE-11: Emergency Power Test
    
    Tracks emergency power system tests and results.
    """
    __tablename__ = "emergency_power_tests"
    __table_args__ = (
        Index('idx_pe11_test_date', 'test_date'),
        Index('idx_pe11_test_system', 'system_id'),
        Index('idx_pe11_test_result', 'test_result'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("emergency_power_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Test details
    test_date = Column(DateTime(timezone=True), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # scheduled, unscheduled, load_test, runtime_test
    test_duration_minutes = Column(Integer, nullable=False)
    
    # Test results
    test_result = Column(String(20), nullable=False)  # passed, failed, partial
    voltage_reading = Column(Numeric(10, 2), nullable=True)
    current_reading = Column(Numeric(10, 2), nullable=True)
    load_percentage = Column(Numeric(5, 2), nullable=True)
    runtime_achieved_minutes = Column(Numeric(10, 2), nullable=True)
    fuel_level_percent = Column(Numeric(5, 2), nullable=True)
    battery_level_percent = Column(Numeric(5, 2), nullable=True)
    
    # Issues and notes
    issues_identified = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Personnel
    tested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    system = relationship("EmergencyPowerSystem", back_populates="tests")


class EmergencyPowerActivation(Base):
    """
    PE-11: Emergency Power Activation
    
    Logs emergency power system activations during outages.
    """
    __tablename__ = "emergency_power_activations"
    __table_args__ = (
        Index('idx_pe11_act_timestamp', 'activated_at'),
        Index('idx_pe11_act_system', 'system_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("emergency_power_systems.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Activation details
    activated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    activation_type = Column(String(50), nullable=False)  # automatic, manual, test
    power_outage_detected = Column(Boolean, default=True, nullable=False)
    
    # Duration
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Performance metrics
    load_percentage = Column(Numeric(5, 2), nullable=True)
    fuel_consumed_gallons = Column(Numeric(10, 2), nullable=True)
    battery_depletion_percent = Column(Numeric(5, 2), nullable=True)
    
    # Systems supported
    systems_supported = Column(JSON, nullable=True)
    
    # Issues
    issues_encountered = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Personnel
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    monitored_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    system = relationship("EmergencyPowerSystem", back_populates="activations")


# ============================================================================
# PE-12: Emergency Lighting
# ============================================================================

class EmergencyLightingSystem(Base):
    """
    PE-12: Emergency Lighting
    
    Tracks emergency lighting systems, testing, and maintenance.
    """
    __tablename__ = "emergency_lighting_systems"
    __table_args__ = (
        Index('idx_pe12_org', 'org_id'),
        Index('idx_pe12_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Lighting details
    light_count = Column(Integer, nullable=True)
    light_type = Column(String(50), nullable=True)  # led, fluorescent, incandescent
    power_source = Column(String(50), nullable=True)  # battery, generator, ups
    
    # Battery backup
    battery_capacity_ah = Column(Numeric(10, 2), nullable=True)
    runtime_minutes = Column(Numeric(10, 2), nullable=True)
    battery_age_months = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    operational_status = Column(String(20), nullable=False, default="operational")
    
    # Testing schedule
    last_test_date = Column(DateTime(timezone=True), nullable=True)
    next_test_due = Column(DateTime(timezone=True), nullable=True)
    test_frequency_days = Column(Integer, default=30, nullable=False)  # Monthly testing
    
    # Maintenance
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    maintenance_frequency_days = Column(Integer, default=180, nullable=False)  # Semi-annual
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tests = relationship("EmergencyLightingTest", back_populates="system")


class EmergencyLightingTest(Base):
    """
    PE-12: Emergency Lighting Test
    
    Tracks emergency lighting system tests and results.
    """
    __tablename__ = "emergency_lighting_tests"
    __table_args__ = (
        Index('idx_pe12_test_date', 'test_date'),
        Index('idx_pe12_test_system', 'system_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("emergency_lighting_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Test details
    test_date = Column(DateTime(timezone=True), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # scheduled, unscheduled, visual, functional
    test_duration_minutes = Column(Integer, nullable=True)
    
    # Test results
    test_result = Column(String(20), nullable=False)  # passed, failed, partial
    lights_functioning = Column(Integer, nullable=True)
    lights_total = Column(Integer, nullable=True)
    battery_level_percent = Column(Numeric(5, 2), nullable=True)
    runtime_achieved_minutes = Column(Numeric(10, 2), nullable=True)
    
    # Issues
    issues_identified = Column(JSON, nullable=True)
    failed_lights = Column(JSON, nullable=True)  # List of failed light identifiers
    notes = Column(Text, nullable=True)
    
    # Personnel
    tested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    system = relationship("EmergencyLightingSystem", back_populates="tests")


# ============================================================================
# PE-13: Fire Protection
# ============================================================================

class FireSuppressionSystemType(str, PyEnum):
    """Fire suppression system types"""
    SPRINKLER = "sprinkler"
    GAS_SUPPRESSION = "gas_suppression"
    FOAM = "foam"
    DRY_CHEMICAL = "dry_chemical"
    FIRE_EXTINGUISHER = "fire_extinguisher"
    FIRE_ALARM = "fire_alarm"


class FireSuppressionSystem(Base):
    """
    PE-13: Fire Protection
    
    Tracks fire suppression systems, inspections, and tests.
    """
    __tablename__ = "fire_suppression_systems"
    __table_args__ = (
        Index('idx_pe13_org', 'org_id'),
        Index('idx_pe13_type', 'system_type'),
        Index('idx_pe13_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    system_type = Column(String(50), nullable=False)  # FireSuppressionSystemType
    location = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # System details
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    coverage_area_sqft = Column(Numeric(10, 2), nullable=True)
    
    # Suppression agent
    suppression_agent = Column(String(100), nullable=True)  # water, fm200, novec1230, etc.
    agent_capacity = Column(String(100), nullable=True)  # gallons, pounds, etc.
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    operational_status = Column(String(20), nullable=False, default="operational")
    
    # Inspection schedule
    last_inspection = Column(DateTime(timezone=True), nullable=True)
    next_inspection_due = Column(DateTime(timezone=True), nullable=True)
    inspection_frequency_days = Column(Integer, default=90, nullable=False)  # Quarterly
    
    # Testing schedule
    last_test = Column(DateTime(timezone=True), nullable=True)
    next_test_due = Column(DateTime(timezone=True), nullable=True)
    test_frequency_days = Column(Integer, default=365, nullable=False)  # Annual
    
    # Maintenance
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    maintenance_frequency_days = Column(Integer, default=180, nullable=False)  # Semi-annual
    
    # Compliance
    nfpa_compliant = Column(Boolean, nullable=True)
    local_code_compliant = Column(Boolean, nullable=True)
    certification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    inspections = relationship("FireSystemInspection", back_populates="system")
    tests = relationship("FireSystemTest", back_populates="system")


class FireSystemInspection(Base):
    """
    PE-13: Fire System Inspection
    
    Tracks fire suppression system inspections.
    """
    __tablename__ = "fire_system_inspections"
    __table_args__ = (
        Index('idx_pe13_insp_date', 'inspection_date'),
        Index('idx_pe13_insp_system', 'system_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("fire_suppression_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Inspection details
    inspection_date = Column(DateTime(timezone=True), nullable=False, index=True)
    inspection_type = Column(String(50), nullable=False)  # scheduled, unscheduled, follow_up
    inspector_name = Column(String(255), nullable=True)
    inspector_company = Column(String(255), nullable=True)
    inspector_certification = Column(String(255), nullable=True)
    
    # Inspection results
    passed = Column(Boolean, nullable=False)
    issues_identified = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Components checked
    components_checked = Column(JSON, nullable=True)
    components_passed = Column(Integer, nullable=True)
    components_failed = Column(Integer, nullable=True)
    
    # Recommendations
    recommendations = Column(Text, nullable=True)
    requires_follow_up = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    system = relationship("FireSuppressionSystem", back_populates="inspections")


class FireSystemTest(Base):
    """
    PE-13: Fire System Test
    
    Tracks fire suppression system tests.
    """
    __tablename__ = "fire_system_tests"
    __table_args__ = (
        Index('idx_pe13_test_date', 'test_date'),
        Index('idx_pe13_test_system', 'system_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("fire_suppression_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Test details
    test_date = Column(DateTime(timezone=True), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # flow_test, pressure_test, functional_test, full_discharge
    test_duration_minutes = Column(Integer, nullable=True)
    
    # Test results
    test_result = Column(String(20), nullable=False)  # passed, failed, partial
    pressure_reading = Column(Numeric(10, 2), nullable=True)
    flow_rate = Column(Numeric(10, 2), nullable=True)
    activation_time_seconds = Column(Numeric(10, 2), nullable=True)
    
    # Issues
    issues_identified = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Personnel
    tested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    system = relationship("FireSuppressionSystem", back_populates="tests")


# ============================================================================
# PE-14: Temperature and Humidity
# ============================================================================

class EnvironmentalSensor(Base):
    """
    PE-14: Temperature and Humidity Monitoring
    
    Tracks environmental sensors and monitoring systems.
    """
    __tablename__ = "environmental_sensors"
    __table_args__ = (
        Index('idx_pe14_org', 'org_id'),
        Index('idx_pe14_location', 'location'),
        Index('idx_pe14_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sensor identification
    sensor_name = Column(String(255), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # temperature, humidity, both, air_quality
    location = Column(String(255), nullable=False, index=True)
    device_id = Column(String(255), nullable=True, unique=True)  # IoT device identifier
    
    # Thresholds
    min_temperature_f = Column(Numeric(5, 2), nullable=True)
    max_temperature_f = Column(Numeric(5, 2), nullable=True)
    min_humidity_percent = Column(Numeric(5, 2), nullable=True)
    max_humidity_percent = Column(Numeric(5, 2), nullable=True)
    
    # Alert settings
    alert_on_threshold_breach = Column(Boolean, default=True, nullable=False)
    alert_recipients = Column(JSON, nullable=True)  # List of user IDs or email addresses
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_reading_at = Column(DateTime(timezone=True), nullable=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    
    # IoT integration
    monitoring_endpoint = Column(String(1000), nullable=True)
    polling_interval_seconds = Column(Integer, default=300, nullable=False)  # 5 minutes default
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    readings = relationship("EnvironmentalReading", back_populates="sensor")
    alerts = relationship("EnvironmentalAlert", back_populates="sensor")


class EnvironmentalReading(Base):
    """
    PE-14: Environmental Reading
    
    Stores environmental sensor readings.
    """
    __tablename__ = "environmental_readings"
    __table_args__ = (
        Index('idx_pe14_read_timestamp', 'timestamp'),
        Index('idx_pe14_read_sensor', 'sensor_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(Integer, ForeignKey("environmental_sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Reading details
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    temperature_f = Column(Numeric(5, 2), nullable=True)
    humidity_percent = Column(Numeric(5, 2), nullable=True)
    air_quality_index = Column(Numeric(5, 2), nullable=True)
    
    # Status
    within_thresholds = Column(Boolean, nullable=False)
    threshold_breach = Column(String(50), nullable=True)  # temperature_high, temperature_low, humidity_high, etc.
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sensor = relationship("EnvironmentalSensor", back_populates="readings")


class EnvironmentalAlert(Base):
    """
    PE-14: Environmental Alert
    
    Tracks environmental threshold breach alerts.
    """
    __tablename__ = "environmental_alerts"
    __table_args__ = (
        Index('idx_pe14_alert_timestamp', 'alerted_at'),
        Index('idx_pe14_alert_sensor', 'sensor_id'),
        Index('idx_pe14_alert_resolved', 'resolved'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(Integer, ForeignKey("environmental_sensors.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Alert details
    alerted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    alert_type = Column(String(50), nullable=False)  # temperature_high, temperature_low, humidity_high, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Reading at alert time
    temperature_f = Column(Numeric(5, 2), nullable=True)
    humidity_percent = Column(Numeric(5, 2), nullable=True)
    threshold_breached = Column(String(50), nullable=False)
    
    # Response
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    sensor = relationship("EnvironmentalSensor", back_populates="alerts")


# ============================================================================
# PE-15: Water Damage Protection
# ============================================================================

class WaterDetectionSystem(Base):
    """
    PE-15: Water Damage Protection
    
    Tracks water detection systems and inspections.
    """
    __tablename__ = "water_detection_systems"
    __table_args__ = (
        Index('idx_pe15_org', 'org_id'),
        Index('idx_pe15_location', 'location'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # System identification
    system_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Detection details
    sensor_count = Column(Integer, nullable=True)
    sensor_locations = Column(JSON, nullable=True)  # List of sensor locations
    device_id = Column(String(255), nullable=True)  # IoT device identifier
    
    # Alert settings
    alert_on_detection = Column(Boolean, default=True, nullable=False)
    alert_recipients = Column(JSON, nullable=True)
    auto_shutoff_enabled = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_test = Column(DateTime(timezone=True), nullable=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    
    # Inspection schedule
    last_inspection = Column(DateTime(timezone=True), nullable=True)
    next_inspection_due = Column(DateTime(timezone=True), nullable=True)
    inspection_frequency_days = Column(Integer, default=90, nullable=False)  # Quarterly
    
    # IoT integration
    monitoring_endpoint = Column(String(1000), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    detections = relationship("WaterDetection", back_populates="system")
    inspections = relationship("WaterSystemInspection", back_populates="system")


class WaterDetection(Base):
    """
    PE-15: Water Detection Event
    
    Logs water detection events.
    """
    __tablename__ = "water_detections"
    __table_args__ = (
        Index('idx_pe15_det_timestamp', 'detected_at'),
        Index('idx_pe15_det_system', 'system_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("water_detection_systems.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Detection details
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    sensor_location = Column(String(255), nullable=True)
    water_level_detected = Column(String(50), nullable=True)  # low, medium, high
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Response
    responded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    response_action = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Impact
    systems_affected = Column(JSON, nullable=True)
    damage_assessment = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    system = relationship("WaterDetectionSystem", back_populates="detections")


class WaterSystemInspection(Base):
    """
    PE-15: Water System Inspection
    
    Tracks water detection system inspections.
    """
    __tablename__ = "water_system_inspections"
    __table_args__ = (
        Index('idx_pe15_insp_date', 'inspection_date'),
        Index('idx_pe15_insp_system', 'system_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("water_detection_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Inspection details
    inspection_date = Column(DateTime(timezone=True), nullable=False, index=True)
    inspection_type = Column(String(50), nullable=False)  # scheduled, unscheduled, follow_up
    
    # Inspection results
    passed = Column(Boolean, nullable=False)
    sensors_functioning = Column(Integer, nullable=True)
    sensors_total = Column(Integer, nullable=True)
    issues_identified = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Personnel
    inspected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    system = relationship("WaterDetectionSystem", back_populates="inspections")


# ============================================================================
# PE-16: Delivery and Removal
# ============================================================================

class DeliveryRemovalType(str, PyEnum):
    """Delivery/removal types"""
    DELIVERY = "delivery"
    REMOVAL = "removal"
    TRANSFER = "transfer"


class DeliveryRemovalStatus(str, PyEnum):
    """Delivery/removal status"""
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeliveryRemovalRecord(Base):
    """
    PE-16: Delivery and Removal
    
    Tracks deliveries, removals, and asset transfers with chain of custody.
    """
    __tablename__ = "delivery_removal_records"
    __table_args__ = (
        Index('idx_pe16_org', 'org_id'),
        Index('idx_pe16_type', 'record_type'),
        Index('idx_pe16_status', 'status'),
        Index('idx_pe16_date', 'scheduled_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Record type
    record_type = Column(String(20), nullable=False)  # DeliveryRemovalType
    status = Column(String(20), nullable=False, default=DeliveryRemovalStatus.SCHEDULED.value)
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    actual_date = Column(DateTime(timezone=True), nullable=True)
    
    # Authorization
    authorized_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    authorization_number = Column(String(255), nullable=True, unique=True)
    authorization_notes = Column(Text, nullable=True)
    
    # Items/assets
    items = Column(JSON, nullable=False)  # List of items with descriptions, serial numbers, etc.
    asset_ids = Column(JSON, nullable=True)  # List of tracked asset IDs
    contains_sensitive_data = Column(Boolean, default=False, nullable=False)
    data_classification = Column(String(50), nullable=True)  # PHI, PII, CONFIDENTIAL, etc.
    
    # Parties
    sender_name = Column(String(255), nullable=True)
    sender_company = Column(String(255), nullable=True)
    sender_contact = Column(String(255), nullable=True)
    receiver_name = Column(String(255), nullable=True)
    receiver_company = Column(String(255), nullable=True)
    receiver_contact = Column(String(255), nullable=True)
    
    # Transportation
    carrier_name = Column(String(255), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    transportation_method = Column(String(50), nullable=True)  # courier, mail, hand_delivery
    
    # Chain of custody
    custody_chain = Column(JSON, nullable=True)  # List of custody transfers
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    verification_notes = Column(Text, nullable=True)
    
    # Security
    requires_secure_handling = Column(Boolean, default=False, nullable=False)
    secure_handling_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================================
# PE-17: Alternate Work Site
# ============================================================================

class AlternateWorkSiteStatus(str, PyEnum):
    """Alternate work site status"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AlternateWorkSite(Base):
    """
    PE-17: Alternate Work Site
    
    Tracks alternate work sites, remote locations, and security assessments.
    """
    __tablename__ = "alternate_work_sites"
    __table_args__ = (
        Index('idx_pe17_org', 'org_id'),
        Index('idx_pe17_status', 'status'),
        Index('idx_pe17_user', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Site identification
    site_name = Column(String(255), nullable=False)
    site_type = Column(String(50), nullable=False)  # home_office, co_working, client_site, temporary
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    gps_coordinates = Column(JSON, nullable=True)  # lat, lon
    
    # Usage
    usage_frequency = Column(String(50), nullable=False)  # daily, weekly, monthly, occasional
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Security assessment
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_result = Column(String(20), nullable=True)  # approved, conditional, rejected
    security_assessment_notes = Column(Text, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Security controls
    has_physical_security = Column(Boolean, nullable=True)
    has_network_security = Column(Boolean, nullable=True)
    has_access_control = Column(Boolean, nullable=True)
    security_controls_description = Column(Text, nullable=True)
    
    # Approval workflow
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=AlternateWorkSiteStatus.PENDING_APPROVAL.value)
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=365, nullable=False)  # Annual review
    
    # Compliance
    compliance_notes = Column(Text, nullable=True)
    compliance_issues = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================================
# PE-18: Location of Information System Components
# ============================================================================

class ComponentLocationType(str, PyEnum):
    """Component location types"""
    DATA_CENTER = "data_center"
    SERVER_ROOM = "server_room"
    COLOCATION = "colocation"
    CLOUD_PROVIDER = "cloud_provider"
    EDGE_LOCATION = "edge_location"
    OFFICE = "office"


class ComponentLocation(Base):
    """
    PE-18: Location of Information System Components
    
    Tracks physical locations of information system components.
    """
    __tablename__ = "component_locations"
    __table_args__ = (
        Index('idx_pe18_org', 'org_id'),
        Index('idx_pe18_type', 'location_type'),
        Index('idx_pe18_facility', 'facility_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location identification
    location_name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)  # ComponentLocationType
    facility_name = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    gps_coordinates = Column(JSON, nullable=True)
    
    # Colocation details
    colocation_provider = Column(String(255), nullable=True)
    colocation_cage_number = Column(String(100), nullable=True)
    colocation_rack_number = Column(String(100), nullable=True)
    
    # Components
    components = Column(JSON, nullable=False)  # List of component identifiers (servers, network gear, etc.)
    component_count = Column(Integer, nullable=True)
    
    # Physical security assessment
    security_assessment_date = Column(DateTime(timezone=True), nullable=True)
    security_assessment_result = Column(String(20), nullable=True)  # compliant, non_compliant, conditional
    security_assessment_notes = Column(Text, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Security controls
    has_access_control = Column(Boolean, nullable=True)
    has_surveillance = Column(Boolean, nullable=True)
    has_fire_suppression = Column(Boolean, nullable=True)
    has_environmental_controls = Column(Boolean, nullable=True)
    security_controls_description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    operational_status = Column(String(20), nullable=False, default="operational")
    
    # Review cycle
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    review_frequency_days = Column(Integer, default=365, nullable=False)  # Annual review
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================================
# PE-19: Information Leakage
# ============================================================================

class InformationLeakageAssessment(Base):
    """
    PE-19: Information Leakage
    
    Tracks TEMPEST/emanation protection assessments and mitigation measures.
    """
    __tablename__ = "information_leakage_assessments"
    __table_args__ = (
        Index('idx_pe19_org', 'org_id'),
        Index('idx_pe19_location', 'location'),
        Index('idx_pe19_date', 'assessment_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Assessment identification
    location = Column(String(255), nullable=False, index=True)
    facility_name = Column(String(255), nullable=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # tempest, emanation, rf_leakage, visual
    
    # Assessment details
    assessed_by = Column(String(255), nullable=True)  # Company or individual name
    assessor_certification = Column(String(255), nullable=True)
    equipment_tested = Column(JSON, nullable=True)  # List of equipment identifiers
    test_methodology = Column(Text, nullable=True)
    
    # Assessment results
    assessment_result = Column(String(20), nullable=False)  # compliant, non_compliant, conditional
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    vulnerabilities_identified = Column(JSON, nullable=True)
    findings = Column(Text, nullable=True)
    
    # Mitigation measures
    mitigation_measures = Column(JSON, nullable=True)  # List of implemented mitigations
    mitigation_effectiveness = Column(String(20), nullable=True)  # effective, partial, ineffective
    requires_follow_up = Column(Boolean, default=False, nullable=False)
    
    # Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_completed = Column(Boolean, default=False, nullable=False)
    follow_up_results = Column(Text, nullable=True)
    
    # Review cycle
    next_assessment_due = Column(DateTime(timezone=True), nullable=True)
    assessment_frequency_days = Column(Integer, default=1095, nullable=False)  # 3 years
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================================
# PE-20: Asset Monitoring and Tracking
# ============================================================================

class AssetTrackingMethod(str, PyEnum):
    """Asset tracking methods"""
    RFID = "rfid"
    BARCODE = "barcode"
    GPS = "gps"
    MANUAL = "manual"
    BLUETOOTH = "bluetooth"
    IOT_SENSOR = "iot_sensor"


class TrackedAsset(Base):
    """
    PE-20: Asset Monitoring and Tracking
    
    Tracks physical assets with RFID, barcode, GPS, or IoT sensors.
    """
    __tablename__ = "tracked_assets"
    __table_args__ = (
        Index('idx_pe20_org', 'org_id'),
        Index('idx_pe20_tag', 'tracking_tag'),
        Index('idx_pe20_location', 'current_location'),
        Index('idx_pe20_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Asset identification
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100), nullable=False)  # server, laptop, network_equipment, etc.
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True, unique=True, index=True)
    
    # Tracking
    tracking_method = Column(String(20), nullable=False)  # AssetTrackingMethod
    tracking_tag = Column(String(255), nullable=True, unique=True, index=True)  # RFID tag, barcode, etc.
    device_id = Column(String(255), nullable=True)  # IoT device identifier
    
    # Location tracking
    current_location = Column(String(255), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("component_locations.id", ondelete="SET NULL"), nullable=True)
    gps_coordinates = Column(JSON, nullable=True)  # Current GPS coordinates
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active, in_transit, maintenance, retired, lost
    is_critical = Column(Boolean, default=False, nullable=False)
    
    # Ownership and assignment
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_department = Column(String(100), nullable=True)
    
    # Inventory
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    purchase_cost = Column(Numeric(10, 2), nullable=True)
    warranty_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Monitoring
    requires_continuous_monitoring = Column(Boolean, default=False, nullable=False)
    monitoring_endpoint = Column(String(1000), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Reconciliation
    last_inventory_reconciliation = Column(DateTime(timezone=True), nullable=True)
    reconciliation_status = Column(String(20), nullable=True)  # verified, discrepancy, missing
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    location_history = relationship("AssetLocationHistory", back_populates="asset")
    inventory_reconciliations = relationship("AssetInventoryReconciliation", back_populates="asset")


class AssetLocationHistory(Base):
    """
    PE-20: Asset Location History
    
    Tracks asset location changes over time.
    """
    __tablename__ = "asset_location_history"
    __table_args__ = (
        Index('idx_pe20_hist_timestamp', 'timestamp'),
        Index('idx_pe20_hist_asset', 'asset_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("tracked_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location change
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    previous_location = Column(String(255), nullable=True)
    new_location = Column(String(255), nullable=False)
    location_id = Column(Integer, ForeignKey("component_locations.id", ondelete="SET NULL"), nullable=True)
    gps_coordinates = Column(JSON, nullable=True)
    
    # Change details
    change_reason = Column(String(255), nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    method = Column(String(50), nullable=True)  # manual, automated_rfid, automated_gps, etc.
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    asset = relationship("TrackedAsset", back_populates="location_history")


class AssetInventoryReconciliation(Base):
    """
    PE-20: Asset Inventory Reconciliation
    
    Tracks periodic inventory reconciliation activities.
    """
    __tablename__ = "asset_inventory_reconciliations"
    __table_args__ = (
        Index('idx_pe20_recon_date', 'reconciliation_date'),
        Index('idx_pe20_recon_asset', 'asset_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("tracked_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Reconciliation details
    reconciliation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    reconciliation_type = Column(String(50), nullable=False)  # scheduled, unscheduled, audit
    location_verified = Column(String(255), nullable=True)
    location_id = Column(Integer, ForeignKey("component_locations.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False)  # verified, discrepancy, missing, found
    discrepancy_type = Column(String(50), nullable=True)  # location_mismatch, missing, unauthorized_move
    discrepancy_notes = Column(Text, nullable=True)
    
    # Personnel
    reconciled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Follow-up
    requires_follow_up = Column(Boolean, default=False, nullable=False)
    follow_up_completed = Column(Boolean, default=False, nullable=False)
    follow_up_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    asset = relationship("TrackedAsset", back_populates="inventory_reconciliations")
