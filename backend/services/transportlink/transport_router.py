from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.cad import Call, Dispatch, Unit
from models.epcr import MasterPatientLink, Patient
from models.transportlink import TransportLeg, TransportTrip
from models.user import User, UserRole
from utils.tenancy import get_scoped_record
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(
    prefix="/api/transport",
    tags=["TransportLink"],
    dependencies=[Depends(require_module("TRANSPORTLINK"))],
)


class TripCreate(BaseModel):
    transport_type: str = Field(default="ift")
    requested_by: str | None = None
    origin_facility: str
    origin_address: str
    destination_facility: str
    destination_address: str
    broker_trip_id: str | None = None
    broker_name: str | None = None
    broker_service_type: str | None = None
    broker_account_id: str | None = None
    epcr_patient_id: int | None = None
    call_id: int | None = None
    dispatch_id: int | None = None
    unit_id: int | None = None
    metadata: dict[str, str] | None = Field(default_factory=dict)


class TripResponse(BaseModel):
    id: int
    status: str

    class Config:
        from_attributes = True


class MedicalNecessityUpdate(BaseModel):
    medical_necessity_status: str = Field(default="approved")
    medical_necessity_notes: str = ""
    pcs_provided: bool = True
    pcs_reference: str = ""


class LegCreate(BaseModel):
    trip_id: int
    leg_number: int
    status: str
    origin_facility: str
    origin_address: str
    destination_facility: str
    destination_address: str
    notes: str | None = ""
    distance_miles: float | None = None
    call_id: int | None = None
    dispatch_id: int | None = None
    unit_id: int | None = None


class LegResponse(BaseModel):
    id: int
    trip_id: int
    status: str

    class Config:
        from_attributes = True


class CompletionRequest(BaseModel):
    completed_at: datetime | None = None


def _ensure_unit(db: Session, user: User, request: Request, unit_id: int) -> Unit:
    return get_scoped_record(db, request, Unit, unit_id, user, resource_label="cad_unit")


def _ensure_dispatch(db: Session, user: User, request: Request, dispatch_id: int) -> Dispatch:
    return get_scoped_record(db, request, Dispatch, dispatch_id, user, resource_label="cad_dispatch")


def _ensure_call(db: Session, user: User, request: Request, call_id: int) -> Call:
    return get_scoped_record(db, request, Call, call_id, user, resource_label="cad_call")


def _ensure_epcr_patient_linked(db: Session, request: Request, user: User, patient_id: int) -> Patient:
    patient = get_scoped_record(db, request, Patient, patient_id, user, resource_label="epcr")
    link_exists = (
        db.query(MasterPatientLink)
        .filter(MasterPatientLink.epcr_patient_id == patient.id)
        .first()
    )
    if not link_exists:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Master patient link required")
    return patient


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    if payload.epcr_patient_id:
        _ensure_epcr_patient_linked(db, request, user, payload.epcr_patient_id)
    if payload.call_id:
        _ensure_call(db, user, request, payload.call_id)
    if payload.dispatch_id:
        _ensure_dispatch(db, user, request, payload.dispatch_id)
    if payload.unit_id:
        _ensure_unit(db, user, request, payload.unit_id)
    trip = TransportTrip(
        org_id=user.org_id,
        transport_type=payload.transport_type,
        requested_by=payload.requested_by or user.full_name,
        origin_facility=payload.origin_facility,
        origin_address=payload.origin_address,
        destination_facility=payload.destination_facility,
        destination_address=payload.destination_address,
        broker_trip_id=payload.broker_trip_id or "",
        broker_name=payload.broker_name or "",
        broker_service_type=payload.broker_service_type or "",
        broker_account_id=payload.broker_account_id or "",
        epcr_patient_id=payload.epcr_patient_id,
        call_id=payload.call_id,
        dispatch_id=payload.dispatch_id,
        unit_id=payload.unit_id,
        payload=payload.metadata or {},
        medical_necessity_status="pending",
    )
    apply_training_mode(trip, request)
    db.add(trip)
    try:
        db.commit()
        db.refresh(trip)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="transport_trip",
            classification=trip.classification,
            after_state=model_snapshot(trip),
            event_type="transport.trip.created",
            event_payload={
                "trip_id": trip.id,
                "transport_type": trip.transport_type,
                "call_id": trip.call_id,
                "dispatch_id": trip.dispatch_id,
                "unit_id": trip.unit_id,
            },
        )
    except Exception as e:
        db.rollback()
        raise
    return trip


@router.post("/{trip_id}/medical_necessity", status_code=status.HTTP_200_OK)
def update_medical_necessity(
    trip_id: int,
    payload: MedicalNecessityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    trip = get_scoped_record(db, request, TransportTrip, trip_id, user, resource_label="transport_trip")
    before_state = model_snapshot(trip)
    trip.medical_necessity_status = payload.medical_necessity_status
    trip.medical_necessity_notes = payload.medical_necessity_notes
    trip.medical_necessity_checked_at = datetime.utcnow()
    trip.pcs_provided = payload.pcs_provided
    trip.pcs_reference = payload.pcs_reference
    apply_training_mode(trip, request)
    try:
        db.commit()
        db.refresh(trip)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="update",
            resource="transport_trip",
            classification=trip.classification,
            before_state=before_state,
            after_state=model_snapshot(trip),
            event_type="transport.trip.medical_necessity.updated",
            event_payload={"trip_id": trip.id, "status": trip.medical_necessity_status},
        )
    except Exception as e:
        db.rollback()
        raise
    return {"status": "ok"}


@router.post("/legs", response_model=LegResponse, status_code=status.HTTP_201_CREATED)
def create_leg(
    payload: LegCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    trip = get_scoped_record(db, request, TransportTrip, payload.trip_id, user, resource_label="transport_trip")
    if payload.call_id:
        _ensure_call(db, user, request, payload.call_id)
    if payload.dispatch_id:
        _ensure_dispatch(db, user, request, payload.dispatch_id)
    if payload.unit_id:
        _ensure_unit(db, user, request, payload.unit_id)
    leg = TransportLeg(
        trip_id=trip.id,
        org_id=user.org_id,
        leg_number=payload.leg_number,
        status=payload.status,
        origin_facility=payload.origin_facility,
        origin_address=payload.origin_address,
        destination_facility=payload.destination_facility,
        destination_address=payload.destination_address,
        notes=payload.notes or "",
        call_id=payload.call_id,
        dispatch_id=payload.dispatch_id,
        unit_id=payload.unit_id,
        distance_miles=payload.distance_miles,
    )
    apply_training_mode(leg, request)
    db.add(leg)
    try:
        db.commit()
        db.refresh(leg)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="transport_leg",
            classification=leg.classification,
            after_state=model_snapshot(leg),
            event_type="transport.leg.created",
            event_payload={"trip_id": trip.id, "leg_id": leg.id},
        )
    except Exception as e:
        db.rollback()
        raise
    return leg


@router.post("/{trip_id}/complete", status_code=status.HTTP_200_OK)
def complete_trip(
    trip_id: int,
    payload: CompletionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    trip = get_scoped_record(db, request, TransportTrip, trip_id, user, resource_label="transport_trip")
    if trip.medical_necessity_status not in {"approved", "verified"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Medical necessity not approved",
        )
    if not trip.pcs_provided:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PCS required before completion",
        )
    legs = (
        db.query(TransportLeg)
        .filter(TransportLeg.trip_id == trip.id)
        .order_by(TransportLeg.leg_number.asc())
        .all()
    )
    if not legs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one leg required",
        )
    before_state = model_snapshot(trip)
    trip.status = "completed"
    trip.completed_at = payload.completed_at or datetime.utcnow()
    apply_training_mode(trip, request)
    try:
        db.commit()
        db.refresh(trip)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="update",
            resource="transport_trip",
            classification=trip.classification,
            before_state=before_state,
            after_state=model_snapshot(trip),
            event_type="transport.trip.completed",
            event_payload={
                "trip_id": trip.id,
                "legs": [model_snapshot(leg) for leg in legs],
                "distance_miles": sum(leg.distance_miles or 0.0 for leg in legs),
            },
        )
    except Exception as e:
        db.rollback()
        raise
    return {"status": "completed", "trip_id": trip.id}
