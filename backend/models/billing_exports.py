from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class ClaimSubmission(Base):
    __tablename__ = "claim_submissions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False, index=True)
    clearinghouse = Column(String, default="OfficeAlly")
    edi_version = Column(String, default="005010X222A1")
    status = Column(String, default="queued")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RemittanceAdvice(Base):
    __tablename__ = "remittance_advice"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    payer = Column(String, nullable=False)
    claim_reference = Column(String, default="")
    status = Column(String, default="received")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClearinghouseAck(Base):
    __tablename__ = "clearinghouse_acks"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    ack_type = Column(String, default="999")
    reference = Column(String, default="")
    status = Column(String, default="accepted")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    payer = Column(String, default="")
    status = Column(String, default="pending")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClaimStatusInquiry(Base):
    __tablename__ = "claim_status_inquiries"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    claim_reference = Column(String, default="")
    status = Column(String, default="pending")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PatientStatement(Base):
    __tablename__ = "patient_statements"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    balance_due = Column(String, default="0")
    status = Column(String, default="queued")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentPosting(Base):
    __tablename__ = "payment_postings"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    source = Column(String, default="manual")
    amount = Column(String, default="0")
    status = Column(String, default="posted")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppealPacket(Base):
    __tablename__ = "appeal_packets"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    claim_reference = Column(String, default="")
    status = Column(String, default="draft")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
