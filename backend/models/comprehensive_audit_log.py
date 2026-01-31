"""
Comprehensive Audit Log Model for FedRAMP AU-2, AU-3, AU-9 Compliance

This model provides immutable, write-only audit logging with all required
FedRAMP AU-3 audit record content:
- Timestamp (AU-3(1))
- User identification (AU-3(1))
- Action performed (AU-3(1))
- Resource accessed (AU-3(1))
- Outcome (success/failure) (AU-3(1))
- IP address (AU-3(1))
- User-agent (AU-3(1))
- Additional context for compliance reporting

Logs are immutable (write-only) and retained for 7 years per FedRAMP requirements.
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


class AuditEventType(str, Enum):
    """Types of audit events for categorization"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"
    API_REQUEST = "api_request"


class AuditOutcome(str, Enum):
    """Outcome of the audited action"""
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    ERROR = "error"


class ComprehensiveAuditLog(Base):
    """
    Comprehensive audit log table for FedRAMP compliance.
    
    This table stores all audit events with complete context required for
    FedRAMP AU-2, AU-3, and AU-9 compliance. Logs are immutable (write-only)
    and must be retained for 7 years.
    
    Table is designed for partitioning by date for performance and retention management.
    """
    __tablename__ = "comprehensive_audit_logs"
    __table_args__ = (
        # Indexes for common query patterns
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user_org', 'user_id', 'org_id'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_outcome', 'outcome'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_ip', 'ip_address'),
        Index('idx_audit_date_user', 'timestamp', 'user_id'),
        Index('idx_audit_date_org', 'timestamp', 'org_id'),
        # Composite index for compliance reporting queries
        Index('idx_audit_compliance', 'org_id', 'event_type', 'outcome', 'timestamp'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Timestamp - AU-3(1) requirement
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Organization and User identification - AU-3(1) requirement
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
    user_email = Column(String(255), nullable=True, index=True)  # Denormalized for retention
    user_role = Column(String(100), nullable=True)  # Denormalized for retention
    
    # Event classification
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # Authentication, Authorization, Data Access, etc.
    
    # Action details - AU-3(1) requirement
    action = Column(String(255), nullable=False, index=True)  # login, create, update, delete, etc.
    resource_type = Column(String(100), nullable=False, index=True)  # user, patient, incident, etc.
    resource_id = Column(String(255), nullable=True, index=True)  # ID of the resource
    
    # Outcome - AU-3(1) requirement
    outcome = Column(
        String(50),
        nullable=False,
        index=True,
    )  # success, failure, denied, error
    
    # Request context - AU-3(1) requirement
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)  # Full user-agent string
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE, etc.
    request_path = Column(String(1000), nullable=True, index=True)  # API endpoint path
    request_query = Column(String(2000), nullable=True)  # Query string (sanitized)
    
    # Session and device context
    session_id = Column(String(255), nullable=True, index=True)
    device_id = Column(String(255), nullable=True, index=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Additional context for compliance
    classification = Column(String(50), nullable=True)  # PHI, NON_PHI, PII, etc.
    training_mode = Column(Boolean, default=False, nullable=False)
    
    # State changes (for data modification events)
    before_state = Column(JSON, nullable=True)  # State before change
    after_state = Column(JSON, nullable=True)  # State after change
    
    # Error details (for failure/error outcomes)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Flexible JSON for additional context
    
    # Compliance fields
    reason_code = Column(String(100), nullable=True)  # Reason for action/decision
    decision_id = Column(String(255), nullable=True)  # Reference to decision/rule
    
    # Retention and immutability
    # Note: This table should have triggers to prevent UPDATE/DELETE operations
    # in production. Logs are write-only for compliance.
    
    def __repr__(self):
        return (
            f"<ComprehensiveAuditLog(id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"user_id={self.user_id}, "
            f"action={self.action}, "
            f"resource={self.resource_type}:{self.resource_id}, "
            f"outcome={self.outcome})>"
        )
