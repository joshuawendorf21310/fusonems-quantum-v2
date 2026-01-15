from sqlalchemy import Column, DateTime, Integer, JSON, String, func

from core.database import Base


class InvestorMetric(Base):
    __tablename__ = "investor_metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    context = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
