from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="LEGAL_HOLD")
    training_mode = Column(Boolean, default=False)
    category = Column(String, nullable=False)
    severity = Column(String, default="Medium")
    message = Column(Text, nullable=False)
    status = Column(String, default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccessAudit(Base):
    __tablename__ = "access_audits"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="LEGAL_HOLD")
    training_mode = Column(Boolean, default=False)
    user_email = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    outcome = Column(String, default="Allowed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ForensicAuditLog(Base):
    __tablename__ = "forensic_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="LEGAL_HOLD")
    training_mode = Column(Boolean, default=False)
    actor_email = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    reason_code = Column(String, default="")
    decision_id = Column(String, default="")
    reasoning_component = Column(String, default="")
    reasoning_version = Column(String, default="")
    method_used = Column(String, default="")
    input_hash = Column(String, default="")
    output_hash = Column(String, default="")
    decision_packet = Column(JSON, nullable=True)
    device_fingerprint = Column(String, default="")
    ip_address = Column(String, default="")
    session_id = Column(String, default="")
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    outcome = Column(String, default="Allowed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
