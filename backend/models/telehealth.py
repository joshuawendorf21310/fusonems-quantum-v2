from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from core.database import TelehealthBase


class TelehealthSession(TelehealthBase):
    __tablename__ = "telehealth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    host_name = Column(String, nullable=False)
    access_code = Column(String, nullable=False)
    session_secret = Column(String, nullable=False)
    status = Column(String, default="Scheduled")
    modality = Column(String, default="video")
    recording_enabled = Column(Boolean, default=True)
    encryption_state = Column(String, default="secure")
    consent_required = Column(Boolean, default=True)
    consent_captured_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TelehealthParticipant(TelehealthBase):
    __tablename__ = "telehealth_participants"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="patient")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class TelehealthMessage(TelehealthBase):
    __tablename__ = "telehealth_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
