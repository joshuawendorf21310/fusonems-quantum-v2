from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from core.database import Base


class PaymentPlanTier(str, Enum):
    SHORT_TERM = "short_term"
    STANDARD = "standard"
    EXTENDED = "extended"


class PaymentPlanStatus(str, Enum):
    PENDING_ACCEPTANCE = "pending_acceptance"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CARD = "card"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"


class InsuranceClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    PENDING = "pending"
    PAID = "paid"
    DENIED = "denied"
    APPEALED = "appealed"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_DENIED = "appeal_denied"
    EXHAUSTED = "exhausted"


class DenialReason(str, Enum):
    MISSING_INFO = "missing_info"
    NOT_COVERED = "not_covered"
    OUT_OF_NETWORK = "out_of_network"
    COORDINATION_OF_BENEFITS = "coordination_of_benefits"
    MEDICAL_NECESSITY = "medical_necessity"
    TIMELY_FILING = "timely_filing"
    OTHER = "other"


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("collections_accounts.id"), nullable=False)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    tier = Column(SQLEnum(PaymentPlanTier), nullable=False)
    status = Column(SQLEnum(PaymentPlanStatus), default=PaymentPlanStatus.PENDING_ACCEPTANCE)
    
    total_balance = Column(Float, nullable=False)
    down_payment = Column(Float, default=0.0)
    financed_amount = Column(Float, nullable=False)
    
    installment_amount = Column(Float, nullable=False)
    number_of_installments = Column(Integer, nullable=False)
    
    frequency = Column(String, default="monthly")
    first_payment_date = Column(Date, nullable=False)
    
    auto_pay_enabled = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_payment_method_id = Column(String, nullable=True)
    payment_method_type = Column(SQLEnum(PaymentMethod), nullable=True)
    
    payments_made = Column(Integer, default=0)
    total_paid = Column(Float, default=0.0)
    remaining_balance = Column(Float, nullable=False)
    
    missed_payments = Column(Integer, default=0)
    last_payment_date = Column(Date, nullable=True)
    next_payment_date = Column(Date, nullable=True)
    
    offered_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    ai_selected_tier = Column(Boolean, default=True)
    tier_selection_rationale = Column(Text, nullable=True)
    
    patient_facing_language = Column(Text, nullable=True)
    
    governance_version = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    installments = relationship("PaymentPlanInstallment", back_populates="plan", cascade="all, delete-orphan")


class PaymentPlanInstallment(Base):
    __tablename__ = "payment_plan_installments"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("payment_plans.id"), nullable=False)
    
    installment_number = Column(Integer, nullable=False)
    amount_due = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    
    paid = Column(Boolean, default=False)
    paid_amount = Column(Float, default=0.0)
    paid_date = Column(Date, nullable=True)
    
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    
    auto_charge_attempted = Column(Boolean, default=False)
    auto_charge_success = Column(Boolean, nullable=True)
    auto_charge_failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    plan = relationship("PaymentPlan", back_populates="installments")


class InsuranceFollowUp(Base):
    __tablename__ = "insurance_follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("billing_claims.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("collections_accounts.id"), nullable=True)
    
    claim_status = Column(SQLEnum(InsuranceClaimStatus), nullable=False)
    
    submitted_at = Column(DateTime, nullable=True)
    last_follow_up_at = Column(DateTime, nullable=True)
    next_follow_up_at = Column(DateTime, nullable=True)
    
    follow_up_count = Column(Integer, default=0)
    
    payer_name = Column(String, nullable=True)
    payer_response = Column(Text, nullable=True)
    
    missing_information = Column(JSON, default=list)
    requested_documentation = Column(JSON, default=list)
    
    denial_reason = Column(SQLEnum(DenialReason), nullable=True)
    denial_details = Column(Text, nullable=True)
    denial_received_at = Column(DateTime, nullable=True)
    
    appealable = Column(Boolean, nullable=True)
    appeal_deadline = Column(Date, nullable=True)
    appeal_prepared = Column(Boolean, default=False)
    appeal_submitted = Column(Boolean, default=False)
    appeal_submitted_at = Column(DateTime, nullable=True)
    
    patient_collections_paused = Column(Boolean, default=True)
    pause_reason = Column(String, default="Insurance pending")
    
    responsibility_exhausted = Column(Boolean, default=False)
    transitioned_to_patient = Column(Boolean, default=False)
    transition_date = Column(DateTime, nullable=True)
    
    ai_managed = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DenialAppeal(Base):
    __tablename__ = "denial_appeals"

    id = Column(Integer, primary_key=True, index=True)
    follow_up_id = Column(Integer, ForeignKey("insurance_follow_ups.id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("billing_claims.id"), nullable=False)
    
    denial_reason = Column(SQLEnum(DenialReason), nullable=False)
    appeal_rationale = Column(Text, nullable=False)
    
    supporting_documentation = Column(JSON, default=list)
    missing_elements = Column(JSON, default=list)
    
    ai_prepared = Column(Boolean, default=True)
    ai_recommendation = Column(Text, nullable=True)
    
    founder_reviewed = Column(Boolean, default=False)
    founder_approved = Column(Boolean, nullable=True)
    founder_notes = Column(Text, nullable=True)
    
    submitted = Column(Boolean, default=False)
    submitted_at = Column(DateTime, nullable=True)
    
    appeal_deadline = Column(Date, nullable=False)
    
    outcome = Column(String, nullable=True)
    outcome_received_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class StripePaymentRecord(Base):
    __tablename__ = "stripe_payment_records"

    id = Column(Integer, primary_key=True, index=True)
    
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("payment_plans.id"), nullable=True)
    installment_id = Column(Integer, ForeignKey("payment_plan_installments.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    stripe_payment_intent_id = Column(String, unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd")
    
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_method_details = Column(JSON, nullable=True)
    
    stripe_fee = Column(Float, nullable=True)
    net_amount = Column(Float, nullable=True)
    
    status = Column(String, nullable=False)
    success = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    
    auto_charge = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    meta_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BillingPerformanceKPI(Base):
    __tablename__ = "billing_performance_kpis"

    id = Column(Integer, primary_key=True, index=True)
    
    period = Column(String, nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    total_charges_billed = Column(Float, default=0.0)
    total_payments_collected = Column(Float, default=0.0)
    net_outstanding_balance = Column(Float, default=0.0)
    
    collection_rate = Column(Float, default=0.0)
    average_days_to_pay = Column(Float, default=0.0)
    
    payment_success_rate = Column(Float, default=0.0)
    payment_failure_rate = Column(Float, default=0.0)
    
    balances_on_payment_plans_count = Column(Integer, default=0)
    balances_on_payment_plans_amount = Column(Float, default=0.0)
    
    writeoff_volume_count = Column(Integer, default=0)
    writeoff_volume_amount = Column(Float, default=0.0)
    
    card_payment_count = Column(Integer, default=0)
    card_payment_amount = Column(Float, default=0.0)
    card_success_rate = Column(Float, default=0.0)
    card_average_fee = Column(Float, default=0.0)
    
    ach_payment_count = Column(Integer, default=0)
    ach_payment_amount = Column(Float, default=0.0)
    ach_success_rate = Column(Float, default=0.0)
    ach_average_fee = Column(Float, default=0.0)
    
    insurance_follow_ups_active = Column(Integer, default=0)
    insurance_denials_count = Column(Integer, default=0)
    insurance_appeals_count = Column(Integer, default=0)
    
    ai_explanation = Column(Text, nullable=True)
    kpi_changes = Column(JSON, default=list)
    optimization_recommendations = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PaymentOptimizationRule(Base):
    __tablename__ = "payment_optimization_rules"

    id = Column(Integer, primary_key=True, index=True)
    
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    
    enabled = Column(Boolean, default=True)
    
    conditions = Column(JSON, nullable=False)
    action = Column(JSON, nullable=False)
    
    rationale = Column(Text, nullable=False)
    
    times_triggered = Column(Integer, default=0)
    times_successful = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
