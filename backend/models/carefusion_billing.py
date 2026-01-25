import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, func

from core.database import TelehealthBase


def _uuid() -> str:
    return str(uuid.uuid4())


class CarefusionLedgerEntry(TelehealthBase):
    __tablename__ = "carefusion_ledger_entries"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(Integer, nullable=False, index=True)
    entry_type = Column(String, default="debit")
    account = Column(String, default="telehealth_ar")
    amount = Column(Integer, default=0)
    currency = Column(String, default="usd")
    reference_type = Column(String, default="")
    reference_id = Column(String, default="")
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CarefusionClaim(TelehealthBase):
    __tablename__ = "carefusion_claims"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String, default="", index=True)
    payer = Column(String, nullable=False)
    status = Column(String, default="draft")
    submission_reference = Column(String, default="")
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CarefusionPayerRouting(TelehealthBase):
    __tablename__ = "carefusion_payer_routing"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(Integer, nullable=False, index=True)
    payer = Column(String, nullable=False)
    route = Column(String, nullable=False)
    rules = Column(JSON, default=dict)
    status = Column(String, default="active")
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CarefusionAuditEvent(TelehealthBase):
    __tablename__ = "carefusion_audit_events"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(Integer, nullable=False, index=True)
    actor = Column(String, default="system")
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    before_state = Column(JSON, default=dict)
    after_state = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
