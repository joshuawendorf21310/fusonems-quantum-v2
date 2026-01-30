from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum
from core.database import Base
from models.cad import Call, Unit


class PredictionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ============================================================================
# AI PREDICTIVE ANALYTICS & INTELLIGENCE
# ============================================================================

class CallVolumePrediction(Base):
    """AI-powered call volume forecasting"""
    __tablename__ = "call_volume_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    prediction_date = Column(Date, nullable=False, index=True)
    prediction_hour = Column(Integer)  # 0-23 for hourly predictions
    
    # Predictions
    predicted_call_volume = Column(Integer, nullable=False)
    predicted_als_calls = Column(Integer)
    predicted_bls_calls = Column(Integer)
    predicted_trauma_calls = Column(Integer)
    predicted_cardiac_calls = Column(Integer)
    
    # Confidence
    confidence_level = Column(SQLEnum(PredictionConfidence), default=PredictionConfidence.MEDIUM)
    confidence_score = Column(Float)
    
    # Factors
    weather_factor = Column(Float)  # Weather impact on call volume
    event_factor = Column(Float)  # Local events (sports, concerts)
    historical_factor = Column(Float)  # Historical patterns
    seasonal_factor = Column(Float)  # Seasonal trends
    
    # Recommended Actions
    recommended_staffing_level = Column(String)
    recommended_unit_placement = Column(JSON)  # [{"unit": "M1", "station": "Station 1"}]
    
    # Actual vs Predicted (populated after the day)
    actual_call_volume = Column(Integer)
    prediction_accuracy = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CrewFatigueAnalysis(Base):
    """AI-powered crew fatigue detection and prevention"""
    __tablename__ = "crew_fatigue_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    
    analysis_date = Column(Date, nullable=False, index=True)
    
    # Fatigue Indicators
    hours_worked_last_24h = Column(Float, nullable=False)
    hours_worked_last_7d = Column(Float, nullable=False)
    consecutive_shifts = Column(Integer)
    calls_responded_last_shift = Column(Integer)
    high_acuity_calls_last_shift = Column(Integer)
    
    # Sleep Estimation
    estimated_hours_off_duty = Column(Float)
    estimated_sleep_hours = Column(Float)
    
    # Fatigue Score
    fatigue_score = Column(Float, nullable=False)  # 0-100, 100 = extreme fatigue
    fatigue_level = Column(String)  # Low, Moderate, High, Critical
    
    # Risk Assessment
    safety_risk_level = Column(SQLEnum(AlertSeverity), default=AlertSeverity.INFO)
    performance_impact_predicted = Column(Float)  # 0-100% performance degradation
    
    # Recommendations
    recommended_action = Column(String)  # Continue, Monitor, Rest Break, Off Duty
    recommended_rest_hours = Column(Float)
    
    # AI Confidence
    confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class OptimalUnitPlacement(Base):
    """AI-powered dynamic unit placement optimization"""
    __tablename__ = "optimal_unit_placements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    recommendation_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Current State
    current_unit_id = Column(Integer, ForeignKey("cad_units.id"), nullable=False)
    current_location = Column(String)
    current_station = Column(String)
    
    # Optimal Placement
    recommended_location = Column(String)
    recommended_station = Column(String)
    recommended_latitude = Column(Float)
    recommended_longitude = Column(Float)
    
    # Reasoning
    reasoning_factors = Column(JSON)  # [{"factor": "High call volume area", "weight": 0.4}]
    coverage_improvement = Column(Float)  # % improvement in coverage
    response_time_improvement = Column(Float)  # Estimated seconds saved
    
    # Risk Areas
    high_risk_areas = Column(JSON)  # [{"area": "Downtown", "risk_score": 0.8}]
    
    # Prediction
    predicted_next_call_location = Column(String)
    predicted_next_call_latitude = Column(Float)
    predicted_next_call_longitude = Column(Float)
    predicted_next_call_time = Column(DateTime)
    
    # Implementation
    implemented = Column(Boolean, default=False)
    implemented_at = Column(DateTime)
    
    # Validation (after implementation)
    actual_response_time_improvement = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AIDocumentationAssistant(Base):
    """AI-powered auto-documentation and narrative generation"""
    __tablename__ = "ai_documentation_assistant"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    
    # AI-Generated Content
    ai_generated_narrative = Column(Text)
    ai_generated_assessment = Column(Text)
    ai_suggested_diagnoses = Column(JSON)  # ["STEMI", "Acute MI", "Chest Pain - Cardiac"]
    ai_suggested_procedures = Column(JSON)  # ["12-Lead ECG", "IV Access", "Aspirin 324mg"]
    
    # Clinical Intelligence
    protocol_recommendations = Column(JSON)  # [{"protocol": "Chest Pain", "confidence": 0.95}]
    drug_interaction_warnings = Column(JSON)  # [{"warning": "Aspirin contraindicated with GI bleed"}]
    differential_diagnosis_suggestions = Column(JSON)
    
    # Documentation Quality Score
    completeness_score = Column(Float)  # 0-100
    missing_fields = Column(JSON)  # ["Chief Complaint", "Past Medical History"]
    suggested_additions = Column(JSON)
    
    # AI Assistance Used
    narrative_accepted = Column(Boolean, default=False)
    assessment_accepted = Column(Boolean, default=False)
    protocol_recommendation_followed = Column(Boolean)
    
    # Learning
    user_feedback = Column(String)  # helpful, not_helpful, incorrect
    feedback_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PredictiveMaintenanceAlert(Base):
    """AI-powered predictive maintenance for vehicles and equipment"""
    __tablename__ = "predictive_maintenance_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    asset_type = Column(String, nullable=False)  # Vehicle, Monitor, Defibrillator, Oxygen System
    asset_id = Column(Integer, nullable=False)
    
    # Prediction
    predicted_failure_date = Column(Date)
    predicted_failure_component = Column(String)
    failure_probability = Column(Float)  # 0-100%
    
    # Data Analysis
    usage_pattern_analysis = Column(JSON)
    anomaly_detected = Column(Boolean, default=False)
    anomaly_description = Column(Text)
    
    # Recommendation
    recommended_action = Column(String)  # Inspect, Service, Replace
    recommended_action_by_date = Column(Date)
    estimated_cost = Column(Float)
    
    # Risk
    risk_level = Column(SQLEnum(AlertSeverity), default=AlertSeverity.INFO)
    operational_impact = Column(String)  # Low, Medium, High, Critical
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    actual_issue_found = Column(Text)
    prediction_accuracy = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# REAL-TIME COLLABORATION
# ============================================================================

class LiveEpcrCollaboration(Base):
    """Real-time ePCR co-authoring session"""
    __tablename__ = "live_epcr_collaboration"
    
    id = Column(Integer, primary_key=True, index=True)
    epcr_id = Column(Integer, ForeignKey("epcr_records.id"), nullable=False)
    
    session_id = Column(String, unique=True, nullable=False, index=True)
    
    # Active Users
    active_users = Column(JSON)  # [{"user_id": 1, "name": "John Doe", "cursor_position": "vitals_section"}]
    
    # Session Status
    session_active = Column(Boolean, default=True)
    session_started_at = Column(DateTime, default=datetime.utcnow)
    session_ended_at = Column(DateTime)
    
    # Collaboration Stats
    total_edits = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamChatMessage(Base):
    """Real-time team chat integrated with incidents"""
    __tablename__ = "team_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Thread (can be incident-based or general)
    thread_type = Column(String, nullable=False)  # incident, station, shift, general
    thread_id = Column(String, nullable=False, index=True)
    
    # Message
    message_text = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # text, image, file, location, voice
    
    # Sender
    sender_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    sender_name = Column(String)
    
    # Attachments
    attachment_url = Column(String)
    attachment_type = Column(String)
    
    # Location Share
    shared_latitude = Column(Float)
    shared_longitude = Column(Float)
    
    # Reactions
    reactions = Column(JSON)  # [{"user_id": 1, "emoji": "👍"}]
    
    # Status
    read_by = Column(JSON)  # [{"user_id": 1, "read_at": "2026-01-27T10:30:00Z"}]
    
    # Threading
    parent_message_id = Column(Integer, ForeignKey("team_chat_messages.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoConferenceSession(Base):
    """Integrated video conferencing for medical consultations"""
    __tablename__ = "video_conference_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    session_id = Column(String, unique=True, nullable=False, index=True)
    
    # Session Type
    session_type = Column(String, nullable=False)  # Medical Director Consult, Peer Consult, Training
    
    # Participants
    participants = Column(JSON)  # [{"user_id": 1, "role": "Paramedic"}, {"user_id": 2, "role": "Medical Director"}]
    
    # Related To
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True)
    qa_case_id = Column(Integer, ForeignKey("qa_cases.id"), nullable=True)
    
    # Video Platform
    platform = Column(String, default="webrtc")  # webrtc, zoom, teams
    meeting_url = Column(String)
    
    # Session Status
    session_active = Column(Boolean, default=True)
    session_started_at = Column(DateTime, default=datetime.utcnow)
    session_ended_at = Column(DateTime)
    session_duration_minutes = Column(Integer)
    
    # Recording
    recording_enabled = Column(Boolean, default=False)
    recording_url = Column(String)
    
    # Notes
    session_notes = Column(Text)
    clinical_decisions_made = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# GAMIFICATION & ENGAGEMENT
# ============================================================================

class PerformanceBadge(Base):
    """Achievement badges for performance milestones"""
    __tablename__ = "performance_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    
    badge_name = Column(String, unique=True, nullable=False)
    badge_description = Column(Text)
    badge_category = Column(String)  # Clinical Excellence, Operational Performance, Safety, Training
    
    # Requirements
    criteria = Column(JSON)  # {"metric": "calls_completed", "threshold": 1000}
    points_value = Column(Integer, default=0)
    
    # Rarity
    rarity = Column(String)  # Common, Uncommon, Rare, Epic, Legendary
    
    # Visual
    badge_icon_url = Column(String)
    badge_color = Column(String)
    
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PersonnelBadgeAward(Base):
    """Personnel badge awards"""
    __tablename__ = "personnel_badge_awards"
    
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("performance_badges.id"), nullable=False)
    
    awarded_at = Column(DateTime, default=datetime.utcnow)
    
    # Achievement Details
    achievement_details = Column(JSON)  # {"calls_completed": 1000, "date_achieved": "2026-01-27"}
    
    # Display
    displayed_on_profile = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Leaderboard(Base):
    """Performance leaderboards"""
    __tablename__ = "leaderboards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    leaderboard_period = Column(String, nullable=False, index=True)  # daily, weekly, monthly, all_time
    leaderboard_type = Column(String, nullable=False)  # calls_completed, documentation_quality, response_time, patient_satisfaction
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Rankings
    rankings = Column(JSON)  # [{"rank": 1, "personnel_id": 1, "score": 98.5}]
    
    # Stats
    total_participants = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformancePoints(Base):
    """Performance points system"""
    __tablename__ = "performance_points"
    
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    
    # Points
    total_points = Column(Integer, default=0)
    points_this_month = Column(Integer, default=0)
    points_this_year = Column(Integer, default=0)
    
    # Level
    current_level = Column(Integer, default=1)
    next_level_points_required = Column(Integer)
    
    # Streaks
    documentation_streak_days = Column(Integer, default=0)
    perfect_response_time_streak = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointsTransaction(Base):
    """Points transaction log"""
    __tablename__ = "points_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    
    points_amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)  # earned, bonus, penalty, redeemed
    
    reason = Column(String, nullable=False)  # "Call Completed", "Documentation Quality", "Badge Earned"
    
    related_call_id = Column(Integer, ForeignKey("cad_calls.id"))
    related_badge_id = Column(Integer, ForeignKey("performance_badges.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# VOICE COMMANDS & HANDS-FREE OPERATION
# ============================================================================

class VoiceCommand(Base):
    """Voice command processing log"""
    __tablename__ = "voice_commands"
    
    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    
    # Voice Input
    voice_input_text = Column(Text, nullable=False)
    voice_confidence_score = Column(Float)
    
    # Command
    command_type = Column(String, nullable=False)  # vitals_entry, medication_entry, navigation, status_update
    command_intent = Column(String)
    
    # Parsed Data
    parsed_data = Column(JSON)  # {"bp_systolic": 120, "bp_diastolic": 80, "hr": 75}
    
    # Execution
    executed_successfully = Column(Boolean, default=True)
    execution_result = Column(Text)
    
    # Context
    call_id = Column(Integer, ForeignKey("cad_calls.id"))
    epcr_id = Column(Integer, ForeignKey("epcr_records.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class VoiceToTextVitals(Base):
    """Voice-to-text vitals entry"""
    __tablename__ = "voice_to_text_vitals"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    
    # Voice Input
    voice_transcript = Column(Text, nullable=False)
    
    # Extracted Vitals
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    heart_rate = Column(Integer)
    respiratory_rate = Column(Integer)
    spo2 = Column(Integer)
    glucose = Column(Integer)
    temperature = Column(Float)
    
    # AI Confidence
    extraction_confidence = Column(Float)
    
    # Validation
    validated_by_user = Column(Boolean, default=False)
    corrected_values = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# AI CLINICAL ASSISTANT
# ============================================================================

class AIProtocolRecommendation(Base):
    """AI-powered protocol recommendations"""
    __tablename__ = "ai_protocol_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    
    # Patient Data Analysis
    chief_complaint = Column(String)
    vitals_analysis = Column(JSON)
    assessment_analysis = Column(JSON)
    
    # Recommendations
    recommended_protocols = Column(JSON)  # [{"protocol": "Chest Pain", "confidence": 0.95, "reasoning": "..."}]
    recommended_interventions = Column(JSON)
    recommended_medications = Column(JSON)
    
    # Warnings
    contraindications = Column(JSON)
    drug_interactions = Column(JSON)
    allergy_warnings = Column(JSON)
    
    # Differential Diagnosis
    differential_diagnoses = Column(JSON)  # [{"diagnosis": "STEMI", "probability": 0.85}]
    
    # AI Confidence
    overall_confidence = Column(Float)
    
    # User Response
    recommendation_followed = Column(Boolean)
    user_feedback = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DrugInteractionCheck(Base):
    """Real-time drug interaction checking"""
    __tablename__ = "drug_interaction_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    
    # Medications Being Administered
    proposed_medication = Column(String, nullable=False)
    proposed_dose = Column(String)
    proposed_route = Column(String)
    
    # Patient Medications
    patient_current_medications = Column(JSON)
    
    # Interaction Analysis
    interactions_found = Column(Boolean, default=False)
    interaction_severity = Column(String)  # Minor, Moderate, Severe, Contraindicated
    interaction_details = Column(JSON)
    
    # Recommendations
    ai_recommendation = Column(String)  # Proceed, Caution, Do Not Administer
    alternative_medications = Column(JSON)
    
    # User Action
    medication_administered = Column(Boolean)
    override_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DifferentialDiagnosisAssistant(Base):
    """AI-powered differential diagnosis suggestions"""
    __tablename__ = "differential_diagnosis_assistant"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=False)
    
    # Patient Presentation
    chief_complaint = Column(String, nullable=False)
    symptoms = Column(JSON)
    vital_signs = Column(JSON)
    physical_exam_findings = Column(JSON)
    
    # AI Analysis
    differential_diagnoses = Column(JSON)  # [{"diagnosis": "STEMI", "probability": 0.85, "supporting_factors": [...], "against_factors": [...]}]
    
    # Most Likely Diagnosis
    most_likely_diagnosis = Column(String)
    probability = Column(Float)
    
    # Clinical Decision Support
    recommended_tests = Column(JSON)  # ["12-Lead ECG", "Troponin"]
    recommended_treatments = Column(JSON)
    
    # Red Flags
    red_flags_identified = Column(JSON)
    time_sensitive_conditions = Column(JSON)  # ["STEMI", "Stroke"]
    
    # User Interaction
    diagnosis_helpful = Column(Boolean)
    actual_working_diagnosis = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
