from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from core.database import TelehealthBase


class TelehealthSession(TelehealthBase):
    __tablename__ = "telehealth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    host_name = Column(String, nullable=False)
    access_code = Column(String, nullable=False)
    session_secret = Column(String, nullable=False)
    status = Column(String, default="Scheduled")
    modality = Column(String, default="video")
    recording_enabled = Column(Boolean, default=True)
    encryption_state = Column(String, default="secure")
    consent_required = Column(Boolean, default=True)
    consent_captured_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TelehealthParticipant(TelehealthBase):
    __tablename__ = "telehealth_participants"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="patient")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class TelehealthMessage(TelehealthBase):
    __tablename__ = "telehealth_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    session_uuid = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TelehealthProvider(TelehealthBase):
    __tablename__ = "telehealth_providers"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    provider_id = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, default="")
    credentials = Column(String, default="")
    license_number = Column(String, default="")
    license_state = Column(String, default="")
    email = Column(String, nullable=False)
    phone = Column(String, default="")
    bio = Column(Text, default="")
    photo_url = Column(String, default="")
    status = Column(String, default="active")
    accepts_new_patients = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TelehealthPatient(TelehealthBase):
    __tablename__ = "telehealth_patients"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    patient_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, default="")
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    address = Column(Text, default="")
    emergency_contact_name = Column(String, default="")
    emergency_contact_phone = Column(String, default="")
    insurance_provider = Column(String, default="")
    insurance_policy_number = Column(String, default="")
    medical_history = Column(Text, default="")
    allergies = Column(Text, default="")
    current_medications = Column(Text, default="")
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TelehealthAppointment(TelehealthBase):
    __tablename__ = "telehealth_appointments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    appointment_id = Column(String, nullable=False, unique=True, index=True)
    patient_id = Column(String, ForeignKey("telehealth_patients.patient_id"), nullable=False, index=True)
    provider_id = Column(String, ForeignKey("telehealth_providers.provider_id"), nullable=False, index=True)
    session_uuid = Column(String, ForeignKey("telehealth_sessions.session_uuid"), nullable=True, index=True)
    appointment_type = Column(String, default="consultation")
    reason_for_visit = Column(Text, nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="scheduled")
    patient_notes = Column(Text, default="")
    provider_notes = Column(Text, default="")
    cancellation_reason = Column(Text, default="")
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TelehealthVisit(TelehealthBase):
    __tablename__ = "telehealth_visits"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    visit_id = Column(String, nullable=False, unique=True, index=True)
    appointment_id = Column(String, ForeignKey("telehealth_appointments.appointment_id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("telehealth_patients.patient_id"), nullable=False, index=True)
    provider_id = Column(String, ForeignKey("telehealth_providers.provider_id"), nullable=False, index=True)
    session_uuid = Column(String, ForeignKey("telehealth_sessions.session_uuid"), nullable=True, index=True)
    chief_complaint = Column(Text, nullable=False)
    history_of_present_illness = Column(Text, default="")
    vital_signs = Column(Text, default="")
    physical_exam = Column(Text, default="")
    assessment = Column(Text, default="")
    diagnosis_codes = Column(String, default="")
    treatment_plan = Column(Text, default="")
    prescriptions_issued = Column(Text, default="")
    follow_up_instructions = Column(Text, default="")
    recording_url = Column(String, default="")
    billing_code = Column(String, default="")
    billing_amount = Column(Numeric(12, 2), default=0)
    billing_status = Column(String, default="pending")
    visit_summary = Column(Text, default="")
    status = Column(String, default="in_progress")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProviderAvailability(TelehealthBase):
    __tablename__ = "provider_availability"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    provider_id = Column(String, ForeignKey("telehealth_providers.provider_id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    slot_duration_minutes = Column(Integer, default=30)
    is_available = Column(Boolean, default=True)
    override_date = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TelehealthPrescription(TelehealthBase):
    __tablename__ = "telehealth_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    prescription_id = Column(String, nullable=False, unique=True, index=True)
    visit_id = Column(String, ForeignKey("telehealth_visits.visit_id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("telehealth_patients.patient_id"), nullable=False, index=True)
    provider_id = Column(String, ForeignKey("telehealth_providers.provider_id"), nullable=False, index=True)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    refills = Column(Integer, default=0)
    directions = Column(Text, nullable=False)
    pharmacy_name = Column(String, default="")
    pharmacy_phone = Column(String, default="")
    pharmacy_fax = Column(String, default="")
    status = Column(String, default="pending")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
