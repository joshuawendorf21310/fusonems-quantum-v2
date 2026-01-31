"""
Multi-Factor Authentication Models
FedRAMP Control: IA-2(1), IA-2(2)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base


class MFADevice(Base):
    """
    MFA Device registration
    Supports TOTP authenticators, hardware tokens, etc.
    """
    __tablename__ = "mfa_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    device_name = Column(String(255), nullable=False)  # User-friendly name
    device_type = Column(String(50), nullable=False, default="totp")  # totp, webauthn, sms, hardware
    
    # Encrypted TOTP secret (must use FIPS 140-2 encryption)
    secret_encrypted = Column(Text, nullable=False)
    
    # Device status
    is_active = Column(Boolean, default=False, nullable=False)
    enrolled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    verified_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    device_fingerprint = Column(String(255), nullable=True)  # For device identification
    last_ip = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mfa_devices")


class MFABackupCode(Base):
    """
    MFA Backup Codes for account recovery
    FedRAMP requires alternative authentication methods
    """
    __tablename__ = "mfa_backup_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Hashed backup code (never store plaintext)
    code_hash = Column(String(64), nullable=False, unique=True)
    
    # Usage tracking
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime(timezone=True), nullable=True)
    used_ip = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User")


class MFAAttempt(Base):
    """
    MFA Verification Attempts
    For audit logging and security monitoring
    """
    __tablename__ = "mfa_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("mfa_devices.id", ondelete="CASCADE"), nullable=True)
    
    # Attempt details
    attempt_type = Column(String(50), nullable=False)  # totp, backup_code, sms, etc.
    success = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    failure_reason = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User")
    device = relationship("MFADevice")
