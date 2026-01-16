from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func

from core.database import FireBase


class FireIncident(FireBase):
    __tablename__ = "fire_incidents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(String, unique=True, nullable=False, index=True)
    incident_type = Column(String, nullable=False)
    incident_category = Column(String, default="Structure")
    incident_subtype = Column(String, default="")
    location = Column(String, nullable=False)
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
    notified_at = Column(DateTime(timezone=True), nullable=True)
    enroute_at = Column(DateTime(timezone=True), nullable=True)
    on_scene_at = Column(DateTime(timezone=True), nullable=True)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, default="")
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FireApparatus(FireBase):
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


class FireApparatusInventory(FireBase):
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


class FirePersonnel(FireBase):
    __tablename__ = "fire_personnel"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    certifications = Column(Text, default="")
    status = Column(String, default="Active")


class FireIncidentApparatus(FireBase):
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


class FireIncidentPersonnel(FireBase):
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


class FireTrainingRecord(FireBase):
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


class FirePreventionRecord(FireBase):
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


class FireAuditLog(FireBase):
    __tablename__ = "fire_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    classification = Column(String, default="LEGAL_HOLD")
    training_mode = Column(Boolean, default=False)
    incident_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FireExportRecord(FireBase):
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
