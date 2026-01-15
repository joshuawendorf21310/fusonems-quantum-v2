from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, func

from core.database import Base


class AiInsight(Base):
    __tablename__ = "ai_console_insights"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
