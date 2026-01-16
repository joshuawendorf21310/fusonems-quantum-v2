from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class PwaDistribution(Base):
    __tablename__ = "pwa_distributions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    platform = Column(String, default="web")
    current_version = Column(String, default="")
    pending_version = Column(String, default="")
    status = Column(String, default="enabled")
    rules = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    plan_name = Column(String, nullable=False)
    status = Column(String, default="active")
    pricing = Column(JSON, nullable=False, default=dict)
    limits = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IncidentCommand(Base):
    __tablename__ = "incident_commands"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, default="open")
    severity = Column(String, default="medium")
    summary = Column(String, default="")
    actions = Column(JSON, nullable=False, default=list)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DataGovernanceRule(Base):
    __tablename__ = "data_governance_rules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    rule_type = Column(String, default="retention")
    status = Column(String, default="active")
    settings = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
