from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func

from core.database import Base


class MedicationMaster(Base):
    __tablename__ = "medication_master"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, default="")
    drug_class = Column(String, default="")
    schedule = Column(String, default="non_controlled")
    concentration = Column(String, default="")
    routes = Column(JSON, nullable=False, default=list)
    status = Column(String, default="active")
    classification = Column(String, default="OPS")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicationAdministration(Base):
    __tablename__ = "medication_administrations"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    patient_id = Column(Integer, nullable=True)
    medication_name = Column(String, nullable=False)
    dose = Column(String, default="")
    dose_units = Column(String, default="")
    route = Column(String, default="")
    time_administered = Column(String, default="")
    notes = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicationFormularyVersion(Base):
    __tablename__ = "medication_formulary_versions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    version = Column(String, default="v1")
    status = Column(String, default="active")
    notes = Column(String, default="")
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
