from sqlalchemy import Column, DateTime, Integer, JSON, String, func

from core.database import Base


class BusinessOpsTask(Base):
    __tablename__ = "business_ops_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    priority = Column(String, default="Normal")
    task_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
