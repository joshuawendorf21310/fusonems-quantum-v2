from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    action = Column(String, nullable=False)
    status = Column(String, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    status = Column(String, default="Open")
    priority = Column(String, default="Normal")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
