"""
Security Event Model for FedRAMP SI-4 Compliance

This model provides comprehensive security event monitoring and alerting
required for FedRAMP SI-4 (Information System Monitoring):
- Real-time security event detection
- Event classification and severity assessment
- Alert generation and management
- Investigation status tracking
- Threat intelligence correlation

Events are captured from multiple sources including:
- Audit logs
- System logs
- Network monitoring
- Application security events
- Behavioral analytics
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Float,
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


class SecurityEventType(str, Enum):
    """Types of security events for categorization"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_VIOLATION = "authorization_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE_DETECTED = "malware_detected"
    INTRUSION_ATTEMPT = "intrusion_attempt"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DENIAL_OF_SERVICE = "denial_of_service"
    CONFIGURATION_CHANGE = "configuration_change"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    THREAT_INTELLIGENCE_MATCH = "threat_intelligence_match"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"
    SYSTEM_COMPROMISE = "system_compromise"
    NETWORK_ANOMALY = "network_anomaly"
    APPLICATION_ERROR = "application_error"
    OTHER = "other"


class EventSeverity(str, Enum):
    """Severity levels for security events"""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status of security alerts"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"


class InvestigationStatus(str, Enum):
    """Status of event investigation"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    CLOSED = "closed"


class SecurityEvent(Base):
    """
    Security event table for FedRAMP SI-4 compliance.
    
    Captures security events from multiple sources and provides:
    - Real-time event detection
    - Event classification and severity assessment
    - Alert generation
    - Investigation tracking
    - Threat intelligence correlation
    """
    __tablename__ = "security_events"
    __table_args__ = (
        # Indexes for common query patterns
        Index('idx_security_event_timestamp', 'timestamp'),
        Index('idx_security_event_type', 'event_type'),
        Index('idx_security_event_severity', 'severity'),
        Index('idx_security_event_org', 'org_id', 'timestamp'),
        Index('idx_security_event_user', 'user_id', 'timestamp'),
        Index('idx_security_event_alert_status', 'alert_status'),
        Index('idx_security_event_investigation', 'investigation_status'),
        Index('idx_security_event_source', 'source'),
        Index('idx_security_event_ip', 'ip_address'),
        Index('idx_security_event_correlation', 'correlation_id'),
        # Composite indexes for dashboard queries
        Index('idx_security_event_dashboard', 'org_id', 'severity', 'alert_status', 'timestamp'),
        Index('idx_security_event_active_alerts', 'org_id', 'alert_status', 'severity'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Organization and User context
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
    
    # Event classification
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    severity = Column(
        String(20),
        nullable=False,
        index=True,
        default=EventSeverity.INFORMATIONAL.value,
    )
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)  # audit_log, siem, behavioral_analytics, etc.
    source_id = Column(String(255), nullable=True)  # ID of the source event/log
    
    # Request context
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(1000), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    device_id = Column(String(255), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Resource context
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    
    # Alert management
    alert_generated = Column(Boolean, default=False, nullable=False, index=True)
    alert_status = Column(
        String(20),
        nullable=True,
        index=True,
    )  # new, acknowledged, investigating, resolved, etc.
    alert_id = Column(String(255), nullable=True, index=True)  # Reference to alert system
    alert_acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    alert_acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Investigation status
    investigation_status = Column(
        String(20),
        nullable=True,
        index=True,
    )  # not_started, in_progress, completed, closed
    investigation_notes = Column(Text, nullable=True)
    investigation_assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    investigation_started_at = Column(DateTime(timezone=True), nullable=True)
    investigation_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Threat intelligence correlation
    threat_intelligence_matched = Column(Boolean, default=False, nullable=False)
    threat_indicators = Column(JSON, nullable=True)  # List of matched threat indicators
    threat_feed_sources = Column(JSON, nullable=True)  # Sources of threat intelligence
    
    # Behavioral analytics correlation
    behavioral_anomaly_detected = Column(Boolean, default=False, nullable=False)
    behavioral_risk_score = Column(Float, nullable=True)  # Risk score from behavioral analytics
    behavioral_anomaly_type = Column(String(100), nullable=True)  # Type of behavioral anomaly
    
    # Event correlation
    correlation_id = Column(String(255), nullable=True, index=True)  # For correlating related events
    related_event_ids = Column(JSON, nullable=True)  # List of related event IDs
    
    # Additional metadata
    raw_event_data = Column(JSON, nullable=True)  # Original event data from source
    normalized_data = Column(JSON, nullable=True)  # Normalized event data
    metadata = Column(JSON, nullable=True)  # Additional flexible metadata
    
    # Compliance fields
    classification = Column(String(50), nullable=True)  # PHI, NON_PHI, PII, etc.
    training_mode = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    org = relationship("Organization", lazy="select")
    acknowledged_by_user = relationship("User", foreign_keys=[alert_acknowledged_by], lazy="select")
    investigation_assigned_user = relationship("User", foreign_keys=[investigation_assigned_to], lazy="select")
    
    def __repr__(self):
        return (
            f"<SecurityEvent(id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"event_type={self.event_type}, "
            f"severity={self.severity}, "
            f"alert_status={self.alert_status})>"
        )


class SecurityAlert(Base):
    """
    Security alert table for managing alerts generated from security events.
    
    Provides alert lifecycle management and notification tracking.
    """
    __tablename__ = "security_alerts"
    __table_args__ = (
        Index('idx_alert_status_severity', 'status', 'severity'),
        Index('idx_alert_org_status', 'org_id', 'status'),
        Index('idx_alert_created', 'created_at'),
        Index('idx_alert_event', 'event_id'),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization context
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Related security event
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(
        String(20),
        nullable=False,
        index=True,
    )
    
    # Alert status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        default=AlertStatus.NEW.value,
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Notification tracking
    notifications_sent = Column(JSON, nullable=True)  # List of notification channels and timestamps
    escalation_level = Column(Integer, default=0, nullable=False)  # Escalation level
    
    # Additional metadata
    tags = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Compliance fields
    classification = Column(String(50), nullable=True)
    training_mode = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    event = relationship("SecurityEvent", lazy="select")
    assigned_user = relationship("User", foreign_keys=[assigned_to], lazy="select")
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by], lazy="select")
    
    def __repr__(self):
        return (
            f"<SecurityAlert(id={self.id}, "
            f"event_id={self.event_id}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )
