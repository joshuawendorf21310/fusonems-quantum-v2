"""
Device Authentication Models for FedRAMP IA-2(11), IA-3, IA-5(2) Compliance

FedRAMP Requirements:
- IA-2(11): Remote Access - Separate Device
- IA-3: Device Identification
- IA-5(2): PKI-Based Authentication
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


class DeviceType(str, Enum):
    """Type of device"""
    HARDWARE_TOKEN = "hardware_token"
    MOBILE_DEVICE = "mobile_device"
    WORKSTATION = "workstation"
    SERVER = "server"
    NETWORK_DEVICE = "network_device"
    UNKNOWN = "unknown"


class DeviceStatus(str, Enum):
    """Status of device"""
    PENDING = "pending"
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AuthenticationMethod(str, Enum):
    """Authentication method"""
    PKI_CERTIFICATE = "pki_certificate"
    HARDWARE_TOKEN = "hardware_token"
    SEPARATE_DEVICE = "separate_device"
    MULTI_FACTOR = "multi_factor"
    PASSWORD = "password"


class SeparateDeviceAuth(Base):
    """
    Separate device authentication records (IA-2(11)).
    
    Tracks hardware tokens and separate devices used for privileged remote access.
    """
    __tablename__ = "separate_device_auths"
    __table_args__ = (
        Index('idx_sep_device_user', 'user_id', 'org_id'),
        Index('idx_sep_device_device', 'device_id'),
        Index('idx_sep_device_status', 'status'),
        Index('idx_sep_device_created', 'created_at'),
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
    
    # Device identification
    device_id = Column(String(255), nullable=False, index=True)  # Unique device identifier
    device_type = Column(
        String(50),
        nullable=False,
        default=DeviceType.HARDWARE_TOKEN.value,
    )
    device_name = Column(String(255), nullable=True)  # User-friendly name
    device_serial = Column(String(255), nullable=True)  # Device serial number
    
    # Device fingerprint
    device_fingerprint = Column(String(255), nullable=True)  # Unique device fingerprint
    hardware_info = Column(JSON, nullable=True)  # Hardware characteristics
    
    # Registration
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    registered_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=DeviceStatus.PENDING.value,
        index=True,
    )
    
    # Usage
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Revocation
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<SeparateDeviceAuth(id={self.id}, "
            f"device_id={self.device_id}, "
            f"device_type={self.device_type}, "
            f"status={self.status})>"
        )


class DeviceIdentification(Base):
    """
    Device identification records (IA-3).
    
    Tracks device fingerprints and characteristics for device identification.
    """
    __tablename__ = "device_identifications"
    __table_args__ = (
        Index('idx_device_id_org', 'org_id'),
        Index('idx_device_id_fingerprint', 'device_fingerprint'),
        Index('idx_device_id_user', 'user_id'),
        Index('idx_device_id_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # User association (optional - devices can be shared)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Device identification
    device_fingerprint = Column(String(255), nullable=False, index=True)  # Unique fingerprint
    device_type = Column(
        String(50),
        nullable=False,
        default=DeviceType.UNKNOWN.value,
    )
    device_name = Column(String(255), nullable=True)
    
    # Device characteristics
    hardware_info = Column(JSON, nullable=True)  # CPU, memory, etc.
    software_info = Column(JSON, nullable=True)  # OS, browser, etc.
    network_info = Column(JSON, nullable=True)  # MAC address, IP ranges, etc.
    
    # Trust status
    is_trusted = Column(Boolean, default=False, nullable=False, index=True)
    trust_level = Column(Integer, default=0, nullable=False)  # 0-100
    trust_reason = Column(Text, nullable=True)  # Why device is trusted
    
    # Registration
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    first_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=DeviceStatus.PENDING.value,
        index=True,
    )
    
    # Usage statistics
    access_count = Column(Integer, default=0, nullable=False)
    last_access_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<DeviceIdentification(id={self.id}, "
            f"device_fingerprint={self.device_fingerprint}, "
            f"is_trusted={self.is_trusted})>"
        )


class PKICertificate(Base):
    """
    PKI certificate records (IA-5(2)).
    
    Stores PKI certificates for certificate-based authentication (CAC/PIV cards).
    """
    __tablename__ = "pki_certificates"
    __table_args__ = (
        Index('idx_pki_user', 'user_id', 'org_id'),
        Index('idx_pki_serial', 'certificate_serial'),
        Index('idx_pki_status', 'status'),
        Index('idx_pki_expires', 'expires_at'),
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
    
    # Certificate details
    certificate_serial = Column(String(255), nullable=False, index=True)  # Certificate serial number
    certificate_subject = Column(String(500), nullable=False)  # Subject DN
    certificate_issuer = Column(String(500), nullable=False)  # Issuer DN
    certificate_thumbprint = Column(String(255), nullable=False)  # SHA-256 thumbprint
    
    # Certificate data (encrypted)
    certificate_pem = Column(Text, nullable=True)  # PEM-encoded certificate (encrypted)
    private_key_encrypted = Column(Text, nullable=True)  # Encrypted private key (if stored)
    
    # Certificate type
    certificate_type = Column(String(50), nullable=False)  # CAC, PIV, SSL, CODE_SIGNING, etc.
    is_cac_piv = Column(Boolean, default=False, nullable=False)  # Is this a CAC/PIV card?
    
    # Validity
    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    not_before = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=DeviceStatus.PENDING.value,
        index=True,
    )
    
    # Registration
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    registered_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Usage
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Revocation
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason = Column(Text, nullable=True)
    revocation_crl_url = Column(String(500), nullable=True)  # CRL URL for revocation check
    
    # Validation
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(String(50), nullable=True)  # valid, expired, revoked, invalid
    validation_error = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<PKICertificate(id={self.id}, "
            f"certificate_serial={self.certificate_serial}, "
            f"certificate_type={self.certificate_type}, "
            f"status={self.status})>"
        )


class PKIAuthenticationAttempt(Base):
    """
    PKI authentication attempt records (IA-5(2)).
    
    Tracks certificate-based authentication attempts.
    """
    __tablename__ = "pki_authentication_attempts"
    __table_args__ = (
        Index('idx_pki_attempt_user', 'user_id', 'org_id'),
        Index('idx_pki_attempt_cert', 'certificate_id'),
        Index('idx_pki_attempt_timestamp', 'attempted_at'),
        Index('idx_pki_attempt_outcome', 'outcome'),
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
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Certificate used
    certificate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pki_certificates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    certificate_serial = Column(String(255), nullable=True)  # Denormalized
    
    # Attempt details
    attempted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    outcome = Column(String(50), nullable=False, index=True)  # success, failure, error
    failure_reason = Column(Text, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Validation details
    certificate_valid = Column(Boolean, nullable=True)
    certificate_expired = Column(Boolean, nullable=True)
    certificate_revoked = Column(Boolean, nullable=True)
    signature_valid = Column(Boolean, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<PKIAuthenticationAttempt(id={self.id}, "
            f"certificate_serial={self.certificate_serial}, "
            f"outcome={self.outcome})>"
        )
