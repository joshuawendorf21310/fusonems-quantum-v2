import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class BillingInvoiceItem(Base):
    __tablename__ = "billing_invoice_items"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    description = Column(String, nullable=False)
    code = Column(String, default="")
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    amount = Column(Integer, default=0)
    meta_data = Column("metadata", JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingInvoiceEvent(Base):
    __tablename__ = "billing_invoice_events"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    from_status = Column(String, default="")
    to_status = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingClaim(Base):
    __tablename__ = "billing_claims"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    payer = Column(String, nullable=False)
    status = Column(String, default="draft")
    submission_reference = Column(String, default="")
    payload = Column(JSON, default=dict)
    submitted_at = Column(DateTime(timezone=True))
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingClaimEvent(Base):
    __tablename__ = "billing_claim_events"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    claim_id = Column(String, ForeignKey("billing_claims.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    from_status = Column(String, default="")
    to_status = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingPaymentEvent(Base):
    __tablename__ = "billing_payment_events"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    payment_id = Column(String, ForeignKey("billing_payments.id"), nullable=True, index=True)
    provider = Column(String, default="stripe")
    provider_event_id = Column(String, nullable=False, index=True, unique=True)
    event_type = Column(String, default="")
    status = Column(String, default="received")
    payload = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    last_error = Column(String, default="")
    classification = Column(String, default="BILLING_SENSITIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingDenial(Base):
    __tablename__ = "billing_denials"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    claim_id = Column(String, ForeignKey("billing_claims.id"), nullable=False, index=True)
    reason = Column(String, nullable=False)
    status = Column(String, default="open")
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingAppeal(Base):
    __tablename__ = "billing_appeals"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    denial_id = Column(String, ForeignKey("billing_denials.id"), nullable=False, index=True)
    status = Column(String, default="draft")
    payload = Column(JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingFacility(Base):
    __tablename__ = "billing_facilities"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    npi = Column(String, default="")
    address = Column(String, default="")
    status = Column(String, default="active")
    meta_data = Column("metadata", JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingContact(Base):
    __tablename__ = "billing_contacts"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    facility_id = Column(String, ForeignKey("billing_facilities.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
    role = Column(String, default="")
    status = Column(String, default="active")
    meta_data = Column("metadata", JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingContactAttempt(Base):
    __tablename__ = "billing_contact_attempts"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("billing_contacts.id"), nullable=False, index=True)
    channel = Column(String, default="email")
    status = Column(String, default="queued")
    payload = Column(JSON, default=dict)
    attempted_at = Column(DateTime(timezone=True))
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingPatientAccount(Base):
    __tablename__ = "billing_patient_accounts"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
    status = Column(String, default="active")
    portal_token_hash = Column(String, default="")
    portal_token_expires_at = Column(DateTime(timezone=True))
    meta_data = Column("metadata", JSON, default=dict)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingDocument(Base):
    __tablename__ = "billing_documents"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=True, index=True)
    payment_id = Column(String, ForeignKey("billing_payments.id"), nullable=True, index=True)
    doc_type = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    file_name = Column(String, default="")
    content_type = Column(String, default="application/pdf")
    checksum = Column(String, default="")
    meta_data = Column("metadata", JSON, default=dict)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingPortalToken(Base):
    __tablename__ = "billing_portal_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_account_id = Column(String, ForeignKey("billing_patient_accounts.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, index=True, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    classification = Column(String, default="PHI")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
