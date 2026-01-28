from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func

from core.database import Base


class PatientPortalAccount(Base):
    __tablename__ = "patient_portal_accounts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    address = Column(Text, default="")
    status = Column(String, default="active")
    preferences = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PatientPortalMessage(Base):
    __tablename__ = "patient_portal_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False)
    sender = Column(String, default="patient")
    message = Column(String, nullable=False)
    status = Column(String, default="new")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PatientBill(Base):
    __tablename__ = "patient_bills"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False, index=True)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    bill_number = Column(String, nullable=False, unique=True, index=True)
    transport_date = Column(DateTime(timezone=True), nullable=False)
    service_type = Column(String, nullable=False)
    pickup_address = Column(Text, default="")
    dropoff_address = Column(Text, default="")
    amount_total = Column(Numeric(12, 2), nullable=False)
    amount_insurance = Column(Numeric(12, 2), default=0)
    amount_patient = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), default=0)
    amount_due = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="pending")
    due_date = Column(DateTime(timezone=True), nullable=True)
    insurance_claim_status = Column(String, default="pending")
    notes = Column(Text, default="")
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PatientPayment(Base):
    __tablename__ = "patient_payments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False, index=True)
    bill_id = Column(Integer, ForeignKey("patient_bills.id"), nullable=False, index=True)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    payment_id = Column(String, nullable=False, unique=True, index=True)
    stripe_payment_intent_id = Column(String, unique=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="pending")
    payment_method = Column(String, default="card")
    payment_method_brand = Column(String, default="")
    payment_method_last4 = Column(String, default="")
    failure_reason = Column(Text, default="")
    receipt_url = Column(String, default="")
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PatientPaymentPlan(Base):
    __tablename__ = "patient_payment_plans"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False, index=True)
    bill_id = Column(Integer, ForeignKey("patient_bills.id"), nullable=False, index=True)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    plan_id = Column(String, nullable=False, unique=True, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), default=0)
    amount_remaining = Column(Numeric(12, 2), nullable=False)
    installment_amount = Column(Numeric(12, 2), nullable=False)
    frequency = Column(String, default="monthly")
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active")
    auto_pay_enabled = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StripeCustomer(Base):
    __tablename__ = "stripe_customers"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("patient_portal_accounts.id"), nullable=False, unique=True, index=True)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, default="")
    name = Column(String, default="")
    default_payment_method = Column(String, default="")
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
