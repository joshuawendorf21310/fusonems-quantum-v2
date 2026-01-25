from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    schema_name = Column(String, default="public")
    training_mode = Column(Boolean, default=False)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    actor_id = Column(String, nullable=True)
    actor_role = Column(String, default="")
    device_id = Column(String, default="")
    server_time = Column(DateTime(timezone=True), server_default=func.now())
    drift_seconds = Column(Integer, default=0)
    drifted = Column(Boolean, default=False)
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
