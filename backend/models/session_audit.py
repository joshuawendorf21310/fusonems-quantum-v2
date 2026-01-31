"""
Session Audit Models for FedRAMP AU-14 Compliance

FedRAMP Requirement AU-14: Session Audit
- Detailed session event capture
- User activity tracking during sessions
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
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


class SessionEventType(str, Enum):
    """Type of session event"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    ACTIVITY_START = "activity_start"
    ACTIVITY_END = "activity_end"
    PRIVILEGE_USE = "privilege_use"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"


class SessionAuditEvent(Base):
    """
    Session audit event records (AU-14).
    
    Tracks detailed events within user sessions for comprehensive auditing.
    """
    __tablename__ = "session_audit_events"
    __table_args__ = (
        Index('idx_session_audit_session', 'session_id'),
        Index('idx_session_audit_user', 'user_id', 'org_id'),
        Index('idx_session_audit_event_type', 'event_type'),
        Index('idx_session_audit_timestamp', 'timestamp'),
        Index('idx_session_audit_resource', 'resource_type', 'resource_id'),
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
        nullable=False,
        index=True,
    )
    user_email = Column(String(255), nullable=True)  # Denormalized
    
    # Session reference
    session_id = Column(
        Integer,
        ForeignKey("auth_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jwt_jti = Column(String(255), nullable=True, index=True)  # JWT ID for session
    
    # Event details
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    action = Column(String(255), nullable=False)  # Specific action performed
    resource_type = Column(String(100), nullable=True, index=True)  # Resource accessed
    resource_id = Column(String(255), nullable=True, index=True)  # Resource ID
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, etc.
    request_path = Column(String(1000), nullable=True)  # API endpoint
    
    # Event data
    event_data = Column(JSON, nullable=True)  # Additional event context
    outcome = Column(String(50), nullable=True)  # success, failure, denied
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Duration (for activity events)
    duration_seconds = Column(Integer, nullable=True)
    
    # Related audit log
    audit_log_id = Column(UUID(as_uuid=True), nullable=True)  # Link to comprehensive_audit_logs
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<SessionAuditEvent(id={self.id}, "
            f"session_id={self.session_id}, "
            f"event_type={self.event_type}, "
            f"action={self.action})>"
        )
