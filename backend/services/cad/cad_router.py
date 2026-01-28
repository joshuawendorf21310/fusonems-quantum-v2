from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Literal

import anyio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.cad import CADIncident, CADIncidentTimeline, Call, Dispatch, Unit
from models.user import User, UserRole
from services.cad.helpers import record_mdt_sync_event
from utils.logger import logger
from utils.tenancy import get_scoped_record, scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import get_scoped_record, scoped_query

router = APIRouter(
    prefix="/api/cad",
    tags=["CAD"],
    dependencies=[Depends(require_module("CAD"))],
)


class CallCreate(BaseModel):
    caller_name: str
    caller_phone: str
    location_address: str
    latitude: float
    longitude: float
    priority: str = "Routine"


class CallResponse(BaseModel):
    id: int
    caller_name: str
    caller_phone: str
    location_address: str
    latitude: float
    longitude: float
    priority: str
    status: str
    eta_minutes: int | None

    class Config:
        from_attributes = True


class UnitCreate(BaseModel):
    unit_identifier: str
    unit_type: Literal["BLS", "ALS", "CCT"] = "BLS"
    status: str = "Available"
    latitude: float = 0.0
    longitude: float = 0.0


class DispatchRequest(BaseModel):
    call_id: int
    unit_identifier: str


class UnitStatusUpdate(BaseModel):
    status: Literal[
        "available",
        "assigned",
        "enroute_to_pickup",
        "on_scene",
        "transporting",
        "at_destination",
    ]
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None


UNIT_STATUS_TO_INCIDENT = {
    "assigned": "assigned",
    "enroute_to_pickup": "enroute_to_pickup",
    "on_scene": "on_scene",
    "transporting": "transporting",
    "at_destination": "at_destination",
}

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(
        dlon / 2
    ) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _estimate_eta(distance_km: float, speed_kph: float = 60.0) -> int:
    if speed_kph <= 0:
        return 0
    return max(1, int((distance_km / speed_kph) * 60))


def _broadcast_update(org_id: int, payload: dict) -> None:
    try:
        anyio.from_thread.run(cad_live_manager.broadcast, org_id, payload)
    except RuntimeError:
        logger.info("CAD live broadcast skipped: no event loop")


def _set_unit_status(unit: Unit, status: str) -> None:
    status_map = {
        "Enroute": "En Route",
        "OnScene": "On Scene",
        "Transport": "Transporting",
        "Available": "Available",
        "Dispatched": "En Route",
    }
    unit.status = status_map.get(status, status)


@router.post("/calls", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
def create_call(
    payload: CallCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = Call(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(call, request)
    db.add(call)
    db.commit()
    db.refresh(call)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_call",
        classification=call.classification,
        after_state=model_snapshot(call),
        event_type="cad.call.created",
        event_payload={"call_id": call.id, "priority": call.priority},
    )
    logger.info("Call logged %s", call.id)
    _broadcast_update(
        user.org_id,
        {"event": "cad.call.created", "call_id": call.id, "priority": call.priority},
    )
    return call


@router.get("/calls", response_model=list[CallResponse])
def list_calls(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, Call, user.org_id, request.state.training_mode).order_by(
        Call.created_at.desc()
    ).all()


@router.get("/units")
def get_units(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    units = scoped_query(db, Unit, user.org_id, request.state.training_mode).order_by(
        Unit.unit_identifier.asc()
    ).all()
    return {"active_units": units}


@router.post("/units", status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    unit = Unit(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(unit, request)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_unit",
        classification=unit.classification,
        after_state=model_snapshot(unit),
        event_type="cad.unit.created",
        event_payload={"unit_identifier": unit.unit_identifier},
    )
    _broadcast_update(
        user.org_id,
        {"event": "cad.unit.created", "unit_identifier": unit.unit_identifier},
    )
    return unit


def _dispatch_to_unit(
    *,
    call: Call,
    unit: Unit,
    request: Request,
    db: Session,
    user: User,
) -> dict:
    call_before = model_snapshot(call)
    unit_before = model_snapshot(unit)
    distance_km = _haversine(call.latitude, call.longitude, unit.latitude, unit.longitude)
    eta_minutes = _estimate_eta(distance_km)
    call.eta_minutes = eta_minutes
    call.status = "Dispatched"
    _set_unit_status(unit, "Dispatched")
    dispatch = Dispatch(call_id=call.id, unit_id=unit.id, status="Dispatched", org_id=user.org_id)
    apply_training_mode(dispatch, request)
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_call",
        classification=call.classification,
        before_state=call_before,
        after_state=model_snapshot(call),
        event_type="cad.call.dispatched",
        event_payload={"call_id": call.id, "unit_identifier": unit.unit_identifier},
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_unit",
        classification=unit.classification,
        before_state=unit_before,
        after_state=model_snapshot(unit),
        event_type="cad.unit.dispatched",
        event_payload={"call_id": call.id, "status": call.status},
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_dispatch",
        classification=dispatch.classification,
        after_state=model_snapshot(dispatch),
        event_type="cad.dispatch.created",
        event_payload={"dispatch_id": dispatch.id, "call_id": call.id},
    )
    _broadcast_update(
        user.org_id,
        {
            "event": "cad.dispatch.created",
            "call_id": call.id,
            "unit_identifier": unit.unit_identifier,
        },
    )
    logger.info("Dispatching %s to call %s", unit.unit_identifier, call.id)
    return {"status": "dispatched", "eta_minutes": eta_minutes}


@router.patch("/units/{unit_id}/status")
def update_unit_status(
    unit_id: int,
    payload: UnitStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    unit = get_scoped_record(db, request, Unit, unit_id, user, resource_label="cad_unit")
    before_unit = model_snapshot(unit)
    unit.status = payload.status
    if payload.latitude is not None:
        unit.latitude = payload.latitude
    if payload.longitude is not None:
        unit.longitude = payload.longitude
    unit.last_update = datetime.utcnow()
    apply_training_mode(unit, request)
    db.add(unit)

    incident = (
        scoped_query(db, CADIncident, user.org_id, request.state.training_mode)
        .filter(CADIncident.assigned_unit_id == unit.id)
        .order_by(CADIncident.created_at.desc())
        .first()
    )
    if incident and payload.status in UNIT_STATUS_TO_INCIDENT:
        before_incident = model_snapshot(incident)
        incident.status = UNIT_STATUS_TO_INCIDENT[payload.status]
        incident.updated_at = datetime.utcnow()
        timeline = CADIncidentTimeline(
            org_id=incident.org_id,
            incident_id=incident.id,
            status=incident.status,
            notes=payload.notes or "Unit status updated",
            payload={
                "unit_status": payload.status,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
            },
            recorded_by_id=user.id,
        )
        apply_training_mode(timeline, request)
        db.add(timeline)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="update",
            resource="cad_incident",
            classification=incident.classification,
            before_state=before_incident,
            after_state=model_snapshot(incident),
            event_type="cad.incident.status.updated",
            event_payload={"incident_id": incident.id, "status": incident.status},
        )
        record_mdt_sync_event(
            db=db,
            request=request,
            user=user,
            incident=incident,
            event_type="cad.incident.status.updated",
            payload={"status": incident.status, "actor_role": user.role},
            unit_id=unit.id,
        )

    record_mdt_sync_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="cad.unit.status",
        payload={"unit_status": payload.status},
        unit_id=unit.id,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_unit",
        classification=unit.classification,
        before_state=before_unit,
        after_state=model_snapshot(unit),
        event_type="cad.unit.status",
        event_payload={"unit_id": unit.id, "status": unit.status},
    )
    db.commit()
    return {"status": "ok"}


class DispatchMessagePayload(BaseModel):
    unit_id: str
    message_id: str
    message_text: str
    priority: Literal["normal", "urgent", "critical"]
    notes: str | None = None


@router.post("/dispatch-message")
def send_dispatch_message(
    payload: DispatchMessagePayload,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.crew)),
):
    """
    MDT → CAD canned message (operational only)
    """
    unit = scoped_query(db, Unit, user.org_id, request.state.training_mode).filter(
        Unit.unit_identifier == payload.unit_id
    ).first()
    
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    
    # Create audit event for dispatch visibility
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="dispatch_message",
        classification="OPS",
        event_type="cad.dispatch_message.sent",
        event_payload={
            "unit_id": payload.unit_id,
            "message_id": payload.message_id,
            "message_text": payload.message_text,
            "priority": payload.priority,
            "notes": payload.notes,
            "user_id": user.id,
        },
    )
    
    logger.info(f"Dispatch message from {payload.unit_id}: {payload.message_text}")
    return {"status": "sent", "timestamp": datetime.utcnow().isoformat()}


class MileageStartPayload(BaseModel):
    odometer: float
    photo: str | None = None


class MileageEndPayload(BaseModel):
    odometer: float
    photo: str | None = None


@router.get("/mileage")
def get_mileage_entries(
    unit_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.crew)),
):
    """
    Get mileage entries for a unit
    """
    unit = scoped_query(db, Unit, user.org_id, request.state.training_mode).filter(
        Unit.unit_identifier == unit_id
    ).first()
    
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    
    # Find active incident
    active_incident = (
        scoped_query(db, CADIncident, user.org_id, request.state.training_mode)
        .filter(
            CADIncident.assigned_unit_id == unit.id,
            CADIncident.status.in_(["assigned", "enroute_to_pickup", "on_scene", "transporting"])
        )
        .order_by(CADIncident.created_at.desc())
        .first()
    )
    
    # Mock data for now - in production, store in separate mileage table
    active_entry = None
    if active_incident:
        active_entry = {
            "id": f"mile_{active_incident.id}",
            "incident_id": str(active_incident.id),
            "incident_number": f"T{active_incident.id:06d}",
            "unit_id": unit_id,
            "start_odometer": None,  # Would come from DB
            "end_odometer": None,
            "gps_distance_km": active_incident.distance_meters / 1000 if active_incident.distance_meters else 0,
            "route_distance_km": active_incident.distance_meters / 1000 if active_incident.distance_meters else 0,
            "start_time": active_incident.created_at.isoformat(),
            "pickup_facility": active_incident.requesting_facility or "Unknown",
            "destination_facility": active_incident.receiving_facility or "Unknown",
            "status": "in_progress",
        }
    
    return {
        "active_entry": active_entry,
        "entries": [],  # Recent completed entries would come from mileage table
    }


@router.post("/mileage/{mileage_id}/start")
def record_start_mileage(
    mileage_id: str,
    payload: MileageStartPayload,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.crew)),
):
    """
    Record start odometer reading
    """
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="mileage_entry",
        classification="OPS",
        event_type="cad.mileage.start",
        event_payload={
            "mileage_id": mileage_id,
            "odometer": payload.odometer,
            "has_photo": payload.photo is not None,
            "user_id": user.id,
        },
    )
    
    logger.info(f"Start mileage recorded: {mileage_id} = {payload.odometer}")
    return {"status": "recorded", "timestamp": datetime.utcnow().isoformat()}


@router.post("/mileage/{mileage_id}/end")
def record_end_mileage(
    mileage_id: str,
    payload: MileageEndPayload,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.crew)),
):
    """
    Record end odometer reading
    """
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="mileage_entry",
        classification="OPS",
        event_type="cad.mileage.end",
        event_payload={
            "mileage_id": mileage_id,
            "odometer": payload.odometer,
            "has_photo": payload.photo is not None,
            "user_id": user.id,
        },
    )
    
    logger.info(f"End mileage recorded: {mileage_id} = {payload.odometer}")
    return {"status": "recorded", "timestamp": datetime.utcnow().isoformat()}


