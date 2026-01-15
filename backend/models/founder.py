from sqlalchemy import Column, DateTime, Integer, JSON, String, func

from core.database import Base


class FounderMetric(Base):
    __tablename__ = "founder_metrics"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    value = Column(String, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
