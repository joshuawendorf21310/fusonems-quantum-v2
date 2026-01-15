from sqlalchemy import Column, DateTime, Integer, JSON, String, func

from core.database import Base


class Patient(Base):
    __tablename__ = "epcr_patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    incident_number = Column(String, nullable=False, index=True)
    vitals = Column(JSON, nullable=False, default=dict)
    interventions = Column(JSON, nullable=False, default=list)
    medications = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
