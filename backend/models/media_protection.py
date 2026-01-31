"""
Media Protection Models for FedRAMP MP-2 through MP-7 Compliance

FedRAMP Requirements:
- MP-2: Media Access - Control access to media
- MP-3: Media Marking - Mark media with classification labels
- MP-4: Media Storage - Control storage of media
- MP-5: Media Transport - Control transport of media
- MP-6: Media Sanitization - Sanitize media before disposal
- MP-7: Media Use - Control use of portable media

This module provides database models for all Media Protection controls.
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

class MediaType(str, Enum):
    """Types of media"""
    HARD_DRIVE = "hard_drive"
    USB_DRIVE = "usb_drive"
    CD_DVD = "cd_dvd"
    TAPE = "tape"
    CLOUD_STORAGE = "cloud_storage"
    NETWORK_STORAGE = "network_storage"
    PORTABLE_DEVICE = "portable_device"
    OTHER = "other"


class ClassificationLevel(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class AccessStatus(str, Enum):
    """Media access status"""
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class StorageStatus(str, Enum):
    """Media storage status"""
    IN_USE = "in_use"
    ARCHIVED = "archived"
    DISPOSED = "disposed"
    LOST = "lost"
    STOLEN = "stolen"


class TransportStatus(str, Enum):
    """Media transport status"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"


class SanitizationMethod(str, Enum):
    """Media sanitization methods"""
    DEGAUSSING = "degaussing"
    CRYPTOGRAPHIC_ERASE = "cryptographic_erase"
    PHYSICAL_DESTRUCTION = "physical_destruction"
    OVERWRITE = "overwrite"
    BLOCK_ERASE = "block_erase"
    CLEAR = "clear"
    PURGE = "purge"
    DESTROY = "destroy"


class SanitizationStatus(str, Enum):
    """Sanitization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"


class MaintenanceStatus(str, Enum):
    """Maintenance status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class MaintenanceType(str, Enum):
    """Maintenance types"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    UPGRADE = "upgrade"
    PATCH = "patch"


class RemoteMaintenanceStatus(str, Enum):
    """Remote maintenance session status"""
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


# ============================================================================
# MP-2: MEDIA ACCESS
# ============================================================================

class MediaAccess(Base):
    """
    Media access records (MP-2).
    
    Tracks who has access to which media and when.
    """
    __tablename__ = "media_access"
    __table_args__ = (
        Index('idx_media_access_org_media', 'org_id', 'media_id'),
        Index('idx_media_access_user', 'user_id'),
        Index('idx_media_access_status', 'access_status'),
        Index('idx_media_access_dates', 'granted_at', 'expires_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media reference
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_storage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # User access
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    user_email = Column(String(255), nullable=True)  # Denormalized
    
    # Access details
    access_status = Column(
        String(50),
        nullable=False,
        default=AccessStatus.GRANTED.value,
        index=True,
    )
    access_purpose = Column(Text, nullable=False)  # Why access is needed
    access_level = Column(String(50), nullable=False)  # read, write, full
    
    # Authorization
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    authorization_reason = Column(Text, nullable=True)
    
    # Timestamps
    granted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason = Column(Text, nullable=True)
    
    # Relationships
    media = relationship("MediaStorage", back_populates="access_records")
    
    def __repr__(self):
        return (
            f"<MediaAccess(id={self.id}, "
            f"media_id={self.media_id}, "
            f"user_id={self.user_id}, "
            f"access_status={self.access_status})>"
        )


# ============================================================================
# MP-3: MEDIA MARKING
# ============================================================================

class MediaMarking(Base):
    """
    Media marking records (MP-3).
    
    Tracks classification labels and markings on media.
    """
    __tablename__ = "media_marking"
    __table_args__ = (
        Index('idx_media_marking_org_media', 'org_id', 'media_id'),
        Index('idx_media_marking_classification', 'classification_level'),
        Index('idx_media_marking_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media reference
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_storage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Classification
    classification_level = Column(
        String(50),
        nullable=False,
        index=True,
    )
    classification_label = Column(String(255), nullable=False)  # Human-readable label
    classification_marking = Column(Text, nullable=True)  # Full marking text
    
    # Marking details
    marked_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    marked_by_email = Column(String(255), nullable=True)  # Denormalized
    
    # Validation
    validated = Column(Boolean, default=False, nullable=False)
    validated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    media = relationship("MediaStorage", back_populates="markings")
    
    def __repr__(self):
        return (
            f"<MediaMarking(id={self.id}, "
            f"media_id={self.media_id}, "
            f"classification_level={self.classification_level})>"
        )


# ============================================================================
# MP-4: MEDIA STORAGE
# ============================================================================

class MediaStorage(Base):
    """
    Media storage records (MP-4).
    
    Tracks storage locations and environmental controls for media.
    """
    __tablename__ = "media_storage"
    __table_args__ = (
        Index('idx_media_storage_org_status', 'org_id', 'storage_status'),
        Index('idx_media_storage_location', 'storage_location'),
        Index('idx_media_storage_type', 'media_type'),
        Index('idx_media_storage_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media identification
    media_identifier = Column(String(255), nullable=False, unique=True, index=True)  # Serial number, UUID, etc.
    media_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    media_description = Column(Text, nullable=True)
    
    # Storage location
    storage_location = Column(String(500), nullable=False, index=True)  # Physical or logical location
    storage_facility = Column(String(255), nullable=True)  # Facility name
    storage_room = Column(String(255), nullable=True)  # Room number/name
    storage_container = Column(String(255), nullable=True)  # Safe, cabinet, etc.
    
    # Environmental controls
    temperature_min = Column(String(50), nullable=True)
    temperature_max = Column(String(50), nullable=True)
    humidity_min = Column(String(50), nullable=True)
    humidity_max = Column(String(50), nullable=True)
    fire_suppression = Column(Boolean, default=False, nullable=False)
    access_control = Column(String(255), nullable=True)  # Type of access control
    
    # Status
    storage_status = Column(
        String(50),
        nullable=False,
        default=StorageStatus.IN_USE.value,
        index=True,
    )
    
    # Inventory
    inventory_date = Column(DateTime(timezone=True), nullable=True)
    last_inventory_check = Column(DateTime(timezone=True), nullable=True)
    next_inventory_check = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Disposal
    disposal_date = Column(DateTime(timezone=True), nullable=True)
    disposal_method = Column(String(100), nullable=True)
    disposal_certificate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_sanitization.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    access_records = relationship("MediaAccess", back_populates="media", cascade="all, delete-orphan")
    markings = relationship("MediaMarking", back_populates="media", cascade="all, delete-orphan")
    transport_records = relationship("MediaTransport", back_populates="media", cascade="all, delete-orphan")
    sanitization_records = relationship("MediaSanitization", back_populates="media", cascade="all, delete-orphan")
    use_records = relationship("MediaUse", back_populates="media", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<MediaStorage(id={self.id}, "
            f"media_identifier={self.media_identifier}, "
            f"storage_status={self.storage_status})>"
        )


# ============================================================================
# MP-5: MEDIA TRANSPORT
# ============================================================================

class MediaTransport(Base):
    """
    Media transport records (MP-5).
    
    Tracks transport authorization, chain of custody, and encryption.
    """
    __tablename__ = "media_transport"
    __table_args__ = (
        Index('idx_media_transport_org_media', 'org_id', 'media_id'),
        Index('idx_media_transport_status', 'transport_status'),
        Index('idx_media_transport_dates', 'transport_date', 'expected_delivery_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media reference
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_storage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Transport details
    transport_number = Column(String(100), nullable=False, unique=True, index=True)  # e.g., "TRANS-2026-001"
    transport_purpose = Column(Text, nullable=False)  # Why media is being transported
    
    # Origin and destination
    origin_location = Column(String(500), nullable=False)
    destination_location = Column(String(500), nullable=False)
    destination_contact = Column(String(255), nullable=True)
    destination_contact_phone = Column(String(50), nullable=True)
    
    # Authorization
    authorized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    authorization_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Transport personnel
    transporter_name = Column(String(255), nullable=False)
    transporter_company = Column(String(255), nullable=True)
    transporter_contact = Column(String(255), nullable=True)
    
    # Encryption
    encryption_required = Column(Boolean, default=True, nullable=False)
    encryption_method = Column(String(100), nullable=True)  # AES-256, etc.
    encryption_verified = Column(Boolean, default=False, nullable=False)
    
    # Chain of custody
    chain_of_custody = Column(JSON, nullable=True)  # Array of custody transfers
    
    # Status
    transport_status = Column(
        String(50),
        nullable=False,
        default=TransportStatus.PENDING.value,
        index=True,
    )
    
    # Dates
    transport_date = Column(DateTime(timezone=True), nullable=False, index=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True, index=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    return_date = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    tracking_number = Column(String(255), nullable=True)
    carrier_name = Column(String(255), nullable=True)
    
    # Relationships
    media = relationship("MediaStorage", back_populates="transport_records")
    
    def __repr__(self):
        return (
            f"<MediaTransport(id={self.id}, "
            f"transport_number={self.transport_number}, "
            f"transport_status={self.transport_status})>"
        )


# ============================================================================
# MP-6: MEDIA SANITIZATION
# ============================================================================

class MediaSanitization(Base):
    """
    Media sanitization records (MP-6).
    
    Tracks sanitization methods, verification, and certificate generation.
    """
    __tablename__ = "media_sanitization"
    __table_args__ = (
        Index('idx_media_sanitization_org_media', 'org_id', 'media_id'),
        Index('idx_media_sanitization_status', 'sanitization_status'),
        Index('idx_media_sanitization_method', 'sanitization_method'),
        Index('idx_media_sanitization_date', 'sanitization_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media reference
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_storage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Sanitization details
    sanitization_number = Column(String(100), nullable=False, unique=True, index=True)  # e.g., "SAN-2026-001"
    sanitization_method = Column(
        String(50),
        nullable=False,
        index=True,
    )
    sanitization_reason = Column(Text, nullable=False)  # Why sanitization is needed
    
    # Status
    sanitization_status = Column(
        String(50),
        nullable=False,
        default=SanitizationStatus.PENDING.value,
        index=True,
    )
    
    # Personnel
    sanitized_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sanitized_by_name = Column(String(255), nullable=True)  # May be external contractor
    sanitized_by_company = Column(String(255), nullable=True)
    
    # Verification
    verified = Column(Boolean, default=False, nullable=False)
    verified_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_method = Column(String(100), nullable=True)  # How verification was performed
    verification_results = Column(Text, nullable=True)
    
    # Dates
    sanitization_date = Column(DateTime(timezone=True), nullable=False, index=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Certificate
    certificate_number = Column(String(100), nullable=True, unique=True, index=True)
    certificate_issued_at = Column(DateTime(timezone=True), nullable=True)
    certificate_issued_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Documentation
    sanitization_procedures = Column(Text, nullable=True)  # Procedures followed
    sanitization_evidence = Column(JSON, nullable=True)  # Photos, logs, etc.
    
    # Relationships
    media = relationship("MediaStorage", back_populates="sanitization_records")
    
    def __repr__(self):
        return (
            f"<MediaSanitization(id={self.id}, "
            f"sanitization_number={self.sanitization_number}, "
            f"sanitization_status={self.sanitization_status})>"
        )


# ============================================================================
# MP-7: MEDIA USE
# ============================================================================

class MediaUse(Base):
    """
    Media use records (MP-7).
    
    Tracks usage of portable media and policy enforcement.
    """
    __tablename__ = "media_use"
    __table_args__ = (
        Index('idx_media_use_org_media', 'org_id', 'media_id'),
        Index('idx_media_use_user', 'user_id'),
        Index('idx_media_use_dates', 'use_start_date', 'use_end_date'),
        Index('idx_media_use_compliant', 'policy_compliant'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Media reference
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media_storage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # User
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    user_email = Column(String(255), nullable=True)  # Denormalized
    
    # Use details
    use_purpose = Column(Text, nullable=False)  # Why media is being used
    use_location = Column(String(500), nullable=True)  # Where media is being used
    device_used_on = Column(String(255), nullable=True)  # Device identifier
    
    # Policy compliance
    policy_compliant = Column(Boolean, default=True, nullable=False, index=True)
    policy_violations = Column(JSON, nullable=True)  # List of policy violations
    policy_acknowledged = Column(Boolean, default=False, nullable=False)
    policy_acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dates
    use_start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    use_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    expected_return_date = Column(DateTime(timezone=True), nullable=True)
    actual_return_date = Column(DateTime(timezone=True), nullable=True)
    
    # Monitoring
    usage_logged = Column(Boolean, default=False, nullable=False)
    data_access_logged = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    media = relationship("MediaStorage", back_populates="use_records")
    
    def __repr__(self):
        return (
            f"<MediaUse(id={self.id}, "
            f"media_id={self.media_id}, "
            f"user_id={self.user_id}, "
            f"policy_compliant={self.policy_compliant})>"
        )
