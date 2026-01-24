from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class Patient(Base):
    __tablename__ = "epcr_patients"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    nemsis_version = Column(String, default="3.5.1")
    nemsis_state = Column(String, default="WI")
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    phone = Column(String, default="")
    address = Column(String, default="")
    incident_number = Column(String, nullable=False, index=True)
    vitals = Column(JSON, nullable=False, default=dict)
    interventions = Column(JSON, nullable=False, default=list)
    medications = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    labs = Column(JSON, nullable=False, default=list)
    cct_interventions = Column(JSON, nullable=False, default=list)
    ocr_snapshots = Column(JSON, nullable=False, default=list)
    narrative = Column(String, default="")
    chart_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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
