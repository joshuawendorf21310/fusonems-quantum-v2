from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)

from core.database import Base


class PatientStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    LOCKED = "locked"
    BILLING_READY = "billing_ready"


class NEMSISValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class EpcrRecordStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINALIZED = "finalized"
    SUBMITTED = "submitted"


class OfflineSyncStatus(str, Enum):
    QUEUED = "queued"
    SYNCED = "synced"
    FAILED = "failed"


class ProviderCertificationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Patient(Base):
    __tablename__ = "epcr_patients"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    nemsis_version = Column(String, default="3.5.1")
    nemsis_state = Column(String, default="WI")
    first_name = Column(String, nullable=False)
    middle_name = Column(String, default="")
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    gender = Column(String, default="")
    race = Column(String, default="")
    ethnicity = Column(String, default="")
    mrn = Column(String, default="")
    phone = Column(String, default="")
    address = Column(String, default="")
    city = Column(String, default="")
    state = Column(String, default="")
    postal_code = Column(String, default="")
    incident_number = Column(String, nullable=False, index=True)
    chief_complaint = Column(String, default="")
    vitals = Column(JSON, nullable=False, default=dict)
    interventions = Column(JSON, nullable=False, default=list)
    medications = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    labs = Column(JSON, nullable=False, default=list)
    cct_interventions = Column(JSON, nullable=False, default=list)
    ocr_snapshots = Column(JSON, nullable=False, default=list)
    narrative = Column(Text, default="")
    chart_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String, default="")
    status = Column(SQLEnum(PatientStatus), default=PatientStatus.DRAFT, index=True)
    qa_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MasterPatient(Base):
    __tablename__ = "master_patients"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    phone = Column(String, default="")
    address = Column(String, default="")
    merged_into_id = Column(Integer, ForeignKey("master_patients.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MasterPatientLink(Base):
    __tablename__ = "master_patient_links"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    epcr_patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False, index=True)
    master_patient_id = Column(Integer, ForeignKey("master_patients.id"), nullable=False, index=True)
    provenance = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MasterPatientMerge(Base):
    __tablename__ = "master_patient_merges"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    from_id = Column(Integer, ForeignKey("master_patients.id"), nullable=False)
    to_id = Column(Integer, ForeignKey("master_patients.id"), nullable=False)
    reason = Column(String, default="")
    actor = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NEMSISValidationResult(Base):
    __tablename__ = "nemsis_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    epcr_patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False, index=True)
    validation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    nemsis_version = Column(String, default="3.5.1")
    status = Column(SQLEnum(NEMSISValidationStatus), default=NEMSISValidationStatus.FAIL)
    missing_fields = Column(JSON, nullable=False, default=list)
    validation_errors = Column(JSON, nullable=False, default=list)
    validator_version = Column(String, default="1.0.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PatientStateTimeline(Base):
    __tablename__ = "patient_state_timeline"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    epcr_patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False, index=True)
    from_status = Column(SQLEnum(PatientStatus), default=PatientStatus.DRAFT)
    to_status = Column(SQLEnum(PatientStatus), default=PatientStatus.DRAFT)
    transition_reason = Column(String, default="")
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class NarrativeVersion(Base):
    __tablename__ = "narrative_versions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    epcr_patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False, index=True)
    version_number = Column(Integer, default=1)
    narrative_text = Column(Text, default="")
    generation_source = Column(String, default="manual")
    generation_metadata = Column(JSON, nullable=False, default=dict)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class EpcrRecord(Base):
    __tablename__ = "epcr_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=False, index=True)
    record_number = Column(String, nullable=False, index=True)
    incident_number = Column(String, nullable=False, index=True)
    cad_call_id = Column(String, default="")
    assignment_id = Column(String, default="")
    protocol_pathway_id = Column(Integer, ForeignKey("protocol_pathways.id"), nullable=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    status = Column(SQLEnum(EpcrRecordStatus), default=EpcrRecordStatus.DRAFT, index=True)
    nemsis_version = Column(String, default="3.5.1")
    nemsis_state = Column(String, default="WI")
    incident_datetime = Column(DateTime(timezone=True), nullable=True)
    dispatch_datetime = Column(DateTime(timezone=True), nullable=True)
    scene_arrival_datetime = Column(DateTime(timezone=True), nullable=True)
    scene_departure_datetime = Column(DateTime(timezone=True), nullable=True)
    hospital_arrival_datetime = Column(DateTime(timezone=True), nullable=True)
    patient_destination = Column(String, default="")
    destination_address = Column(String, default="")
    destination_phone = Column(String, default="")
    chief_complaint = Column(String, default="")
    chief_complaint_code = Column(String, default="")
    injury_mechanism = Column(String, default="")
    trauma_score = Column(JSON, default=dict)
    airway_status = Column(String, default="")
    transport_priority = Column(String, default="")
    reason_for_transport = Column(Text, default="")
    custom_fields = Column(JSON, nullable=False, default=dict)
    is_finalized = Column(Boolean, default=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EpcrVitals(Base):
    __tablename__ = "epcr_vitals"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    sequence = Column(Integer, default=0)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String, default="manual")
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    values = Column(JSON, nullable=False, default=dict)
    nemsis_elements = Column(JSON, nullable=False, default=dict)
    confidence = Column(Integer, default=100)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrAssessment(Base):
    __tablename__ = "epcr_assessments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    chief_complaint = Column(String, default="")
    assessment_summary = Column(Text, default="")
    clinical_impression = Column(Text, default="")
    impression_code = Column(String(32), default="")  # ICD-10 from terminology (NEMSIS-constrained)
    plan = Column(Text, default="")
    protocol_notes = Column(JSON, nullable=False, default=dict)
    supporting_documents = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrIntervention(Base):
    __tablename__ = "epcr_interventions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    procedure_name = Column(String, nullable=False)
    description = Column(Text, default="")
    performed_at = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, default="scene")
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    result = Column(String, default="")
    intervention_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrMedication(Base):
    __tablename__ = "epcr_medications"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    medication_name = Column(String, nullable=False)
    ndc = Column(String, default="")
    dose = Column(String, default="")
    units = Column(String, default="")
    route = Column(String, default="")
    administration_time = Column(DateTime(timezone=True), nullable=True)
    frequency = Column(String, default="")
    infusion_rate = Column(String, default="")
    volume = Column(String, default="")
    stop_time = Column(DateTime(timezone=True), nullable=True)
    estimated_effect = Column(String, default="")
    med_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrNarrative(Base):
    __tablename__ = "epcr_narratives"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    narrative_text = Column(Text, default="")
    generation_source = Column(String, default="manual")
    voice_transcription_id = Column(String, default="")
    confidence_score = Column(Integer, default=0)
    version_number = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    ai_refined_text = Column(Text, default="")
    med_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrOcrSnapshot(Base):
    __tablename__ = "epcr_ocr_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    device_type = Column(String, default="")
    device_name = Column(String, default="")
    confidence = Column(Integer, default=0)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    raw_text = Column(Text, default="")
    fields = Column(JSON, nullable=False, default=dict)
    med_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrTimeline(Base):
    __tablename__ = "epcr_timeline"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    description = Column(Text, default="")
    timestamp = Column(DateTime(timezone=True), nullable=False)
    med_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PreArrivalNotification(Base):
    __tablename__ = "prearrival_notifications"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    hospital_name = Column(String, default="")
    hospital_phone = Column(String, default="")
    hospital_address = Column(String, default="")
    hospital_latitude = Column(String, default="")
    hospital_longitude = Column(String, default="")
    eta = Column(DateTime(timezone=True), nullable=True)
    eta_threshold_minutes = Column(Integer, default=15)
    eta_source = Column(String, default="gps")
    channel = Column(String, default="text")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    disposition_element = Column(String, default="eDisposition.24")
    med_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrValidationRule(Base):
    __tablename__ = "epcr_validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    target_field = Column(String, default="")
    condition = Column(JSON, nullable=False, default=dict)
    severity = Column(String, default="high")
    enforcement = Column(String, default="hard_block")
    active = Column(Boolean, default=True)
    version = Column(String, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrVisibilityRule(Base):
    __tablename__ = "epcr_visibility_rules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    target_fields = Column(JSON, nullable=False, default=list)
    visibility_condition = Column(JSON, nullable=False, default=dict)
    default_visibility = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    version = Column(String, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EpcrSchematronRule(Base):
    __tablename__ = "epcr_schematron_rules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    namespace = Column(String, default="")
    assertion = Column(Text, default="")
    fix = Column(Text, default="")
    active = Column(Boolean, default=True)
    version = Column(String, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProtocolPathway(Base):
    __tablename__ = "protocol_pathways"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    protocol_type = Column(String, default="general")
    age_range = Column(JSON, nullable=False, default=dict)
    vitals_thresholds = Column(JSON, nullable=False, default=dict)
    keywords = Column(JSON, nullable=False, default=list)
    ai_trigger = Column(JSON, nullable=False, default=dict)
    confidence_override = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    version = Column(String, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProviderCertification(Base):
    __tablename__ = "provider_certifications"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    certification_type = Column(String, nullable=False)
    certification_type_id = Column(Integer, ForeignKey("certification_types.id"), nullable=True)
    jurisdiction = Column(String, default="")
    issued_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(ProviderCertificationStatus), default=ProviderCertificationStatus.ACTIVE)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CertificationType(Base):
    __tablename__ = "certification_types"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    jurisdiction = Column(String, default="")
    scope = Column(JSON, nullable=False, default=dict)
    required_roles = Column(JSON, nullable=False, default=list)
    version = Column(String, default="v1")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OfflineSyncQueue(Base):
    __tablename__ = "epcr_offline_sync"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    encrypted_payload = Column(String, default="")
    status = Column(SQLEnum(OfflineSyncStatus), default=OfflineSyncStatus.QUEUED)
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
