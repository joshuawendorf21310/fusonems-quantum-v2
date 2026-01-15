from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    severity = Column(String, default="Medium")
    message = Column(Text, nullable=False)
    status = Column(String, default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccessAudit(Base):
    __tablename__ = "access_audits"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    outcome = Column(String, default="Allowed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
