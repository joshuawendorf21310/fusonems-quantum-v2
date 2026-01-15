from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class DataValidationIssue(Base):
    __tablename__ = "data_validation_issues"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    severity = Column(String, default="Medium")
    issue = Column(Text, nullable=False)
    status = Column(String, default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
