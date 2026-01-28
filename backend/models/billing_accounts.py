import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    customer_type = Column(String, default="agency")
    display_name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
    external_refs = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False, index=True)
    customer_id = Column(String, ForeignKey("billing_customers.id"), nullable=False)
    encounter_id = Column(String, default="")
    mission_id = Column(String, default="")
    transport_id = Column(String, default="")
    status = Column(String, default="DRAFT")
    currency = Column(String, default="usd")
    subtotal = Column(Integer, default=0)
    tax = Column(Integer, default=0)
    total = Column(Integer, default=0)
    amount_paid = Column(Integer, default=0)
    amount_due = Column(Integer, default=0)
    due_date = Column(DateTime(timezone=True))
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BillingInvoiceLine(Base):
    __tablename__ = "billing_invoice_lines"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    description = Column(String, default="")
    code = Column(String, default="")
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    amount = Column(Integer, default=0)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingPayment(Base):
    __tablename__ = "billing_payments"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("billing_invoices.id"), nullable=False, index=True)
    provider = Column(String, default="stripe")
    provider_payment_id = Column(String, default="")
    amount = Column(Integer, default=0)
    status = Column(String, default="initiated")
    method = Column(String, default="card")
    received_at = Column(DateTime(timezone=True))
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingLedgerEntry(Base):
    __tablename__ = "billing_ledger_entries"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    entry_type = Column(String, default="debit")
    account = Column(String, default="AR")
    amount = Column(Integer, default=0)
    currency = Column(String, default="usd")
    reference_type = Column(String, default="")
    reference_id = Column(String, default="")
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingWebhookReceipt(Base):
    __tablename__ = "billing_webhook_receipts"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    provider = Column(String, default="stripe")
    event_id = Column(String, nullable=False, index=True, unique=True)
    event_type = Column(String, default="")
    signature_valid = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    processing_status = Column(String, default="processed")
    payload_hash = Column(String, default="")
    payload_json = Column(JSON, default=dict)
    error = Column(String, default="")
