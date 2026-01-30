from __future__ import annotations

from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.cad import CADIncident, CADIncidentTimeline, Unit
from models.transportlink import TransportTrip
from models.user import User, UserRole
from services.cad.helpers import create_crewlink_page, record_mdt_sync_event
from utils.tenancy import get_scoped_record, scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

ACTIVE_INCIDENT_STATUSES = {
    "pending",
    "assigned",
    "enroute_to_pickup",
    "on_scene",
    "transporting",
    "at_destination",
}
FINAL_INCIDENT_STATUSES = {"completed", "cancelled"}

STATUS_TO_TRANSPORT_STATE = {
    "pending": "requested",
    "assigned": "dispatched",
    "enroute_to_pickup": "enroute",
    "on_scene": "on_scene",
    "transporting": "transport",
    "at_destination": "completed",
    "completed": "completed",
    "cancelled": "cancelled",
}

TRANSPORT_TYPE_UNIT_MAP = {
    "CCT": {"CCT"},
    "IFT": {"BLS", "ALS"},
    "NEMT": {"BLS", "ALS"},
}


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class IncidentCreate(BaseModel):
    requesting_facility: str
    receiving_facility: str
    transport_type: Literal["IFT", "NEMT", "CCT"]
    priority: str = "Routine"
    scheduled_time: datetime | None = None
    transport_link_trip_id: int | None = None
    distance_meters: float | None = None
    eta_minutes: int | None = None
    route_geometry: list[GeoPoint] | None = None
    notes: str | None = None


class IncidentAssignment(BaseModel):
    unit_id: int
    eta_minutes: int | None = None
    distance_meters: float | None = None
    route_geometry: list[GeoPoint] | None = None


class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "assigned",
        "enroute_to_pickup",
        "on_scene",
        "transporting",
        "at_destination",
        "completed",
        "cancelled",
    ]
    notes: str | None = None
    priority: str | None = None
    scheduled_time: datetime | None = None
    eta_minutes: int | None = None
    distance_meters: float | None = None
    route_geometry: list[GeoPoint] | None = None


class IncidentTimelineEntry(BaseModel):
    status: str
    notes: str
    recorded_at: datetime
    payload: dict

    class Config:
        from_attributes = True


class CrewLinkHistoryEntry(BaseModel):
    event_type: str
    title: str
    message: str
    payload: dict
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: int
    requesting_facility: str
    receiving_facility: str
    transport_type: str
    priority: str
    status: str
    scheduled_time: datetime | None
    transport_link_trip_id: int | None
    assigned_unit_id: int | None
    eta_minutes: int | None
    distance_meters: float | None
    route_geometry: list[GeoPoint]
    notes: str
    timeline_entries: list[IncidentTimelineEntry]
    crewlink_messages: list[CrewLinkHistoryEntry]

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/api/cad/incidents",
    tags=["CAD"],
    dependencies=[Depends(require_module("CAD"))],
)


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_m * asin(sqrt(a))


def _estimate_eta(distance_meters: float, speed_mps: float = 15.0) -> int:
    if distance_meters <= 0:
        return 0
    minutes = distance_meters / (speed_mps * 60)
    return max(1, int(minutes))


def _ensure_single_active_incident(
    db: Session,
    user: User,
    trip_id: int,
    training_mode: bool,
    exclude_id: int | None = None,
) -> None:
    query = scoped_query(db, CADIncident, user.org_id, training_mode).filter(
        CADIncident.transport_link_trip_id == trip_id,
        CADIncident.status.in_(list(ACTIVE_INCIDENT_STATUSES)),
    )
    if exclude_id is not None:
        query = query.filter(CADIncident.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active incident already linked to this TransportLink trip",
        )


def _record_timeline(
    db: Session,
    incident: CADIncident,
    status: str,
    user_id: int | None,
    notes: str = "",
    payload: dict | None = None,
) -> CADIncidentTimeline:
    entry = CADIncidentTimeline(
        org_id=incident.org_id,
        incident_id=incident.id,
        status=status,
        notes=notes or "",
        payload=payload or {},
        recorded_by_id=user_id,
    )
    db.add(entry)
    return entry


def _update_transport_trip_status(
    db: Session,
    request: Request,
    user: User,
    incident: CADIncident,
    status: str,
) -> None:
    if not incident.transport_link_trip_id:
        return
    trip = get_scoped_record(
        db,
        request,
        TransportTrip,
        incident.transport_link_trip_id,
        user,
        resource_label="transport_trip",
    )
    before_state = model_snapshot(trip)
    trip.status = STATUS_TO_TRANSPORT_STATE.get(status, trip.status)
    trip.unit_id = incident.assigned_unit_id
    trip.payload = {**(trip.payload or {}), "cad_incident_id": incident.id}
    apply_training_mode(trip, request)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="transport_trip",
        classification=trip.classification,
        before_state=before_state,
        after_state=model_snapshot(trip),
        event_type="transport.trip.status.updated",
        event_payload={"trip_id": trip.id, "status": trip.status},
    )


def _ensure_unit_eligible(unit: Unit, transport_type: str) -> None:
    allowed_types = TRANSPORT_TYPE_UNIT_MAP.get(transport_type, {"BLS", "ALS", "CCT"})
    if unit.unit_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unit type {unit.unit_type} cannot serve transport type {transport_type}",
        )


def _ensure_unit_not_busy(
    db: Session,
    user: User,
    unit_id: int,
    training_mode: bool,
    exclude_incident: int | None = None,
) -> None:
    query = scoped_query(db, CADIncident, user.org_id, training_mode).filter(
        CADIncident.assigned_unit_id == unit_id,
        CADIncident.status.in_(list(ACTIVE_INCIDENT_STATUSES)),
    )
    if exclude_incident is not None:
        query = query.filter(CADIncident.id != exclude_incident)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unit is already assigned to another active incident",
        )


def _serialize_geometry(points: list[GeoPoint] | None) -> list[dict[str, float]]:
    return [{"latitude": point.latitude, "longitude": point.longitude} for point in points] if points else []


def _compose_crewlink_payload(incident: CADIncident, unit: Unit | None) -> dict[str, Any]:
    return {
        "incident_id": incident.id,
        "transport_type": incident.transport_type,
        "priority": incident.priority,
        "requesting_facility": incident.requesting_facility,
        "receiving_facility": incident.receiving_facility,
        "assigned_unit": unit.unit_identifier if unit else None,
        "eta_minutes": incident.eta_minutes,
    }


def _incident_to_dashboard(incident: CADIncident, db: Session) -> dict:
    """Shape for dashboard/list: id, incident_number, incident_type, priority, status, address, created_at, assigned_units."""
    unit_ids = [incident.assigned_unit_id] if incident.assigned_unit_id else []
    units = db.query(Unit).filter(Unit.id.in_(unit_ids)).all() if unit_ids else []
    return {
        "id": incident.id,
        "incident_number": f"T{incident.id:06d}",
        "incident_type": incident.transport_type,
        "priority": incident.priority,
        "status": incident.status,
        "address": incident.requesting_facility or "",
        "created_at": incident.created_at.isoformat() if incident.created_at else "",
        "assigned_units": [u.unit_identifier for u in units],
    }


@router.get("/active")
def list_active_incidents(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    """Active incidents only (excludes completed/cancelled). For dashboard."""
    incidents = (
        scoped_query(db, CADIncident, user.org_id, request.state.training_mode)
        .filter(CADIncident.status.in_(list(ACTIVE_INCIDENT_STATUSES)))
        .order_by(CADIncident.created_at.desc())
        .all()
    )
    return [_incident_to_dashboard(inc, db) for inc in incidents]


@router.get("")
def list_incidents(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    """List incidents with optional pagination and filters. Returns { incidents, total_pages }."""
    query = scoped_query(db, CADIncident, user.org_id, request.state.training_mode)
    if status_filter and status_filter != "all":
        query = query.filter(CADIncident.status == status_filter)
    if priority_filter and priority_filter != "all":
        query = query.filter(CADIncident.priority == priority_filter)
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    incidents = query.order_by(CADIncident.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "incidents": [_incident_to_dashboard(inc, db) for inc in incidents],
        "total_pages": total_pages,
    }


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    if payload.transport_link_trip_id:
        _ensure_single_active_incident(
            db, user, payload.transport_link_trip_id, request.state.training_mode
        )
    incident = CADIncident(
        org_id=user.org_id,
        requesting_facility=payload.requesting_facility,
        receiving_facility=payload.receiving_facility,
        transport_type=payload.transport_type,
        priority=payload.priority,
        scheduled_time=payload.scheduled_time,
        transport_link_trip_id=payload.transport_link_trip_id,
        distance_meters=payload.distance_meters,
        eta_minutes=payload.eta_minutes
        or (_estimate_eta(payload.distance_meters) if payload.distance_meters else None),
        route_geometry=_serialize_geometry(payload.route_geometry),
        notes=payload.notes or "",
    )
    apply_training_mode(incident, request)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    _record_timeline(db, incident, incident.status, user.id, notes="Incident created")
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="cad_incident",
        classification=incident.classification,
        after_state=model_snapshot(incident),
        event_type="cad.incident.created",
        event_payload={"incident_id": incident.id},
    )
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        CADIncident,
        incident_id,
        user,
        resource_label="cad_incident",
    )
    return incident


@router.patch("/{incident_id}/assign", response_model=IncidentResponse)
def assign_unit(
    incident_id: int,
    payload: IncidentAssignment,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(db, request, CADIncident, incident_id, user, resource_label="cad_incident")
    if incident.assigned_unit_id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Incident already has an assigned unit")
    unit = get_scoped_record(db, request, Unit, payload.unit_id, user, resource_label="cad_unit")
    _ensure_unit_eligible(unit, incident.transport_type)
    _ensure_unit_not_busy(db, user, unit.id, request.state.training_mode)
    before_incident = model_snapshot(incident)
    before_unit = model_snapshot(unit)
    incident.assigned_unit_id = unit.id
    incident.status = "assigned"
    incident.route_geometry = payload.route_geometry and _serialize_geometry(payload.route_geometry) or incident.route_geometry
    incident.distance_meters = payload.distance_meters or incident.distance_meters
    incident.eta_minutes = payload.eta_minutes or incident.eta_minutes or (
        _estimate_eta(payload.distance_meters) if payload.distance_meters else incident.eta_minutes
    )
    unit.status = "assigned"
    apply_training_mode(unit, request)
    apply_training_mode(incident, request)
    db.add(unit)
    db.add(incident)
    _record_timeline(db, incident, "assigned", user.id, notes="Unit assigned")
    _update_transport_trip_status(db, request, user, incident, "assigned")
    crewlink_message = create_crewlink_page(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="assignment",
        title="Unit assignment",
        message=f"{unit.unit_identifier} assigned to {incident.requesting_facility} → {incident.receiving_facility}",
        payload=_compose_crewlink_payload(incident, unit),
    )
    record_mdt_sync_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="cad.incident.unit_assigned",
        payload={"unit_id": unit.id, "incident_status": incident.status},
        unit_id=unit.id,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_incident",
        classification=incident.classification,
        before_state=before_incident,
        after_state=model_snapshot(incident),
        event_type="cad.incident.assigned",
        event_payload={"incident_id": incident.id, "assigned_unit": unit.unit_identifier},
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
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(db, request, CADIncident, incident_id, user, resource_label="cad_incident")
    before = model_snapshot(incident)
    if payload.priority and payload.priority != incident.priority:
        incident.priority = payload.priority
        create_crewlink_page(
            db=db,
            request=request,
            user=user,
            incident=incident,
            event_type="priority_change",
            title="Priority updated",
            message=f"Incident priority changed to {incident.priority}",
            payload=_compose_crewlink_payload(incident, incident.assigned_unit),
        )
    if payload.scheduled_time is not None:
        incident.scheduled_time = payload.scheduled_time
    if payload.distance_meters:
        incident.distance_meters = payload.distance_meters
    if payload.eta_minutes:
        incident.eta_minutes = payload.eta_minutes
    if payload.route_geometry:
        incident.route_geometry = _serialize_geometry(payload.route_geometry)
    if payload.status:
        if incident.transport_link_trip_id:
            _ensure_single_active_incident(
                db,
                user,
                incident.transport_link_trip_id,
                request.state.training_mode,
                exclude_id=incident.id,
            )
        incident.status = payload.status
        _record_timeline(db, incident, payload.status, user.id, notes=payload.notes or "Status update")
        _update_transport_trip_status(db, request, user, incident, payload.status)
        if payload.status == "cancelled":
            create_crewlink_page(
                db=db,
                request=request,
                user=user,
                incident=incident,
                event_type="cancelled",
                title="Incident cancelled",
                message="Incident cancelled",
                payload=_compose_crewlink_payload(incident, incident.assigned_unit),
            )
    apply_training_mode(incident, request)
    db.add(incident)
    record_mdt_sync_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="cad.incident.status_updated",
        payload={"status": incident.status, "notes": payload.notes or ""},
        unit_id=incident.assigned_unit_id,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="cad_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="cad.incident.status.updated",
        event_payload={"incident_id": incident.id, "status": incident.status},
    )
    db.commit()
    db.refresh(incident)
    return incident
