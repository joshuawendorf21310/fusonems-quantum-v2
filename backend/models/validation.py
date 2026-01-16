from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class DataValidationIssue(Base):
    __tablename__ = "data_validation_issues"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    severity = Column(String, default="Medium")
    issue = Column(Text, nullable=False)
    status = Column(String, default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    rule_type = Column(String, default="required_field")
    field = Column(String, default="")
    condition = Column(JSON, default=dict)
    severity = Column(String, default="High")
    enforcement = Column(String, default="hard_block")
    status = Column(String, default="active")
    version = Column(String, default="v1")
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
