from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from core.database import Base


class NotificationType(str, Enum):
    INCIDENT_DISPATCHED = "incident.dispatched"
    INCIDENT_UPDATED = "incident.updated"
    CALL_RECEIVED = "call.received"
    MESSAGE_RECEIVED = "message.received"
    PAYMENT_FAILED = "payment.failed"
    PATIENT_ALERT = "patient.alert"
    SYSTEM_ALERT = "system.alert"
    COMPLIANCE_REMINDER = "compliance.reminder"
    TASK_ASSIGNED = "task.assigned"
    DOCUMENT_READY = "document.ready"
    NEMSIS_UPDATE = "compliance.nemsis_update"


class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class InAppNotification(Base):
    __tablename__ = "in_app_notifications"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    severity = Column(SQLEnum(NotificationSeverity), default=NotificationSeverity.INFO)
    
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    linked_resource_type = Column(String(50), nullable=True)
    linked_resource_id = Column(Integer, nullable=True)
    
    metadata_payload = Column("metadata", JSON, nullable=True)
    
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    training_mode = Column(Boolean, default=False)
    
    user = relationship("User", foreign_keys=[user_id])
    org = relationship("Organization", foreign_keys=[org_id])


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    
    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end = Column(String(5), nullable=True)
    
    critical_override = Column(Boolean, default=True)
    
    notification_settings = Column(JSON, nullable=True, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id])
    org = relationship("Organization", foreign_keys=[org_id])
