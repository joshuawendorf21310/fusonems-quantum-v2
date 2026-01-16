from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func

from core.config import settings
from core.database import HemsBase

HEMS_SCHEMA = None if settings.DATABASE_URL.startswith("sqlite") else "hems"
SCHEMA_ARGS = {"schema": HEMS_SCHEMA} if HEMS_SCHEMA else {}
SCHEMA_PREFIX = f"{HEMS_SCHEMA}." if HEMS_SCHEMA else ""


class HemsMission(HemsBase):
    __tablename__ = "hems_missions"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    mission_type = Column(String, default="scene")
    requesting_party = Column(String, default="")
    patient_global_id = Column(String, default="")
    pickup_location = Column(String, nullable=False)
    destination_location = Column(String, nullable=False)
    status = Column(String, default="intake")
    risk_score = Column(Float, default=0.0)
    correlation_id = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsMissionTimeline(HemsBase):
    __tablename__ = "hems_mission_timeline"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    status = Column(String, nullable=False)
    notes = Column(Text, default="")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsAircraft(HemsBase):
    __tablename__ = "hems_aircraft"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="AVIATION_SAFETY")
    training_mode = Column(Boolean, default=False)
    tail_number = Column(String, nullable=False, unique=True)
    capability_flags = Column(JSON, nullable=False, default=dict)
    availability = Column(String, default="Available")
    maintenance_status = Column(String, default="Green")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsCrew(HemsBase):
    __tablename__ = "hems_crew"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    duty_status = Column(String, default="Ready")
    readiness_flags = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsAssignment(HemsBase):
    __tablename__ = "hems_assignments"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    crew_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_crew.id"), nullable=False)
    aircraft_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_aircraft.id"), nullable=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    assignment_role = Column(String, default="")
    status = Column(String, default="Assigned")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsRiskAssessment(HemsBase):
    __tablename__ = "hems_risk_assessments"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="AVIATION_SAFETY")
    training_mode = Column(Boolean, default=False)
    weather_summary = Column(Text, default="")
    risk_score = Column(Float, default=0.0)
    constraints = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsChart(HemsBase):
    __tablename__ = "hems_charts"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    vitals_trends = Column(JSON, nullable=False, default=dict)
    ventilator_settings = Column(JSON, nullable=False, default=dict)
    infusions = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    handoff_summary = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsHandoff(HemsBase):
    __tablename__ = "hems_handoffs"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    receiving_clinician = Column(String, default="")
    signature = Column(String, default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsBillingPacket(HemsBase):
    __tablename__ = "hems_billing_packets"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="BILLING_SENSITIVE")
    training_mode = Column(Boolean, default=False)
    transport_type = Column(String, default="scene")
    miles = Column(Float, default=0.0)
    time_minutes = Column(Integer, default=0)
    justification = Column(Text, default="")
    export_status = Column(String, default="Pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsIncidentLink(HemsBase):
    __tablename__ = "hems_incident_links"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    ground_incident_id = Column(String, default="")
    epcr_id = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HemsQualityReview(HemsBase):
    __tablename__ = "hems_quality_reviews"
    __table_args__ = SCHEMA_ARGS

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=False)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    reviewer = Column(String, default="")
    status = Column(String, default="open")
    determination = Column(String, default="pending")
    notes = Column(Text, default="")
    compliance_flags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
