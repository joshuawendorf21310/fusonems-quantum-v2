"""
Non-Repudiation Models for FedRAMP AU-10 Compliance

FedRAMP Requirement AU-10: Non-Repudiation
- Digital signatures for critical actions
- Proof of origin
- Proof of receipt
- Cryptographic verification
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


class SignatureAlgorithm(str, Enum):
    """Digital signature algorithm"""
    RSA_SHA256 = "RSA-SHA256"
    RSA_SHA512 = "RSA-SHA512"
    ECDSA_SHA256 = "ECDSA-SHA256"
    ECDSA_SHA512 = "ECDSA-SHA512"
    ED25519 = "ED25519"


class SignatureStatus(str, Enum):
    """Status of digital signature"""
    PENDING = "pending"
    SIGNED = "signed"
    VERIFIED = "verified"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ActionCriticality(str, Enum):
    """Criticality level of action requiring signature"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DigitalSignature(Base):
    """
    Digital signature records for non-repudiation (AU-10).
    
    Stores digital signatures for critical actions to provide proof of origin.
    """
    __tablename__ = "digital_signatures"
    __table_args__ = (
        Index('idx_signature_org_resource', 'org_id', 'resource_type', 'resource_id'),
        Index('idx_signature_user', 'signed_by_user_id'),
        Index('idx_signature_status', 'status'),
        Index('idx_signature_created', 'created_at'),
        Index('idx_signature_hash', 'content_hash'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Resource being signed
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., "user", "configuration", "document"
    resource_id = Column(String(255), nullable=False, index=True)
    
    # Action being signed
    action = Column(String(255), nullable=False)  # e.g., "create", "update", "delete", "approve"
    action_criticality = Column(
        String(50),
        nullable=False,
        default=ActionCriticality.MEDIUM.value,
    )
    
    # Content being signed
    content_hash = Column(String(255), nullable=False, index=True)  # SHA-256 hash of content
    content_preview = Column(Text, nullable=True)  # Preview of content (truncated)
    full_content = Column(JSON, nullable=True)  # Full content (encrypted or redacted)
    
    # Signature details
    signature_algorithm = Column(
        String(50),
        nullable=False,
        default=SignatureAlgorithm.RSA_SHA256.value,
    )
    signature_value = Column(Text, nullable=False)  # Base64-encoded signature
    signature_certificate = Column(Text, nullable=True)  # Certificate used for signing
    
    # Signer
    signed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    signed_by_email = Column(String(255), nullable=True)  # Denormalized
    signed_by_role = Column(String(100), nullable=True)  # Denormalized
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    signed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=SignatureStatus.SIGNED.value,
        index=True,
    )
    
    # Verification
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_result = Column(Text, nullable=True)  # Verification details
    
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
    
    # Related audit log
    audit_log_id = Column(UUID(as_uuid=True), nullable=True)  # Link to comprehensive_audit_logs
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<DigitalSignature(id={self.id}, "
            f"resource_type={self.resource_type}, "
            f"action={self.action}, "
            f"status={self.status})>"
        )


class ReceiptConfirmation(Base):
    """
    Receipt confirmation records for non-repudiation (AU-10).
    
    Provides proof of receipt for critical communications and actions.
    """
    __tablename__ = "receipt_confirmations"
    __table_args__ = (
        Index('idx_receipt_org_resource', 'org_id', 'resource_type', 'resource_id'),
        Index('idx_receipt_recipient', 'recipient_user_id'),
        Index('idx_receipt_status', 'status'),
        Index('idx_receipt_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Resource being acknowledged
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    
    # Communication/action details
    communication_type = Column(String(100), nullable=False)  # e.g., "notification", "approval_request", "document"
    communication_content = Column(Text, nullable=True)  # Content preview
    
    # Sender
    sent_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sent_by_email = Column(String(255), nullable=True)
    
    # Recipient
    recipient_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    recipient_email = Column(String(255), nullable=True)
    
    # Receipt details
    receipt_hash = Column(String(255), nullable=False)  # Hash of receipt content
    receipt_signature = Column(Text, nullable=True)  # Digital signature of receipt
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    sent_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    received_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, received, acknowledged, expired
    
    # Acknowledgment
    acknowledgment_message = Column(Text, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<ReceiptConfirmation(id={self.id}, "
            f"resource_type={self.resource_type}, "
            f"recipient_user_id={self.recipient_user_id}, "
            f"status={self.status})>"
        )
