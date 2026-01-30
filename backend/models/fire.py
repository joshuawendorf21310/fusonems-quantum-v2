from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class FireIncident(Base):
    __tablename__ = "fire_incidents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(String, unique=True, nullable=False, index=True)
    incident_number = Column(String, unique=True, nullable=False, index=True)
    incident_type = Column(String, nullable=False)
    incident_category = Column(String, default="Structure")
    incident_subtype = Column(String, default="")
    neris_category = Column(String, default="")
    local_descriptor = Column(String, default="")
    location = Column(String, nullable=False)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    alarm_datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    priority = Column(String, default="Routine")
    status = Column(String, default="Open")
    hybrid_ems = Column(Boolean, default=False)
    ems_incident_id = Column(String, default="")
    nfirs_status = Column(String, default="Draft")
    neris_status = Column(String, default="Draft")
    loss_estimate = Column(Float, default=0.0)
    property_use = Column(String, default="")
    situation_found = Column(String, default="")
    narrative = Column(Text, default="")
    ai_summary = Column(Text, default="")
    responding_units = Column(JSON, nullable=False, default=list)
    actions_taken = Column(Text, default="")
    exposures = Column(JSON, nullable=False, default=list)
    civilian_casualties = Column(Integer, default=0)
    civilian_casualty_details = Column(Text, default="")
    firefighter_casualties = Column(Integer, default=0)
    firefighter_casualty_details = Column(Text, default="")
    notified_at = Column(DateTime(timezone=True), nullable=True)
    enroute_at = Column(DateTime(timezone=True), nullable=True)
    on_scene_at = Column(DateTime(timezone=True), nullable=True)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, default="")
    approved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)


class FireApparatus(Base):
    __tablename__ = "fire_apparatus"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    apparatus_id = Column(String, unique=True, nullable=False, index=True)
    apparatus_type = Column(String, nullable=False)
    status = Column(String, default="In Service")
    mileage = Column(Integer, default=0)
    readiness_score = Column(Integer, default=100)


class FireApparatusInventory(Base):
    __tablename__ = "fire_apparatus_inventory"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    apparatus_id = Column(Integer, ForeignKey("fire_apparatus.id"), nullable=False)
    item_name = Column(String, nullable=False)
    status = Column(String, default="Ready")
    quantity = Column(Integer, default=1)
    notes = Column(Text, default="")



class FireIncidentApparatus(Base):
    __tablename__ = "fire_incident_apparatus"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(Integer, ForeignKey("fire_incidents.id"), nullable=False)
    apparatus_id = Column(Integer, ForeignKey("fire_apparatus.id"), nullable=False)
    role = Column(String, default="Primary")
    status = Column(String, default="Assigned")
    notes = Column(Text, default="")


class FireIncidentPersonnel(Base):
    __tablename__ = "fire_incident_personnel"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(Integer, ForeignKey("fire_incidents.id"), nullable=False)
    personnel_id = Column(Integer, ForeignKey("fire_personnel.id"), nullable=False)
    role = Column(String, default="Responder")
    status = Column(String, default="Assigned")
    notes = Column(Text, default="")


class FireTrainingRecord(Base):
    __tablename__ = "fire_training_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    training_type = Column(String, nullable=False)
    crew = Column(String, nullable=False)
    status = Column(String, default="Planned")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FirePreventionRecord(Base):
    __tablename__ = "fire_prevention_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    occupancy_name = Column(String, nullable=False)
    inspection_status = Column(String, default="Scheduled")
    hydrant_map = Column(Text, default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FireAuditLog(Base):
    __tablename__ = "fire_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="LEGAL_HOLD")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FireExportRecord(Base):
    __tablename__ = "fire_exports"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    export_type = Column(String, default="NFIRS")
    incident_id = Column(String, default="")
    status = Column(String, default="generated")
    payload = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FireIncidentTimeline(Base):
    __tablename__ = "fire_incident_timeline"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(Integer, ForeignKey("fire_incidents.id"), nullable=False)
    incident_identifier = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    notes = Column(Text, default="")
    event_data = Column(JSON, nullable=False, default=dict)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class FireInventoryHook(Base):
    __tablename__ = "fire_inventory_hooks"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(Integer, ForeignKey("fire_incidents.id"), nullable=False)
    incident_identifier = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    usage_summary = Column(Text, default="")
    notes = Column(Text, default="")
    reported_by = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Fire911Transport(Base):
    __tablename__ = "fire_911_transports"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    
    incident_id = Column(String, nullable=False, index=True)
    transport_id = Column(String, unique=True, nullable=False, index=True)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    phone = Column(String, default="")
    address = Column(String, default="")
    
    chief_complaint = Column(String, nullable=False)
    chief_complaint_icd10 = Column(String, default="")
    
    vitals = Column(JSON, nullable=False, default=dict)
    assessment = Column(Text, default="")
    
    interventions = Column(JSON, nullable=False, default=list)
    medications = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    
    transport_decision = Column(String, default="Transport")
    transport_destination = Column(String, default="")
    transport_mode = Column(String, default="Ground")
    
    responding_unit = Column(String, default="")
    responding_personnel = Column(JSON, nullable=False, default=list)
    
    narrative = Column(Text, default="")
    status = Column(String, default="Draft")
    
    scene_time = Column(DateTime(timezone=True), nullable=True)
    transport_initiated_time = Column(DateTime(timezone=True), nullable=True)
    arrival_at_hospital_time = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Fire911TransportTimeline(Base):
    __tablename__ = "fire_911_transport_timeline"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    
    transport_id = Column(Integer, ForeignKey("fire_911_transports.id"), nullable=False)
    transport_identifier = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    notes = Column(Text, default="")
    event_data = Column(JSON, nullable=False, default=dict)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
