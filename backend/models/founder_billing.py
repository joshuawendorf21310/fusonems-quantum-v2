from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from core.database import Base


class StatementLifecycleState(str, Enum):
    DRAFTED = "drafted"
    FINALIZED = "finalized"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    PAID = "paid"
    ESCALATED = "escalated"
    FAILED = "failed"


class DeliveryChannel(str, Enum):
    EMAIL = "email"
    PHYSICAL_MAIL = "physical_mail"
    SMS = "sms"
    PATIENT_PORTAL = "patient_portal"


class AIActionType(str, Enum):
    STATEMENT_GENERATED = "statement_generated"
    STATEMENT_FINALIZED = "statement_finalized"
    STATEMENT_SENT = "statement_sent"
    CHANNEL_SELECTED = "channel_selected"
    ESCALATION_TRIGGERED = "escalation_triggered"
    FOLLOW_UP_SENT = "follow_up_sent"
    PAYMENT_PLAN_OFFERED = "payment_plan_offered"


class PatientStatement(Base):
    __tablename__ = "patient_statements"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True)
    
    statement_number = Column(String, unique=True, nullable=False, index=True)
    statement_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    
    total_charges = Column(Float, nullable=False)
    insurance_paid = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)
    patient_responsibility = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    balance_due = Column(Float, nullable=False)
    
    lifecycle_state = Column(SQLEnum(StatementLifecycleState), default=StatementLifecycleState.DRAFTED)
    
    ai_generated = Column(Boolean, default=True)
    ai_approved_at = Column(DateTime, nullable=True)
    founder_override = Column(Boolean, default=False)
    founder_override_reason = Column(Text, nullable=True)
    
    itemized_charges = Column(JSON, nullable=True)
    payment_history = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    deliveries = relationship("StatementDelivery", back_populates="statement", cascade="all, delete-orphan")
    audit_logs = relationship("BillingAuditLog", back_populates="statement", cascade="all, delete-orphan")
    escalations = relationship("StatementEscalation", back_populates="statement", cascade="all, delete-orphan")


class StatementDelivery(Base):
    __tablename__ = "statement_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=False)
    
    channel = Column(SQLEnum(DeliveryChannel), nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    
    success = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    
    email_address = Column(String, nullable=True)
    postmark_message_id = Column(String, nullable=True, index=True)
    
    physical_address = Column(JSON, nullable=True)
    lob_mail_id = Column(String, nullable=True, index=True)
    lob_tracking_events = Column(JSON, default=list)
    
    sms_phone_number = Column(String, nullable=True)
    twilio_message_sid = Column(String, nullable=True)
    
    ai_selected_channel = Column(Boolean, default=True)
    channel_selection_reason = Column(Text, nullable=True)
    
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    statement = relationship("PatientStatement", back_populates="deliveries")
    audit_logs = relationship("BillingAuditLog", back_populates="delivery", cascade="all, delete-orphan")


class BillingAuditLog(Base):
    __tablename__ = "billing_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=True)
    delivery_id = Column(Integer, ForeignKey("statement_deliveries.id"), nullable=True)
    
    action_type = Column(SQLEnum(AIActionType), nullable=False)
    action_description = Column(Text, nullable=False)
    
    executed_by = Column(String, default="AI Agent under Founder billing authority")
    founder_override = Column(Boolean, default=False)
    
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=True)
    
    meta_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    statement = relationship("PatientStatement", back_populates="audit_logs")
    delivery = relationship("StatementDelivery", back_populates="audit_logs")


class StatementEscalation(Base):
    __tablename__ = "statement_escalations"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=False)
    
    escalation_level = Column(Integer, default=1)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    triggered_by = Column(String, default="AI Agent")
    
    trigger_reason = Column(Text, nullable=False)
    days_overdue = Column(Integer, nullable=False)
    
    action_taken = Column(Text, nullable=False)
    next_escalation_at = Column(DateTime, nullable=True)
    
    payment_plan_offered = Column(Boolean, default=False)
    payment_plan_terms = Column(JSON, nullable=True)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_method = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    statement = relationship("PatientStatement", back_populates="escalations")


class LobMailJob(Base):
    __tablename__ = "lob_mail_jobs"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("statement_deliveries.id"), nullable=False)
    
    lob_letter_id = Column(String, unique=True, nullable=False, index=True)
    lob_url = Column(String, nullable=True)
    
    to_address = Column(JSON, nullable=False)
    from_address = Column(JSON, nullable=False)
    
    pdf_url = Column(String, nullable=True)
    expected_delivery_date = Column(DateTime, nullable=True)
    
    mail_type = Column(String, default="usps_first_class")
    color = Column(Boolean, default=True)
    double_sided = Column(Boolean, default=True)
    
    tracking_number = Column(String, nullable=True, index=True)
    tracking_events = Column(JSON, default=list)
    
    status = Column(String, nullable=True)
    send_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    
    cost = Column(Float, nullable=True)
    
    address_validated = Column(Boolean, default=False)
    address_validation_result = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoleBillerConfig(Base):
    __tablename__ = "sole_biller_config"

    id = Column(Integer, primary_key=True, index=True)
    
    enabled = Column(Boolean, default=False)
    founder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    ai_autonomous_approval_threshold = Column(Float, default=500.0)
    require_founder_approval_above = Column(Float, nullable=True)
    
    auto_send_statements = Column(Boolean, default=True)
    auto_escalate_overdue = Column(Boolean, default=True)
    auto_offer_payment_plans = Column(Boolean, default=True)
    
    preferred_channel_order = Column(JSON, default=["email", "physical_mail", "sms"])
    email_failover_to_mail = Column(Boolean, default=True)
    failover_delay_hours = Column(Integer, default=48)
    
    escalation_schedule_days = Column(JSON, default=[30, 60, 90])
    payment_plan_min_balance = Column(Float, default=200.0)
    payment_plan_max_months = Column(Integer, default=12)
    
    hard_boundaries = Column(JSON, default={
        "cannot_alter_balances": True,
        "cannot_modify_clinical_docs": True,
        "cannot_submit_legal_filings": True,
        "cannot_forgive_balances_without_config": True
    })
    
    lob_api_key = Column(String, nullable=True)
    postmark_api_key = Column(String, nullable=True)
    twilio_account_sid = Column(String, nullable=True)
    twilio_auth_token = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIBillingDecision(Base):
    __tablename__ = "ai_billing_decisions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=True)
    
    decision_type = Column(String, nullable=False)
    decision_rationale = Column(Text, nullable=False)
    
    confidence_score = Column(Float, nullable=False)
    risk_assessment = Column(String, nullable=False)
    
    factors_considered = Column(JSON, default=list)
    alternative_actions = Column(JSON, default=list)
    
    auto_executed = Column(Boolean, default=False)
    requires_founder_approval = Column(Boolean, default=False)
    founder_approved = Column(Boolean, nullable=True)
    founder_approval_at = Column(DateTime, nullable=True)
    
    outcome = Column(String, nullable=True)
    outcome_metrics = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
