import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        JSON, String, func)
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base

# Document extraction snapshot for AI/deterministic extraction
class TransportDocType(str, enum.Enum):
    PCS = "PCS"
    AOB = "AOB"
    ABD = "ABD"
    FACESHEET = "FACESHEET"


class TransportTrip(Base):
    __tablename__ = "transport_trips"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    transport_type = Column(String, default="ift")
    status = Column(String, default="requested")
    requested_by = Column(String, default="")
    origin_facility = Column(String, default="")
    origin_address = Column(String, default="")
    destination_facility = Column(String, default="")
    destination_address = Column(String, default="")
    broker_trip_id = Column(String, default="")
    broker_name = Column(String, default="")
    broker_service_type = Column(String, default="")
    broker_account_id = Column(String, default="")
    epcr_patient_id = Column(Integer, ForeignKey("epcr_patients.id"), nullable=True, index=True)
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("cad_dispatches.id"), nullable=True, index=True)
    unit_id = Column(Integer, ForeignKey("cad_units.id"), nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    medical_necessity_status = Column(String, default="pending")
    medical_necessity_notes = Column(String, default="")
    medical_necessity_checked_at = Column(DateTime(timezone=True), nullable=True)
    pcs_provided = Column(Boolean, default=False)
    pcs_reference = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class TransportLeg(Base):
    __tablename__ = "transport_legs"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("transport_trips.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classification = Column(String, default="PHI")
    training_mode = Column(Boolean, default=False)
    leg_number = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False)
    origin_facility = Column(String, default="")
    origin_address = Column(String, default="")
    destination_facility = Column(String, default="")
    destination_address = Column(String, default="")
    notes = Column(String, default="")
    call_id = Column(Integer, ForeignKey("cad_calls.id"), nullable=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("cad_dispatches.id"), nullable=True, index=True)
    unit_id = Column(Integer, ForeignKey("cad_units.id"), nullable=True, index=True)
    distance_miles = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TransportDocumentSnapshot(Base):
    __tablename__ = "transport_document_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("transport_trips.id"), nullable=False, index=True)
    doc_type = Column(String, nullable=False, index=True)
    file_id = Column(String, nullable=True)
    extracted_json = Column(JSON, nullable=False)
    confidence_json = Column(JSON, nullable=False)
    evidence_json = Column(JSON, nullable=False)
    warnings_json = Column(JSON, nullable=True)
    provider = Column(String, nullable=False, default="deterministic")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
