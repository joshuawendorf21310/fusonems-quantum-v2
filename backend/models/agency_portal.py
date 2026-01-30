from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from core.database import Base


class AgencyOnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    ACTIVE = "active"


class OnboardingStep(str, Enum):
    AGENCY_IDENTITY = "agency_identity"
    SERVICE_AREA = "service_area"
    LICENSING = "licensing"
    NEMSIS_REPORTING = "nemsis_reporting"
    PAYER_MIX = "payer_mix"
    INSURANCE_PREFERENCES = "insurance_preferences"
    REMITTANCE_HANDLING = "remittance_handling"
    PATIENT_COMMUNICATION = "patient_communication"
    AUTHORIZATION_CONSENT = "authorization_consent"
    FINAL_REVIEW = "final_review"


class MessageCategory(str, Enum):
    ONBOARDING = "onboarding"
    BILLING_STATUS = "billing_status"
    ANALYTICS = "analytics"
    INSURANCE_PAYER = "insurance_payer"
    DOCUMENT_SUBMISSION = "document_submission"
    GENERAL_SUPPORT = "general_support"


class MessagePriority(str, Enum):
    INFORMATIONAL = "informational"
    TIME_SENSITIVE = "time_sensitive"
    CRITICAL = "critical"


class MessageStatus(str, Enum):
    RECEIVED = "received"
    TRIAGED = "triaged"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    RESPONDED = "responded"
    RESOLVED = "resolved"


class ThirdPartyBillingAgency(Base):
    __tablename__ = "third_party_billing_agencies"

    id = Column(Integer, primary_key=True, index=True)
    
    agency_name = Column(String, nullable=False, index=True)
    agency_code = Column(String, unique=True, nullable=False, index=True)
    
    onboarding_status = Column(SQLEnum(AgencyOnboardingStatus), default=AgencyOnboardingStatus.NOT_STARTED)
    onboarding_started_at = Column(DateTime, nullable=True)
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_approved_at = Column(DateTime, nullable=True)
    billing_activated_at = Column(DateTime, nullable=True)
    
    active = Column(Boolean, default=False)
    
    service_area = Column(JSON, nullable=True)
    licensing_details = Column(JSON, nullable=True)
    nemsis_requirements = Column(JSON, nullable=True)
    payer_mix = Column(JSON, nullable=True)
    insurance_preferences = Column(JSON, nullable=True)
    remittance_handling = Column(JSON, nullable=True)
    patient_communication_preferences = Column(JSON, nullable=True)
    
    billing_provider_authorization = Column(Boolean, default=False)
    third_party_consent = Column(Boolean, default=False)
    
    primary_contact_name = Column(String, nullable=True)
    primary_contact_email = Column(String, nullable=True)
    primary_contact_phone = Column(String, nullable=True)
    
    portal_access_enabled = Column(Boolean, default=True)
    
    isolation_boundary = Column(String, nullable=False)
    
    # Multi-state: Wisconsin-first, US-wide
    state = Column(String(2), nullable=True, index=True)  # e.g. "WI", "IL"
    # Service types: ambulance, fire, hems (JSON list, e.g. ["ambulance", "fire", "hems"])
    service_types = Column(JSON, nullable=True)  # ["ambulance"] | ["fire"] | ["hems"] | any combination
    # Fair pricing: base + per transport (cents)
    base_charge_cents = Column(Integer, nullable=True)
    per_call_cents = Column(Integer, nullable=True)
    billing_interval = Column(String(20), nullable=True)  # e.g. "monthly"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    onboarding_steps = relationship("AgencyOnboardingStepRecord", back_populates="agency", cascade="all, delete-orphan")
    messages = relationship("AgencyPortalMessage", back_populates="agency", cascade="all, delete-orphan")
    analytics = relationship("AgencyAnalyticsSnapshot", back_populates="agency", cascade="all, delete-orphan")


class AgencyOnboardingStepRecord(Base):
    __tablename__ = "agency_onboarding_step_records"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False)
    
    step = Column(SQLEnum(OnboardingStep), nullable=False)
    step_order = Column(Integer, nullable=False)
    
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    data_collected = Column(JSON, default=dict)
    
    ai_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agency = relationship("ThirdPartyBillingAgency", back_populates="onboarding_steps")


class AgencyPortalMessage(Base):
    __tablename__ = "agency_portal_messages"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False)
    
    thread_id = Column(String, nullable=False, index=True)
    parent_message_id = Column(Integer, ForeignKey("agency_portal_messages.id"), nullable=True)
    
    category = Column(SQLEnum(MessageCategory), nullable=False)
    priority = Column(SQLEnum(MessagePriority), default=MessagePriority.INFORMATIONAL)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.RECEIVED)
    
    subject = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    sender_type = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    sla_response_due_at = Column(DateTime, nullable=True)
    sla_met = Column(Boolean, nullable=True)
    
    ai_triaged = Column(Boolean, default=False)
    ai_triage_summary = Column(Text, nullable=True)
    ai_extracted_questions = Column(JSON, default=list)
    ai_suggested_response = Column(Text, nullable=True)
    ai_routed_to = Column(String, nullable=True)
    
    requires_founder_attention = Column(Boolean, default=False)
    founder_reviewed = Column(Boolean, default=False)
    
    linked_context = Column(JSON, nullable=True)
    
    attachments = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agency = relationship("ThirdPartyBillingAgency", back_populates="messages")
    responses = relationship("AgencyPortalMessage", foreign_keys=[parent_message_id], remote_side=[id])


class AgencyAnalyticsSnapshot(Base):
    __tablename__ = "agency_analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False)
    
    period = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    charges_billed = Column(Float, default=0.0)
    payments_collected = Column(Float, default=0.0)
    outstanding_balance = Column(Float, default=0.0)
    
    collection_rate = Column(Float, default=0.0)
    average_days_to_pay = Column(Float, default=0.0)
    
    payer_mix_performance = Column(JSON, default=dict)
    denial_rate = Column(Float, default=0.0)
    
    payment_method_distribution = Column(JSON, default=dict)
    
    accounts_insurance_pending = Column(Integer, default=0)
    accounts_patient_responsibility = Column(Integer, default=0)
    accounts_payment_plan = Column(Integer, default=0)
    accounts_collections = Column(Integer, default=0)
    
    revenue_trend = Column(String, nullable=True)
    cash_flow_predictability_score = Column(Float, nullable=True)
    
    ai_explanation = Column(Text, nullable=True)
    ai_insights = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agency = relationship("ThirdPartyBillingAgency", back_populates="analytics")


class AgencyMessageSLA(Base):
    __tablename__ = "agency_message_slas"

    id = Column(Integer, primary_key=True, index=True)
    
    category = Column(SQLEnum(MessageCategory), nullable=False, unique=True)
    priority = Column(SQLEnum(MessagePriority), nullable=False)
    
    response_time_hours = Column(Integer, nullable=False)
    resolution_time_hours = Column(Integer, nullable=True)
    
    description = Column(Text, nullable=False)
    expectations = Column(Text, nullable=False)
    
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AITriageAction(Base):
    __tablename__ = "ai_triage_actions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("agency_portal_messages.id"), nullable=False)
    
    action_type = Column(String, nullable=False)
    action_description = Column(Text, nullable=False)
    
    category_assigned = Column(SQLEnum(MessageCategory), nullable=True)
    priority_assigned = Column(SQLEnum(MessagePriority), nullable=True)
    
    summary_generated = Column(Text, nullable=True)
    questions_extracted = Column(JSON, default=list)
    
    response_drafted = Column(Boolean, default=False)
    draft_response = Column(Text, nullable=True)
    
    flagged_for_founder = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    
    executed_by = Column(String, default="AI Agent - Messaging Auto-Triage")
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    extra_metadata = Column(JSON, default=dict)


class AgencyPortalAccessLog(Base):
    __tablename__ = "agency_portal_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False)
    
    user_name = Column(String, nullable=False)
    access_type = Column(String, nullable=False)
    
    resource_accessed = Column(String, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    ip_address = Column(String, nullable=True)
    
    isolation_verified = Column(Boolean, default=True)


class AgencyBillingIsolationBoundary(Base):
    __tablename__ = "agency_billing_isolation_boundaries"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), unique=True, nullable=False)
    
    can_view_own_data = Column(Boolean, default=True)
    can_view_cross_agency_data = Column(Boolean, default=False)
    
    can_modify_billing_logic = Column(Boolean, default=False)
    can_modify_collections_governance = Column(Boolean, default=False)
    can_modify_payment_processing = Column(Boolean, default=False)
    can_modify_ai_execution = Column(Boolean, default=False)
    
    can_contact_patients_directly = Column(Boolean, default=False)
    can_override_ai_actions = Column(Boolean, default=False)
    
    can_access_founder_dashboard = Column(Boolean, default=False)
    can_access_internal_systems = Column(Boolean, default=False)
    can_access_carefusion = Column(Boolean, default=False)
    can_access_telehealth = Column(Boolean, default=False)
    
    enforced = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# AGENCY TRANSPARENCY PORTAL MODELS
# ============================================================================
# These models provide read-only agency visibility into incidents, claims,
# and documentation while protecting internal billing mechanics.


class TransportType(str, Enum):
    EMERGENCY = "emergency"
    NON_EMERGENCY = "non_emergency"
    IFT = "ift"
    HEMS = "hems"


class ClaimStatusType(str, Enum):
    PREPARING_CLAIM = "preparing_claim"
    WAITING_ON_DOCUMENTATION = "waiting_on_documentation"
    SUBMITTED_TO_PAYER = "submitted_to_payer"
    PAYER_REVIEWING = "payer_reviewing"
    ADDITIONAL_INFO_REQUESTED = "additional_info_requested"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DENIED_UNDER_REVIEW = "denied_under_review"
    CLOSED = "closed"


class DocumentStatusType(str, Enum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    WAITING_ON_SENDER = "waiting_on_sender"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    COMPLETE = "complete"


class DocumentType(str, Enum):
    PCS = "pcs"
    AUTHORIZATION = "authorization"
    MEDICAL_RECORDS = "medical_records"
    SIGNATURES = "signatures"


class PendingFromType(str, Enum):
    FACILITY = "facility"
    PHYSICIAN_OFFICE = "physician_office"
    PAYER = "payer"


class AgencyPortalUserRole(str, Enum):
    AGENCY_ADMINISTRATOR = "agency_administrator"
    AGENCY_FINANCE_VIEWER = "agency_finance_viewer"
    AGENCY_OPERATIONS = "agency_operations"
    AGENCY_CREW = "agency_crew"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class AgencyIncidentView(Base):
    """
    Agency-safe incident data view.
    Excludes internal geocodes, CAD timelines, QA flags, and internal notes.
    Classification: AGENCY_VISIBLE
    """
    __tablename__ = "agency_incident_views"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # PHI Classification
    classification = Column(String, default="AGENCY_VISIBLE")
    
    # Incident Details
    date_of_service = Column(DateTime, nullable=False, index=True)
    transport_type = Column(SQLEnum(TransportType), nullable=False)
    
    # Location - Facility/City only (no geocodes)
    pickup_location = Column(String, nullable=True)  # Facility name or city
    destination_location = Column(String, nullable=True)  # Facility name or city
    
    # Unit and Patient (masked per policy)
    unit_identifier = Column(String, nullable=True)
    patient_reference = Column(String, nullable=True)  # Masked identifier
    
    # Claim Status (plain language)
    claim_status = Column(String, nullable=True)  # Human-readable status
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        {'comment': 'Agency-safe incident data excluding internal operations data'}
    )


class AgencyDocumentStatus(Base):
    """
    Document tracking visible to agencies.
    Excludes fax numbers, retry counts, AI confidence, and internal notes.
    Classification: AGENCY_VISIBLE
    """
    __tablename__ = "agency_document_statuses"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("agency_incident_views.incident_id"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    
    # PHI Classification
    classification = Column(String, default="AGENCY_VISIBLE")
    
    # Document Details
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    is_required = Column(Boolean, default=True)
    status = Column(SQLEnum(DocumentStatusType), default=DocumentStatusType.NOT_REQUESTED)
    
    # Pending Information (high-level only)
    pending_from = Column(SQLEnum(PendingFromType), nullable=True)
    last_status_change = Column(DateTime, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'comment': 'Document status tracking visible to agencies, excludes internal mechanics'}
    )


class AgencyClaimStatus(Base):
    """
    Plain-language claim states visible to agencies.
    Provides transparency without exposing internal billing logic.
    Classification: BILLING_SENSITIVE
    """
    __tablename__ = "agency_claim_statuses"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, nullable=False, unique=True, index=True)
    incident_id = Column(String, ForeignKey("agency_incident_views.incident_id"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    
    # PHI Classification
    classification = Column(String, default="BILLING_SENSITIVE")
    
    # Status Details
    status = Column(SQLEnum(ClaimStatusType), default=ClaimStatusType.PREPARING_CLAIM)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    short_explanation = Column(Text, nullable=True)  # Auto-generated explanation
    
    # Process Tracking (human-readable)
    current_step = Column(String, nullable=True)
    what_is_needed = Column(Text, nullable=True)
    who_is_responsible = Column(String, nullable=True)
    
    # Financial Summary
    amount_billed = Column(Numeric(10, 2), nullable=True)
    amount_paid = Column(Numeric(10, 2), default=0.00)
    remaining_balance = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'comment': 'Plain-language claim status for agency transparency'}
    )


class AgencyPayment(Base):
    """
    Payment tracking visible to agencies.
    Shows payment history without internal processing details.
    Classification: BILLING_SENSITIVE
    """
    __tablename__ = "agency_payments"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, ForeignKey("agency_claim_statuses.claim_id"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    
    # PHI Classification
    classification = Column(String, default="BILLING_SENSITIVE")
    
    # Payment Details
    payment_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    adjustment = Column(Numeric(10, 2), default=0.00)
    write_off = Column(Numeric(10, 2), default=0.00)
    
    # Payment Information
    payment_type = Column(String, nullable=True)  # check, eft, credit_card, etc.
    payer_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'comment': 'Payment tracking for agency transparency'}
    )


class AgencyPortalUser(Base):
    """
    Agency user access control.
    Defines roles and permissions for agency portal users.
    Classification: AGENCY_IDENTITY
    """
    __tablename__ = "agency_portal_users"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # PHI Classification
    classification = Column(String, default="AGENCY_IDENTITY")
    
    # Role and Permissions
    role = Column(SQLEnum(AgencyPortalUserRole), nullable=False)
    
    # Access Control
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    
    # Permissions (role-based defaults, can be customized)
    can_view_incidents = Column(Boolean, default=True)
    can_view_claims = Column(Boolean, default=False)  # Finance only
    can_view_payments = Column(Boolean, default=False)  # Finance only
    can_send_messages = Column(Boolean, default=True)
    can_download_reports = Column(Boolean, default=False)  # Admin/Finance only
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'comment': 'Agency portal user access and permissions'}
    )


class AgencyMessage(Base):
    """
    Secure messaging between agencies and platform.
    Supports incident-specific and general communications.
    Classification: AGENCY_COMMUNICATION
    """
    __tablename__ = "agency_messages"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("third_party_billing_agencies.id"), nullable=False, index=True)
    incident_id = Column(String, ForeignKey("agency_incident_views.incident_id"), nullable=True, index=True)
    
    # PHI Classification
    classification = Column(String, default="AGENCY_COMMUNICATION")
    
    # Message Details
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Direction and Status
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    read_status = Column(Boolean, default=False)
    
    # Sender Information
    sender_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sender_name = Column(String, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Thread Management
    thread_id = Column(String, nullable=True, index=True)
    parent_message_id = Column(Integer, ForeignKey("agency_messages.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = relationship("AgencyMessage", foreign_keys=[parent_message_id], remote_side=[id])
    
    __table_args__ = (
        {'comment': 'Secure messaging for agency-platform communication'}
    )

