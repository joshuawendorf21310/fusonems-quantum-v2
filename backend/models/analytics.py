from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class AnalyticsMetric(Base):
    __tablename__ = "analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    metric_key = Column(String, nullable=False, index=True)
    metric_value = Column(String, nullable=False)
    window = Column(String, default="24h")
    tags = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    event_key = Column(String, nullable=False, index=True)
    module_key = Column(String, nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
