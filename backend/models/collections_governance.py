from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from core.database import Base


class CollectionsPhase(str, Enum):
    INTERNAL = "internal"
    PRE_COLLECTIONS = "pre_collections"
    DECISION_REQUIRED = "decision_required"
    WRITTEN_OFF = "written_off"
    RESOLVED = "resolved"


class CollectionsAction(str, Enum):
    STATEMENT_SENT = "statement_sent"
    REMINDER_SENT = "reminder_sent"
    NOTICE_SENT = "notice_sent"
    FINAL_INTERNAL_NOTICE_SENT = "final_internal_notice_sent"
    ESCALATION_PAUSED = "escalation_paused"
    FLAGGED_FOR_DECISION = "flagged_for_decision"
    WRITTEN_OFF = "written_off"
    RESOLVED = "resolved"


class WriteOffReason(str, Enum):
    SMALL_BALANCE = "small_balance"
    COST_EXCEEDS_BALANCE = "cost_exceeds_balance"
    UNDELIVERABLE = "undeliverable"
    DECEASED_PATIENT = "deceased_patient"
    FOUNDER_DECISION = "founder_decision"


class CollectionsGovernancePolicy(Base):
    __tablename__ = "collections_governance_policy"

    id = Column(Integer, primary_key=True, index=True)
    
    version = Column(String, unique=True, nullable=False, index=True)
    version_date = Column(DateTime, default=datetime.utcnow)
    
    immutable = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    
    internal_collections_enabled = Column(Boolean, default=True)
    pre_collections_enabled = Column(Boolean, default=True)
    external_collections_enabled = Column(Boolean, default=False)
    credit_reporting_enabled = Column(Boolean, default=False)
    legal_action_enabled = Column(Boolean, default=False)
    
    escalation_day_0 = Column(Integer, default=0)
    escalation_day_15 = Column(Integer, default=15)
    escalation_day_30 = Column(Integer, default=30)
    escalation_day_60 = Column(Integer, default=60)
    escalation_day_90 = Column(Integer, default=90)
    
    pause_on_any_payment = Column(Boolean, default=True)
    reset_timeline_on_payment = Column(Boolean, default=True)
    
    small_balance_threshold = Column(Float, default=25.0)
    auto_writeoff_small_balances = Column(Boolean, default=False)
    
    write_off_requires_founder_approval = Column(Boolean, default=True)
    flag_for_decision_at_days = Column(Integer, default=90)
    
    final_internal_notice_template = Column(Text, nullable=False)
    
    prohibited_language = Column(JSON, default=list)
    
    ai_authority_statement = Column(Text, default="AI Agent under Founder billing authority (Wisconsin)")
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CollectionsAccount(Base):
    __tablename__ = "collections_accounts"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    current_phase = Column(SQLEnum(CollectionsPhase), default=CollectionsPhase.INTERNAL)
    
    original_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    total_paid = Column(Float, default=0.0)
    
    days_since_due = Column(Integer, default=0)
    
    escalation_paused = Column(Boolean, default=False)
    pause_reason = Column(Text, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    
    notices_sent = Column(Integer, default=0)
    last_notice_sent_at = Column(DateTime, nullable=True)
    
    delivery_proof = Column(JSON, default=list)
    
    flagged_for_founder_decision = Column(Boolean, default=False)
    flagged_at = Column(DateTime, nullable=True)
    founder_decision = Column(String, nullable=True)
    founder_decision_at = Column(DateTime, nullable=True)
    
    write_off_eligible = Column(Boolean, default=False)
    write_off_reason = Column(SQLEnum(WriteOffReason), nullable=True)
    written_off = Column(Boolean, default=False)
    written_off_at = Column(DateTime, nullable=True)
    write_off_amount = Column(Float, nullable=True)
    
    insurance_pending = Column(Boolean, default=False)
    payment_attempts = Column(Integer, default=0)
    
    communication_history = Column(JSON, default=list)
    
    governance_version = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    actions = relationship("CollectionsActionLog", back_populates="account", cascade="all, delete-orphan")


class CollectionsActionLog(Base):
    __tablename__ = "collections_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("collections_accounts.id"), nullable=False)
    
    action = Column(SQLEnum(CollectionsAction), nullable=False)
    action_description = Column(Text, nullable=False)
    
    executed_by = Column(String, default="AI Agent under Founder billing authority (Wisconsin)")
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    governance_version = Column(String, nullable=False)
    policy_reference = Column(String, nullable=True)
    
    balance_at_action = Column(Float, nullable=False)
    days_overdue_at_action = Column(Integer, nullable=False)
    
    notice_template_id = Column(Integer, ForeignKey("patient_statement_templates.id"), nullable=True)
    delivery_log_id = Column(Integer, ForeignKey("statement_delivery_logs.id"), nullable=True)
    
    reversible = Column(Boolean, default=True)
    reversed = Column(Boolean, default=False)
    reversed_at = Column(DateTime, nullable=True)
    
    extra_metadata = Column(JSON, default=dict)
    
    account = relationship("CollectionsAccount", back_populates="actions")


class CollectionsDecisionRequest(Base):
    __tablename__ = "collections_decision_requests"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("collections_accounts.id"), nullable=False)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    
    balance = Column(Float, nullable=False)
    days_overdue = Column(Integer, nullable=False)
    
    notices_sent_count = Column(Integer, nullable=False)
    delivery_proof_summary = Column(JSON, default=list)
    
    payment_attempts = Column(Integer, default=0)
    insurance_status = Column(String, nullable=True)
    
    communication_summary = Column(JSON, default=list)
    
    ai_recommendation = Column(String, nullable=True)
    ai_recommendation_rationale = Column(Text, nullable=True)
    
    founder_reviewed = Column(Boolean, default=False)
    founder_decision = Column(String, nullable=True)
    founder_decision_rationale = Column(Text, nullable=True)
    founder_decided_at = Column(DateTime, nullable=True)
    
    outcome = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class WriteOffRecord(Base):
    __tablename__ = "write_off_records"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("collections_accounts.id"), nullable=False)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    original_balance = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    write_off_amount = Column(Float, nullable=False)
    
    reason = Column(SQLEnum(WriteOffReason), nullable=False)
    detailed_rationale = Column(Text, nullable=False)
    
    cost_benefit_analysis = Column(JSON, nullable=True)
    
    approved_by = Column(String, nullable=False)
    approved_at = Column(DateTime, default=datetime.utcnow)
    
    governance_version = Column(String, nullable=False)
    
    reversible = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CollectionsProhibitedAction(Base):
    __tablename__ = "collections_prohibited_actions"

    id = Column(Integer, primary_key=True, index=True)
    
    action_attempted = Column(String, nullable=False)
    prohibited_reason = Column(Text, nullable=False)
    
    attempted_by = Column(String, nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    governance_version = Column(String, nullable=False)
    
    blocked = Column(Boolean, default=True)
    
    extra_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
