from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum
from core.database import Base
from models.epcr import Patient
from models.cad import Call


class MessageStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DENIED = "denied"


# ============================================================================
# PATIENT PORTAL
# ============================================================================

class PatientPortalAccount(Base):
    __tablename__ = "patient_portal_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String)
    
    # Authentication
    password_hash = Column(String, nullable=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_phone = Column(String)
    
    # Account Status
    account_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String)
    
    # Password Reset
    password_reset_token = Column(String)
    password_reset_expires = Column(DateTime)
    
    # Access
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Consent
    terms_accepted = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime)
    hipaa_acknowledgment = Column(Boolean, default=False)
    hipaa_acknowledged_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientPortalMessage(Base):
    __tablename__ = "patient_portal_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    subject = Column(String, nullable=False)
    message_body = Column(Text, nullable=False)
    
    # Direction
    sent_by_patient = Column(Boolean, default=True)
    sent_by_staff_name = Column(String)
    
    # Status
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.UNREAD)
    
    # Thread
    parent_message_id = Column(Integer, ForeignKey("patient_portal_messages.id"))
    
    # Attachments
    has_attachment = Column(Boolean, default=False)
    attachment_paths = Column(JSON)
    
    # Read Tracking
    read_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MedicalRecordRequest(Base):
    __tablename__ = "medical_record_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    request_type = Column(String, nullable=False)  # Full Records, Specific Incident, Date Range
    
    # Specific Incident
    incident_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True)
    
    # Date Range
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    
    # Delivery Method
    delivery_method = Column(String, nullable=False)  # Email, Mail, Portal Download, In-Person Pickup
    delivery_address = Column(String)
    delivery_email = Column(String)
    
    # Authorization
    authorization_form_path = Column(String)
    hipaa_authorization_signed = Column(Boolean, default=False)
    
    # Status
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    
    assigned_to = Column(String)
    completed_date = Column(DateTime)
    denial_reason = Column(Text)
    
    # Fees
    fee_charged = Column(Float, default=0.0)
    fee_paid = Column(Boolean, default=False)
    payment_date = Column(DateTime)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientBillPayment(Base):
    __tablename__ = "patient_bill_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    statement_id = Column(Integer, ForeignKey("patient_statements.id"), nullable=True)
    
    payment_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)  # Credit Card, Debit Card, ACH, Check
    
    # Stripe Integration
    stripe_payment_intent_id = Column(String, unique=True)
    stripe_charge_id = Column(String)
    
    # Card Details (last 4 only, no full card numbers)
    card_last_four = Column(String)
    card_brand = Column(String)
    
    # ACH Details
    bank_name = Column(String)
    account_last_four = Column(String)
    
    # Status
    payment_status = Column(String, default="pending")  # pending, completed, failed, refunded
    
    # Confirmation
    confirmation_number = Column(String, unique=True)
    receipt_sent = Column(Boolean, default=False)
    receipt_sent_at = Column(DateTime)
    
    # Processing
    processed_at = Column(DateTime)
    failure_reason = Column(Text)
    
    # Refund
    refunded = Column(Boolean, default=False)
    refund_amount = Column(Float)
    refund_date = Column(DateTime)
    refund_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AppointmentRequest(Base):
    __tablename__ = "appointment_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    appointment_type = Column(String, nullable=False)  # Follow-Up, Records Pickup, Billing Inquiry
    
    requested_date = Column(Date)
    requested_time = Column(String)
    alternate_date = Column(Date)
    alternate_time = Column(String)
    
    reason = Column(Text)
    
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    
    # Scheduled
    scheduled_date = Column(Date)
    scheduled_time = Column(String)
    location = Column(String)
    
    assigned_to = Column(String)
    
    # Confirmation
    confirmed_by_patient = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientPortalAccessLog(Base):
    __tablename__ = "patient_portal_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    access_date = Column(DateTime, default=datetime.utcnow)
    
    action = Column(String, nullable=False)  # Login, View Statement, View Records, Download Document, Send Message, Make Payment
    
    ip_address = Column(String)
    user_agent = Column(String)
    
    resource_accessed = Column(String)  # statement_id:123, message_id:456, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientDocumentShare(Base):
    __tablename__ = "patient_document_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    document_type = Column(String, nullable=False)  # ePCR, Statement, Lab Result, etc.
    document_id = Column(Integer, nullable=False)
    
    # Share Details
    share_token = Column(String, unique=True, nullable=False, index=True)
    share_expires_at = Column(DateTime, nullable=False)
    
    recipient_email = Column(String)
    recipient_name = Column(String)
    
    # Access Tracking
    accessed = Column(Boolean, default=False)
    accessed_at = Column(DateTime)
    access_count = Column(Integer, default=0)
    
    # Security
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String)
    
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientPreference(Base):
    __tablename__ = "patient_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    
    # Communication Preferences
    preferred_contact_method = Column(String)  # Email, Phone, SMS, Portal
    email_notifications_enabled = Column(Boolean, default=True)
    sms_notifications_enabled = Column(Boolean, default=False)
    
    # Notification Types
    notify_new_statement = Column(Boolean, default=True)
    notify_payment_due = Column(Boolean, default=True)
    notify_payment_received = Column(Boolean, default=True)
    notify_new_message = Column(Boolean, default=True)
    notify_appointment_reminder = Column(Boolean, default=True)
    
    # Statement Delivery
    paperless_statements = Column(Boolean, default=False)
    
    # Language
    preferred_language = Column(String, default="en")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientSurveyResponse(Base):
    __tablename__ = "patient_survey_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True)
    
    survey_sent_at = Column(DateTime)
    survey_completed_at = Column(DateTime)
    
    # Ratings (1-5)
    overall_satisfaction = Column(Integer)
    response_time_rating = Column(Integer)
    crew_professionalism_rating = Column(Integer)
    care_quality_rating = Column(Integer)
    communication_rating = Column(Integer)
    
    # Net Promoter Score (0-10)
    nps_score = Column(Integer)
    
    # Comments
    positive_feedback = Column(Text)
    areas_for_improvement = Column(Text)
    
    # Follow-Up
    follow_up_requested = Column(Boolean, default=False)
    follow_up_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
