"""
Audit Failure Response Models for FedRAMP AU-5 Compliance

FedRAMP Requirement AU-5: Response to Audit Processing Failures
- Alert on audit system failures
- Take action on audit failures
- Failover to alternate logging
- Capacity monitoring
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


class AuditFailureSeverity(str, Enum):
    """Severity of audit system failure"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditFailureStatus(str, Enum):
    """Status of audit failure response"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FAILOVER_ACTIVE = "failover_active"
    CAPACITY_EXCEEDED = "capacity_exceeded"


class AuditFailureType(str, Enum):
    """Type of audit system failure"""
    STORAGE_FULL = "storage_full"
    WRITE_FAILURE = "write_failure"
    NETWORK_FAILURE = "network_failure"
    DATABASE_ERROR = "database_error"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    PERMISSION_DENIED = "permission_denied"
    SYSTEM_OVERLOAD = "system_overload"
    UNKNOWN = "unknown"


class AuditFailureResponse(Base):
    """
    Audit failure detection and response records (AU-5).
    
    Tracks audit system failures and response actions.
    """
    __tablename__ = "audit_failure_responses"
    __table_args__ = (
        Index('idx_audit_failure_org_status', 'org_id', 'status'),
        Index('idx_audit_failure_detected', 'detected_at'),
        Index('idx_audit_failure_type', 'failure_type'),
        Index('idx_audit_failure_severity', 'severity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Failure details
    failure_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    severity = Column(
        String(50),
        nullable=False,
        index=True,
    )
    status = Column(
        String(50),
        nullable=False,
        default=AuditFailureStatus.DETECTED.value,
        index=True,
    )
    
    # Failure description
    failure_message = Column(Text, nullable=False)
    error_code = Column(String(100), nullable=True)
    error_details = Column(JSON, nullable=True)  # Additional error context
    
    # Detection
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    detected_by = Column(String(255), nullable=True)  # System component that detected
    
    # Response actions
    alert_sent = Column(Boolean, default=False, nullable=False)
    alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    alert_recipients = Column(JSON, nullable=True)  # List of recipients
    
    # Failover
    failover_activated = Column(Boolean, default=False, nullable=False)
    failover_activated_at = Column(DateTime(timezone=True), nullable=True)
    failover_target = Column(String(255), nullable=True)  # Alternate logging system
    failover_status = Column(String(50), nullable=True)  # active, failed, restored
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes = Column(Text, nullable=True)
    
    # Capacity monitoring
    storage_usage_percent = Column(Integer, nullable=True)  # Storage usage at time of failure
    log_rate_per_second = Column(Integer, nullable=True)  # Log rate when failure occurred
    
    # Impact assessment
    affected_events_count = Column(Integer, nullable=True)  # Number of events potentially lost
    events_recovered = Column(Integer, nullable=True)  # Number of events recovered
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<AuditFailureResponse(id={self.id}, "
            f"failure_type={self.failure_type}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )


class AuditSystemCapacity(Base):
    """
    Audit system capacity monitoring (AU-5).
    
    Tracks capacity metrics to prevent failures.
    """
    __tablename__ = "audit_system_capacity"
    __table_args__ = (
        Index('idx_capacity_org_timestamp', 'org_id', 'recorded_at'),
        Index('idx_capacity_recorded', 'recorded_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Capacity metrics
    storage_usage_percent = Column(Integer, nullable=False)  # 0-100
    storage_available_bytes = Column(Integer, nullable=True)
    storage_total_bytes = Column(Integer, nullable=True)
    
    log_rate_per_second = Column(Integer, nullable=True)  # Events per second
    log_queue_size = Column(Integer, nullable=True)  # Pending events
    
    # Thresholds
    storage_warning_threshold = Column(Integer, default=80, nullable=False)  # Warn at 80%
    storage_critical_threshold = Column(Integer, default=90, nullable=False)  # Critical at 90%
    
    # Status
    is_healthy = Column(Boolean, default=True, nullable=False, index=True)
    warnings_active = Column(JSON, nullable=True)  # List of active warnings
    
    # Timestamp
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<AuditSystemCapacity(id={self.id}, "
            f"storage_usage_percent={self.storage_usage_percent}, "
            f"is_healthy={self.is_healthy})>"
        )
