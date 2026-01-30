from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class FaxRecord(Base):
    __tablename__ = "fax_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Direction: inbound or outbound
    direction = Column(String, nullable=False, index=True)
    
    # Status: queued, sending, delivered, failed, received
    status = Column(String, default="queued", index=True)
    
    # Sender/Recipient info
    sender_number = Column(String, default="")
    recipient_number = Column(String, default="")
    sender_name = Column(String, default="")
    recipient_name = Column(String, default="")
    
    # Cover page
    has_cover_page = Column(Boolean, default=False)
    cover_page_subject = Column(String, default="")
    cover_page_message = Column(Text, default="")
    cover_page_from = Column(String, default="")
    cover_page_to = Column(String, default="")
    
    # Fax details
    page_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Provider details
    provider = Column(String, default="srfax")  # srfax, twilio, etc
    provider_fax_id = Column(String, default="", index=True)
    provider_status = Column(String, default="")
    provider_response = Column(JSON, nullable=False, default=dict)
    
    # Document storage
    document_url = Column(String, default="")
    document_filename = Column(String, default="")
    document_content_type = Column(String, default="application/pdf")
    document_size_bytes = Column(Integer, default=0)
    
    # Timestamps
    queued_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(Text, default="")
    error_code = Column(String, default="")
    
    # Metadata
    meta = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="phi")  # Healthcare faxes are PHI
    
    # User tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FaxAttachment(Base):
    __tablename__ = "fax_attachments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    fax_id = Column(Integer, ForeignKey("fax_records.id"), nullable=False, index=True)
    
    # Attachment details
    filename = Column(String, nullable=False)
    original_filename = Column(String, default="")
    content_type = Column(String, default="application/pdf")
    size_bytes = Column(Integer, default=0)
    
    # Storage
    file_url = Column(String, default="")
    file_path = Column(String, default="")
    sha256 = Column(String, default="", index=True)
    
    # Metadata
    page_count = Column(Integer, default=0)
    meta = Column(JSON, nullable=False, default=dict)
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FacilityContact(Base):
    """Trusted facility contact information - Layer 1 and Layer 2 source"""
    __tablename__ = "facility_contacts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Facility identification
    facility_name = Column(String, nullable=False, index=True)
    facility_address = Column(String, default="")
    facility_city = Column(String, default="", index=True)
    facility_state = Column(String, default="", index=True)
    facility_zip = Column(String, default="")
    
    # External identifiers
    npi = Column(String, default="", index=True)
    cms_ccn = Column(String, default="", index=True)
    state_license = Column(String, default="")
    
    # Contact information
    fax_number = Column(String, nullable=False, index=True)
    phone_number = Column(String, default="")
    
    # Department routing
    department = Column(String, default="general")  # general, records, billing, admissions, physician, case_management
    department_tag = Column(String, default="")  # Custom agency tags
    
    # Data source tracking
    source_layer = Column(Integer, nullable=False)  # 1=internal, 2=agency-provided, 3=external-reference
    source_description = Column(String, default="")
    
    # Validation and verification
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_successful_fax = Column(DateTime(timezone=True), nullable=True)
    total_successful_faxes = Column(Integer, default=0)
    total_failed_faxes = Column(Integer, default=0)
    
    # Version control for agency-provided data
    version = Column(Integer, default=1)
    replaced_by = Column(Integer, ForeignKey("facility_contacts.id"), nullable=True)
    
    # Status
    active = Column(Boolean, default=True, index=True)
    notes = Column(Text, default="")
    
    # Metadata
    meta = Column(JSON, nullable=False, default=dict)
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FaxResolutionHistory(Base):
    """Audit trail for fax number resolution attempts"""
    __tablename__ = "fax_resolution_history"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Resolution request
    facility_name = Column(String, nullable=False, index=True)
    facility_address = Column(String, default="")
    document_type = Column(String, default="")  # PCS, medical_records, authorization, denial, etc.
    workflow_context = Column(String, default="")
    
    # Resolution result
    resolved = Column(Boolean, nullable=False, index=True)
    fax_number = Column(String, default="")
    source_layer = Column(Integer, nullable=True)  # 1-4
    source_description = Column(String, default="")
    confidence_score = Column(Integer, default=0)  # 0-100
    department = Column(String, default="")
    
    # Decision flags
    requires_human_review = Column(Boolean, default=False, index=True)
    human_reviewed = Column(Boolean, default=False)
    human_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    human_reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Conflict tracking
    conflicting_numbers = Column(JSON, nullable=False, default=list)
    
    # Audit trail
    resolution_steps = Column(JSON, nullable=False, default=list)  # List of ResolutionStep dicts
    
    # Linked records
    facility_contact_id = Column(Integer, ForeignKey("facility_contacts.id"), nullable=True, index=True)
    fax_record_id = Column(Integer, ForeignKey("fax_records.id"), nullable=True, index=True)
    
    # Metadata
    meta = Column(JSON, nullable=False, default=dict)
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InboundFax(Base):
    """Inbound fax document reception and classification"""
    __tablename__ = "inbound_faxes"

    id = Column(String, primary_key=True, index=True)  # UUID
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Reception details
    received_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sender_fax_number = Column(String, nullable=False, index=True)
    pages = Column(Integer, default=0)
    
    # Document storage (immutable)
    original_document_url = Column(String, nullable=False)
    original_document_sha256 = Column(String, default="", index=True)
    original_document_size_bytes = Column(Integer, default=0)
    
    # Provider details
    provider = Column(String, default="srfax", index=True)
    provider_fax_id = Column(String, default="", index=True)
    provider_metadata = Column(JSON, nullable=False, default=dict)
    
    # Classification
    classified_type = Column(String, default="unknown", index=True)  # pcs, authorization, medical_records, denial, unknown
    classification_confidence = Column(Integer, default=0)  # 0-100
    classification_method = Column(String, default="")  # ai, ocr, manual, rule_based
    classification_details = Column(JSON, nullable=False, default=dict)
    
    # Matching
    matched_request_id = Column(String, nullable=True, index=True)
    match_confidence = Column(Integer, default=0)  # 0-100
    match_method = Column(String, default="")
    match_details = Column(JSON, nullable=False, default=dict)
    
    # Review
    requires_human_review = Column(Boolean, default=False, index=True)
    review_reason = Column(String, default="")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, default="")
    
    # Status: received, classifying, classified, matching, matched, attached, pending_review, rejected
    status = Column(String, default="received", nullable=False, index=True)
    
    # OCR extracted data
    extracted_text = Column(Text, default="")
    extracted_fields = Column(JSON, nullable=False, default=dict)
    
    # Metadata
    meta = Column(JSON, nullable=False, default=dict)
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InboundFaxMatchAttempt(Base):
    """Individual matching attempts for inbound faxes"""
    __tablename__ = "inbound_fax_match_attempts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    inbound_fax_id = Column(String, ForeignKey("inbound_faxes.id"), nullable=False, index=True)
    
    # Match target
    request_id = Column(String, nullable=False, index=True)
    request_type = Column(String, default="")  # billing_request, authorization_request, etc.
    
    # Match scoring
    match_score = Column(Integer, nullable=False)  # 0-100
    match_factors = Column(JSON, nullable=False, default=dict)  # What matched (patient, date, facility, etc.)
    
    # Selection
    selected = Column(Boolean, default=False, index=True)
    selected_at = Column(DateTime(timezone=True), nullable=True)
    selected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    meta = Column(JSON, nullable=False, default=dict)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FaxTemplate(Base):
    """Locked fax templates requiring founder approval for changes - Section V"""
    __tablename__ = "fax_templates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Template identification
    document_type = Column(String, nullable=False, index=True)
    template_name = Column(String, nullable=False)
    template_body = Column(Text, nullable=False)
    
    # Version control
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Approval tracking - IMMUTABLE without founder approval
    approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Change request tracking
    pending_change_request = Column(Boolean, default=False, nullable=False)
    proposed_body = Column(Text, default="")
    change_requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_requested_at = Column(DateTime(timezone=True), nullable=True)
    change_justification = Column(Text, default="")
    
    # Audit trail
    replaced_by = Column(Integer, ForeignKey("fax_templates.id"), nullable=True)
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FaxAuditLog(Base):
    """
    IMMUTABLE audit log for all fax operations.
    Every fax action must be logged with complete context and tamper detection.
    """
    __tablename__ = "fax_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Action details
    action_type = Column(String, nullable=False, index=True)  # policy_check, resolution, send_attempt, receive, classify, match, review
    request_id = Column(String, nullable=False, index=True)  # UUID for tracking related actions
    incident_id = Column(Integer, ForeignKey("cad_incidents.id"), nullable=True, index=True)
    claim_id = Column(Integer, nullable=True)
    
    # Policy reference
    policy_decision_id = Column(String, nullable=False, index=True)  # Reference to policy decision
    policy_allowed = Column(Boolean, nullable=False, index=True)
    policy_reference = Column(String, nullable=False)  # Which policy/rule was applied
    
    # Document details
    document_type = Column(String, nullable=False, index=True)  # DocumentType enum value
    
    # Resolution details
    destination_source_layer = Column(Integer, nullable=True)  # 1-4 source layer
    destination_fax_number = Column(String, default="")  # Encrypted in production
    destination_facility = Column(String, default="")
    destination_department = Column(String, default="")
    
    # Outcome
    outcome = Column(String, nullable=False, index=True)  # success, failed, denied, pending_review, suppressed
    outcome_details = Column(JSON, nullable=False, default=dict)  # Detailed outcome data
    error_message = Column(Text, default="")
    error_code = Column(String, default="")
    
    # Metadata
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # If human-triggered
    ai_initiated = Column(Boolean, default=False, index=True)
    ai_confidence_score = Column(Integer, default=0)  # 0-100
    
    # Linked records
    fax_record_id = Column(Integer, ForeignKey("fax_records.id"), nullable=True, index=True)
    resolution_history_id = Column(Integer, ForeignKey("fax_resolution_history.id"), nullable=True, index=True)
    
    # Complete context snapshot (immutable)
    workflow_state = Column(String, default="")
    timing_context = Column(JSON, nullable=False, default=dict)
    resolution_context = Column(JSON, nullable=False, default=dict)
    
    # Immutable hash for tamper detection
    audit_hash = Column(String, nullable=False, index=True)  # SHA256 of record
    
    # Training mode flag
    training_mode = Column(Boolean, default=False, index=True)


class DocumentType:
    """Enum-like class for fax document types"""
    PCS = "PCS"
    AUTHORIZATION = "AUTHORIZATION"
    MEDICAL_RECORDS = "MEDICAL_RECORDS"
    DENIAL_DOCUMENTATION = "DENIAL_DOCUMENTATION"
    COMPLIANCE_DOCUMENTS = "COMPLIANCE_DOCUMENTS"
    GENERAL_COMPLIANCE = "GENERAL_COMPLIANCE"
    BILL = "BILL"
    CLAIM = "CLAIM"
    APPEAL = "APPEAL"
    OTHER = "OTHER"


class FaxAttemptLog(Base):
    """Log of fax attempt timing for anti-spam controls"""
    __tablename__ = "fax_attempt_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    request_id = Column(String, nullable=False, index=True)
    recipient_number = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False)
    attempt_count = Column(Integer, default=1)
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now())
    next_allowed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending", index=True)
    result = Column(String, default="")
    error_message = Column(Text, default="")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
