from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class CommsProvider(Base):
    __tablename__ = "comms_providers"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    provider_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String, default="active")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsTemplate(Base):
    __tablename__ = "comms_templates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    channel = Column(String, default="email")
    subject = Column(String, default="")
    body = Column(String, default="")
    meta_data = Column("metadata", JSON, default=dict)
    status = Column(String, default="active")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsEvent(Base):
    __tablename__ = "comms_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("comms_messages.id"), nullable=True)
    thread_id = Column(Integer, ForeignKey("comms_threads.id"), nullable=True)
    event_type = Column(String, nullable=False)
    status = Column(String, default="queued")
    payload = Column(JSON, default=dict)
    error = Column(String, default="")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsDeliveryAttempt(Base):
    __tablename__ = "comms_delivery_attempts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("comms_events.id"), nullable=False, index=True)
    provider = Column(String, default="")
    status = Column(String, default="pending")
    response_payload = Column(JSON, default=dict)
    error = Column(String, default="")
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
