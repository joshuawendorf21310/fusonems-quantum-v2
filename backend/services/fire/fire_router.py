from datetime import datetime, timezone
import json
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_fire_db
from core.guards import require_module
from core.security import require_roles
from models.fire import (
    FireApparatus,
    FireApparatusInventory,
    FireAuditLog,
    FireExportRecord,
    FireIncident,
    FireIncidentApparatus,
    FireIncidentPersonnel,
    FirePreventionRecord,
    FireTrainingRecord,
    FireIncidentTimeline,
    FireInventoryHook,
)
from models.fire_rms import FirePersonnel
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.ai_registry import register_ai_output
from utils.legal import enforce_legal_hold
from utils.time import utc_now
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/fire",
    tags=["Fire-EMS"],
    dependencies=[Depends(require_module("FIRE"))],
)


class IncidentCreate(BaseModel):
    incident_type: str
    location: str
    incident_category: str = "Structure"
    incident_subtype: str = ""
    incident_number: str | None = None
    incident_type_category: str = ""
    local_descriptor: str = ""
    alarm_datetime: datetime | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None
    priority: str = "Routine"
    hybrid_ems: bool = False
    ems_incident_id: str = ""
    loss_estimate: float = 0.0
    property_use: str = ""
    situation_found: str = ""
    narrative: str = ""
    actions_taken: str = ""
    exposures: list[str] = Field(default_factory=list)
    responding_units: list[str] = Field(default_factory=list)
    civilian_casualties: int = 0
    civilian_casualty_details: str = ""
    firefighter_casualties: int = 0
    firefighter_casualty_details: str = ""


class IncidentUpdate(BaseModel):
    location: str | None = None
    incident_type: str | None = None
    incident_number: str | None = None
    incident_category: str | None = None
    incident_subtype: str | None = None
    incident_type_category: str | None = None
    local_descriptor: str | None = None
    alarm_datetime: datetime | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None
    priority: str | None = None
    loss_estimate: float | None = None
    property_use: str | None = None
    situation_found: str | None = None
    narrative: str | None = None
    actions_taken: str | None = None
    exposures: list[str] | None = None
    responding_units: list[str] | None = None
    civilian_casualties: int | None = None
    civilian_casualty_details: str | None = None
    firefighter_casualties: int | None = None
    firefighter_casualty_details: str | None = None
    status: str | None = None


class IncidentTimelineUpdate(BaseModel):
    notified_at: Optional[datetime] = None
    enroute_at: Optional[datetime] = None
    on_scene_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None


class IncidentStatusUpdate(BaseModel):
    status: Optional[str] = None
    nfirs_status: Optional[str] = None
    neris_status: Optional[str] = None
    ai_summary: Optional[str] = None


class IncidentApproval(BaseModel):
    approved_by: str
    approved_at: Optional[datetime] = None


class IncidentLinkEms(BaseModel):
    ems_incident_id: str


class InventoryHookCreate(BaseModel):
    equipment_type: str
    quantity: int = 1
    usage_summary: str = ""
    notes: str = ""
    payload: dict = Field(default_factory=dict)


class ApparatusCreate(BaseModel):
    apparatus_id: str
    apparatus_type: str
    status: str = "In Service"
    mileage: int = 0
    readiness_score: int = 100


class PersonnelCreate(BaseModel):
    full_name: str
    role: str
    certifications: str = ""


class IncidentAssignApparatus(BaseModel):
    apparatus_id: int
    role: str = "Primary"
    status: str = "Assigned"
    notes: str = ""


class IncidentAssignPersonnel(BaseModel):
    personnel_id: int
    role: str = "Responder"
    status: str = "Assigned"
    notes: str = ""


class TrainingCreate(BaseModel):
    training_type: str
    crew: str
    status: str = "Planned"
    notes: str = ""


class PreventionCreate(BaseModel):
    occupancy_name: str
    inspection_status: str = "Scheduled"
    hydrant_map: str = ""
    notes: str = ""


class ApparatusInventoryCreate(BaseModel):
    apparatus_id: int
    item_name: str
    status: str = "Ready"
    quantity: int = 1
    notes: str = ""


class FireExportRequest(BaseModel):
    incident_id: str


def log_audit(
    db: Session,
    incident_id: str,
    action: str,
    actor: str = "system",
    actor_org_id: int | None = None,
) -> None:
    if actor_org_id is None:
        return
    db.add(
        FireAuditLog(
            incident_id=incident_id,
            action=action,
            actor=actor,
            org_id=actor_org_id,
        )
    )


def record_timeline_event(
    db: Session,
    request: Request,
    user: User,
    incident: FireIncident,
    event_type: str,
    notes: str = "",
    event_data: dict | None = None,
) -> FireIncidentTimeline:
    entry = FireIncidentTimeline(
        org_id=user.org_id,
        incident_id=incident.id,
        incident_identifier=incident.incident_id,
        event_type=event_type,
        notes=notes,
        event_data=event_data or {},
    )
    apply_training_mode(entry, request)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="timeline",
        resource="fire_incident_timeline",
        classification=entry.classification,
        after_state=model_snapshot(entry),
        event_type=f"fire.incident.timeline.{event_type}",
        event_payload={
            "incident_id": incident.incident_id,
            "event_id": entry.id,
            "notes": notes,
        },
    )
    return entry


def ensure_incident_editable(incident: FireIncident, incoming_status: str | None = None) -> None:
    if incident.status in {"Closed", "Exported"}:
        if incoming_status == incident.status or incoming_status == "Open":
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident is closed. Reopen to make updates.",
        )


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident_number = payload.incident_number or f"FIR-{uuid4().hex[:6].upper()}"
    incident = FireIncident(
        org_id=user.org_id,
        incident_id=f"FIR-{uuid4().hex[:8].upper()}",
        incident_number=incident_number,
        incident_type=payload.incident_type,
        incident_category=payload.incident_category,
        incident_subtype=payload.incident_subtype,
        neris_category=payload.incident_type_category,
        local_descriptor=payload.local_descriptor,
        location=payload.location,
        location_latitude=payload.location_latitude,
        location_longitude=payload.location_longitude,
        alarm_datetime=payload.alarm_datetime or utc_now(),
        priority=payload.priority,
        hybrid_ems=payload.hybrid_ems,
        ems_incident_id=payload.ems_incident_id,
        loss_estimate=payload.loss_estimate,
        property_use=payload.property_use,
        situation_found=payload.situation_found,
        narrative=payload.narrative,
        actions_taken=payload.actions_taken,
        exposures=payload.exposures,
        responding_units=payload.responding_units,
        civilian_casualties=payload.civilian_casualties,
        civilian_casualty_details=payload.civilian_casualty_details,
        firefighter_casualties=payload.firefighter_casualties,
        firefighter_casualty_details=payload.firefighter_casualty_details,
    )
    apply_training_mode(incident, request)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    log_audit(db, incident.incident_id, "Created incident", actor_org_id=user.org_id)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_incident",
        classification=incident.classification,
        after_state=model_snapshot(incident),
        event_type="fire.incident.created",
        event_payload={"incident_id": incident.incident_id},
    )
    db.commit()
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="created",
        notes="Incident created",
    )
    return model_snapshot(incident)


@router.get("/incidents")
def list_incidents(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, FireIncident, user.org_id, request.state.training_mode).order_by(
        FireIncident.created_at.desc()
    ).all()


@router.get("/incidents/{incident_id}")
def get_incident(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )


@router.get("/incidents/{incident_id}/timeline")
def incident_timeline(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    return (
        scoped_query(db, FireIncidentTimeline, user.org_id, request.state.training_mode)
        .filter(FireIncidentTimeline.incident_id == incident.id)
        .order_by(FireIncidentTimeline.recorded_at.asc())
        .all()
    )


@router.patch("/incidents/{incident_id}/timeline")
def update_timeline(
    incident_id: str,
    payload: IncidentTimelineUpdate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "update")
    ensure_incident_editable(incident)
    before = model_snapshot(incident)
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(incident, field, value)
    incident.updated_at = utc_now()
    log_audit(db, incident_id, "Updated timeline", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.timeline_updated",
        event_payload={"incident_id": incident.incident_id},
    )
    if changes:
        if "on_scene_at" in changes:
            record_timeline_event(
                db=db,
                request=request,
                user=user,
                incident=incident,
                event_type="unit_arrived",
                notes="Unit arrived on scene",
                event_data={"timestamp": incident.on_scene_at.isoformat() if incident.on_scene_at else ""},
            )
        record_timeline_event(
            db=db,
            request=request,
            user=user,
            incident=incident,
            event_type="updated",
            notes="Timeline updated",
            event_data={"fields": list(changes.keys())},
        )
    return incident


@router.patch("/incidents/{incident_id}/status")
def update_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "update")
    ensure_incident_editable(incident, payload.status)
    before = model_snapshot(incident)
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(incident, field, value)
    incident.updated_at = utc_now()
    log_audit(db, incident_id, "Updated status", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.status_updated",
        event_payload={"incident_id": incident.incident_id},
    )
    if payload.status:
        record_timeline_event(
            db=db,
            request=request,
            user=user,
            incident=incident,
            event_type="updated_status",
            notes=f"Status updated to {payload.status}",
            event_data={"status": payload.status},
        )
    return incident


@router.patch("/incidents/{incident_id}")
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "update")
    ensure_incident_editable(incident, payload.status)
    before = model_snapshot(incident)
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(incident, field, value)
    incident.updated_at = utc_now()
    log_audit(db, incident_id, "Updated incident", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.updated",
        event_payload={"incident_id": incident.incident_id},
    )
    if changes:
        record_timeline_event(
            db=db,
            request=request,
            user=user,
            incident=incident,
            event_type="updated",
            notes="Incident data updated",
            event_data={"fields": list(changes.keys())},
        )
    return incident


@router.post("/incidents/{incident_id}/close")
def close_incident(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "close")
    ensure_incident_editable(incident, incoming_status="Closed")
    before = model_snapshot(incident)
    incident.status = "Closed"
    incident.closed_at = utc_now()
    incident.updated_at = utc_now()
    log_audit(db, incident.incident_id, "Closed incident", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="close",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.closed",
        event_payload={"incident_id": incident.incident_id},
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="closed",
        notes="Incident closed",
    )
    return {"status": "closed", "incident_id": incident.incident_id}


def _persist_fire_export(
    db: Session,
    request: Request,
    user: User,
    incident: FireIncident,
    export_type: str,
    payload: dict,
    event_type: str,
) -> FireExportRecord:
    record = FireExportRecord(
        org_id=user.org_id,
        export_type=export_type,
        incident_id=incident.incident_id,
        payload=json.dumps(payload),
    )
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_export",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type=event_type,
        event_payload={
            "export_id": record.id,
            "export_type": export_type,
            "incident_id": incident.incident_id,
        },
    )
    return record


def _emit_export_generated_event(
    db: Session,
    request: Request,
    user: User,
    incident: FireIncident,
    export_type: str,
    payload: dict,
    record: FireExportRecord,
) -> None:
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="export",
        resource="fire_export",
        classification=incident.classification,
        after_state={
            "incident_id": incident.incident_id,
            "export_id": record.id,
            "export_type": export_type,
        },
        event_type="fire.export.generated",
        event_payload={
            "incident_id": incident.incident_id,
            "export_id": record.id,
            "export_type": export_type,
            "format": payload.get("format"),
        },
    )


def _build_neris_export_payload(
    request: Request, db: Session, incident: FireIncident
) -> dict:
    training_mode = request.state.training_mode
    apparatus_assignments = (
        scoped_query(db, FireIncidentApparatus, incident.org_id, training_mode)
        .filter(FireIncidentApparatus.incident_id == incident.id)
        .all()
    )
    personnel_assignments = (
        scoped_query(db, FireIncidentPersonnel, incident.org_id, training_mode)
        .filter(FireIncidentPersonnel.incident_id == incident.id)
        .all()
    )
    apparatus_ids = {assignment.apparatus_id for assignment in apparatus_assignments}
    personnel_ids = {assignment.personnel_id for assignment in personnel_assignments}
    apparatus_map = {}
    personnel_map = {}
    if apparatus_ids:
        apparatus_map = {
            apparatus.id: apparatus
            for apparatus in (
                scoped_query(db, FireApparatus, incident.org_id, training_mode)
                .filter(FireApparatus.id.in_(list(apparatus_ids)))
                .all()
            )
        }
    if personnel_ids:
        personnel_map = {
            person.id: person
            for person in (
                scoped_query(db, FirePersonnel, incident.org_id, training_mode)
                .filter(FirePersonnel.id.in_(list(personnel_ids)))
                .all()
            )
        }

    apparatus_payload = [
        {
            "assignment_id": assignment.id,
            "apparatus_record_id": assignment.apparatus_id,
            "apparatus_identifier": apparatus_map.get(assignment.apparatus_id).apparatus_id
            if apparatus_map.get(assignment.apparatus_id)
            else None,
            "role": assignment.role,
            "status": assignment.status,
            "notes": assignment.notes,
        }
        for assignment in apparatus_assignments
    ]
    personnel_payload = [
        {
            "assignment_id": assignment.id,
            "personnel_id": assignment.personnel_id,
            "full_name": personnel_map.get(assignment.personnel_id).full_name
            if personnel_map.get(assignment.personnel_id)
            else None,
            "role": assignment.role,
            "status": assignment.status,
            "notes": assignment.notes,
        }
        for assignment in personnel_assignments
    ]

    return {
        "format": "NERIS",
        "incident_id": incident.incident_id,
        "incident_number": incident.incident_number,
        "neris_category": incident.neris_category,
        "local_descriptor": incident.local_descriptor,
        "incident_type": incident.incident_type,
        "location": {
            "address": incident.location,
            "latitude": incident.location_latitude,
            "longitude": incident.location_longitude,
        },
        "alarm_datetime": incident.alarm_datetime.isoformat()
        if incident.alarm_datetime
        else None,
        "priority": incident.priority,
        "status": incident.status,
        "responding_units": incident.responding_units or [],
        "actions_taken": incident.actions_taken,
        "exposures": incident.exposures,
        "casualties": {
            "civilian": {
                "count": incident.civilian_casualties,
                "details": incident.civilian_casualty_details,
            },
            "firefighter": {
                "count": incident.firefighter_casualties,
                "details": incident.firefighter_casualty_details,
            },
        },
        "assignments": {
            "apparatus": apparatus_payload,
            "personnel": personnel_payload,
        },
        "narrative": incident.narrative,
        "neris_status": incident.neris_status,
        "nfirs_status": incident.nfirs_status,
    }


@router.post("/incidents/{incident_id}/export")
def export_incident(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    payload = _build_neris_export_payload(request, db, incident)
    record = _persist_fire_export(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NERIS",
        payload=payload,
        event_type="fire.export.neris_created",
    )
    _emit_export_generated_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NERIS",
        payload=payload,
        record=record,
    )
    incident.status = "Exported"
    incident.updated_at = utc_now()
    log_audit(db, incident.incident_id, "Exported incident", actor_org_id=user.org_id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="exported",
        notes="Structured export generated",
        event_data={"export_id": record.id},
    )
    return {"status": "exported", "export": payload, "export_id": record.id}


@router.post("/incidents/{incident_id}/inventory_hooks", status_code=status.HTTP_201_CREATED)
def create_inventory_hook(
    incident_id: str,
    payload: InventoryHookCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "inventory")
    ensure_incident_editable(incident)
    hook = FireInventoryHook(
        org_id=user.org_id,
        incident_id=incident.id,
        incident_identifier=incident.incident_id,
        equipment_type=payload.equipment_type,
        quantity=payload.quantity,
        usage_summary=payload.usage_summary,
        notes=payload.notes,
        reported_by=user.email,
        payload=payload.payload,
    )
    apply_training_mode(hook, request)
    db.add(hook)
    db.commit()
    db.refresh(hook)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_inventory_hook",
        classification=hook.classification,
        after_state=model_snapshot(hook),
        event_type="inventory.fire.hook_recorded",
        event_payload={
            "incident_id": incident.incident_id,
            "equipment": hook.equipment_type,
            "quantity": hook.quantity,
        },
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="inventory_recorded",
        notes="Equipment usage recorded",
        event_data={"equipment": hook.equipment_type, "quantity": hook.quantity},
    )
    return model_snapshot(hook)


@router.post("/incidents/{incident_id}/approval")
def approve_incident(
    incident_id: str,
    payload: IncidentApproval,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "update")
    before = model_snapshot(incident)
    incident.approved_by = payload.approved_by
    incident.approved_at = payload.approved_at or datetime.now(timezone.utc)
    log_audit(db, incident_id, f"Approved by {payload.approved_by}", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="approve",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.approved",
        event_payload={"incident_id": incident.incident_id},
    )
    return incident


@router.post("/incidents/{incident_id}/link-epcr")
def link_epcr(
    incident_id: str,
    payload: IncidentLinkEms,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    enforce_legal_hold(db, user.org_id, "fire_incident", incident.incident_id, "update")
    before = model_snapshot(incident)
    incident.hybrid_ems = True
    incident.ems_incident_id = payload.ems_incident_id
    log_audit(db, incident_id, f"Linked ePCR {payload.ems_incident_id}", actor_org_id=user.org_id)
    db.commit()
    db.refresh(incident)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="link_epcr",
        resource="fire_incident",
        classification=incident.classification,
        before_state=before,
        after_state=model_snapshot(incident),
        event_type="fire.incident.epcr_linked",
        event_payload={"incident_id": incident.incident_id, "epcr": payload.ems_incident_id},
    )
    return incident


@router.post("/apparatus", status_code=status.HTTP_201_CREATED)
def create_apparatus(
    payload: ApparatusCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    apparatus = FireApparatus(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(apparatus, request)
    db.add(apparatus)
    db.commit()
    db.refresh(apparatus)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_apparatus",
        classification=apparatus.classification,
        after_state=model_snapshot(apparatus),
        event_type="fire.apparatus.created",
        event_payload={"apparatus_id": apparatus.id},
    )
    return model_snapshot(apparatus)


@router.get("/apparatus")
def list_apparatus(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, FireApparatus, user.org_id, request.state.training_mode).order_by(
        FireApparatus.apparatus_id.asc()
    ).all()


@router.post("/apparatus/inventory", status_code=status.HTTP_201_CREATED)
def create_apparatus_inventory(
    payload: ApparatusInventoryCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    apparatus = (
        scoped_query(db, FireApparatus, user.org_id, request.state.training_mode)
        .filter(FireApparatus.id == payload.apparatus_id)
        .first()
    )
    if not apparatus:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apparatus not found")
    record = FireApparatusInventory(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_apparatus_inventory",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="fire.apparatus_inventory.created",
        event_payload={"inventory_id": record.id, "apparatus_id": apparatus.id},
    )
    return model_snapshot(record)


@router.get("/apparatus/{apparatus_id}/inventory")
def list_apparatus_inventory(
    apparatus_id: int,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return (
        scoped_query(db, FireApparatusInventory, user.org_id, request.state.training_mode)
        .filter(FireApparatusInventory.apparatus_id == apparatus_id)
        .all()
    )


@router.post("/personnel", status_code=status.HTTP_201_CREATED)
def create_personnel(
    payload: PersonnelCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = FirePersonnel(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_personnel",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="fire.personnel.created",
        event_payload={"personnel_id": record.id},
    )
    return model_snapshot(record)


@router.get("/personnel")
def list_personnel(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, FirePersonnel, user.org_id, request.state.training_mode).order_by(
        FirePersonnel.full_name.asc()
    ).all()


@router.post("/incidents/{incident_id}/assign-apparatus", status_code=status.HTTP_201_CREATED)
def assign_apparatus(
    incident_id: str,
    payload: IncidentAssignApparatus,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    apparatus = (
        scoped_query(db, FireApparatus, user.org_id, request.state.training_mode)
        .filter(FireApparatus.id == payload.apparatus_id)
        .first()
    )
    if not apparatus:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apparatus not found")
    assignment = FireIncidentApparatus(
        incident_id=incident.id,
        apparatus_id=payload.apparatus_id,
        role=payload.role,
        status=payload.status,
        notes=payload.notes,
        org_id=user.org_id,
    )
    db.add(assignment)
    log_audit(db, incident_id, "Assigned apparatus", actor_org_id=user.org_id)
    db.commit()
    db.refresh(assignment)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="assign",
        resource="fire_incident_apparatus",
        classification=assignment.classification,
        after_state=model_snapshot(assignment),
        event_type="fire.incident.apparatus_assigned",
        event_payload={
            "assignment_id": assignment.id,
            "incident_id": incident.incident_id,
            "apparatus_id": apparatus.id,
        },
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_assigned",
        notes="Apparatus assigned",
        event_data={"apparatus_id": apparatus.id, "role": payload.role},
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_added",
        notes="Apparatus added to incident",
        event_data={
            "assignment_id": assignment.id,
            "apparatus_id": apparatus.id,
            "role": payload.role,
        },
    )
    return assignment


@router.post("/incidents/{incident_id}/assign-personnel", status_code=status.HTTP_201_CREATED)
def assign_personnel(
    incident_id: str,
    payload: IncidentAssignPersonnel,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    personnel = (
        scoped_query(db, FirePersonnel, user.org_id, request.state.training_mode)
        .filter(FirePersonnel.id == payload.personnel_id)
        .first()
    )
    if not personnel:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Personnel not found")
    assignment = FireIncidentPersonnel(
        incident_id=incident.id,
        personnel_id=payload.personnel_id,
        role=payload.role,
        status=payload.status,
        notes=payload.notes,
        org_id=user.org_id,
    )
    db.add(assignment)
    log_audit(db, incident_id, "Assigned personnel", actor_org_id=user.org_id)
    db.commit()
    db.refresh(assignment)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="assign",
        resource="fire_incident_personnel",
        classification=assignment.classification,
        after_state=model_snapshot(assignment),
        event_type="fire.incident.personnel_assigned",
        event_payload={
            "assignment_id": assignment.id,
            "incident_id": incident.incident_id,
            "personnel_id": personnel.id,
        },
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_assigned",
        notes="Personnel assigned",
        event_data={"personnel_id": personnel.id, "role": payload.role},
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_added",
        notes="Personnel added to incident",
        event_data={
            "assignment_id": assignment.id,
            "personnel_id": personnel.id,
            "role": payload.role,
        },
    )
    return assignment


@router.delete("/incidents/{incident_id}/assign-apparatus/{assignment_id}")
def remove_apparatus_assignment(
    incident_id: str,
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    ensure_incident_editable(incident)
    assignment = (
        scoped_query(db, FireIncidentApparatus, user.org_id, request.state.training_mode)
        .filter(FireIncidentApparatus.id == assignment_id)
        .first()
    )
    if not assignment or assignment.incident_id != incident.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    before = model_snapshot(assignment)
    db.delete(assignment)
    log_audit(db, incident.incident_id, "Removed apparatus", actor_org_id=user.org_id)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="delete",
        resource="fire_incident_apparatus",
        classification=incident.classification,
        before_state=before,
        after_state={},
        event_type="fire.incident.apparatus_removed",
        event_payload={
            "incident_id": incident.incident_id,
            "assignment_id": assignment_id,
            "apparatus_id": assignment.apparatus_id,
        },
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_removed",
        notes="Apparatus removed from incident",
        event_data={
            "assignment_id": assignment_id,
            "apparatus_id": assignment.apparatus_id,
        },
    )
    return {"status": "removed", "assignment_id": assignment_id}


@router.delete("/incidents/{incident_id}/assign-personnel/{assignment_id}")
def remove_personnel_assignment(
    incident_id: str,
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    ensure_incident_editable(incident)
    assignment = (
        scoped_query(db, FireIncidentPersonnel, user.org_id, request.state.training_mode)
        .filter(FireIncidentPersonnel.id == assignment_id)
        .first()
    )
    if not assignment or assignment.incident_id != incident.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    before = model_snapshot(assignment)
    db.delete(assignment)
    log_audit(db, incident.incident_id, "Removed personnel", actor_org_id=user.org_id)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="delete",
        resource="fire_incident_personnel",
        classification=incident.classification,
        before_state=before,
        after_state={},
        event_type="fire.incident.personnel_removed",
        event_payload={
            "incident_id": incident.incident_id,
            "assignment_id": assignment_id,
            "personnel_id": assignment.personnel_id,
        },
    )
    record_timeline_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        event_type="unit_removed",
        notes="Personnel removed from incident",
        event_data={
            "assignment_id": assignment_id,
            "personnel_id": assignment.personnel_id,
        },
    )
    return {"status": "removed", "assignment_id": assignment_id}


@router.get("/incidents/{incident_id}/assignments")
def list_assignments(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    apparatus = (
        scoped_query(db, FireIncidentApparatus, user.org_id, request.state.training_mode)
        .filter(FireIncidentApparatus.incident_id == incident.id)
        .all()
    )
    personnel = (
        scoped_query(db, FireIncidentPersonnel, user.org_id, request.state.training_mode)
        .filter(FireIncidentPersonnel.incident_id == incident.id)
        .all()
    )
    return {"apparatus": apparatus, "personnel": personnel}


@router.post("/training", status_code=status.HTTP_201_CREATED)
def create_training(
    payload: TrainingCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = FireTrainingRecord(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_training",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="fire.training.created",
        event_payload={"training_id": record.id},
    )
    return record


@router.get("/training")
def list_training(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(
        db, FireTrainingRecord, user.org_id, request.state.training_mode
    ).order_by(FireTrainingRecord.created_at.desc()).all()


@router.post("/prevention", status_code=status.HTTP_201_CREATED)
def create_prevention(
    payload: PreventionCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = FirePreventionRecord(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fire_prevention",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="fire.prevention.created",
        event_payload={"prevention_id": record.id},
    )
    return record


@router.get("/prevention")
def list_prevention(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(
        db, FirePreventionRecord, user.org_id, request.state.training_mode
    ).order_by(FirePreventionRecord.created_at.desc()).all()


@router.get("/dashboard")
def fire_dashboard(user: User = Depends(require_roles())):
    return {
        "active_incidents": 4,
        "apparatus_ready": "92%",
        "training_gap": "2 crews",
        "risk_indicator": "Moderate",
    }


@router.get("/incidents/{incident_id}/ai-review")
def ai_review(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles()),
):
    incident = get_scoped_record(
        db,
        request,
        FireIncident,
        incident_id,
        user,
        id_field="incident_id",
        resource_label="fire-incident",
    )
    missing = []
    if not incident.narrative:
        missing.append("Narrative")
    if not incident.property_use:
        missing.append("Property Use")
    if not incident.situation_found:
        missing.append("Situation Found")
    suggestion = "All required fields complete." if not missing else f"Missing: {', '.join(missing)}"
    ai_record = register_ai_output(
        db=db,
        org_id=user.org_id,
        model_name="quantum-ai",
        model_version="v1.0",
        prompt="fire_incident_review",
        output_text=suggestion,
        advisory_level="ADVISORY",
        classification=incident.classification,
        input_refs=[{"resource": "fire_incident", "id": incident.incident_id}],
        config_snapshot={"module": "fire"},
        training_mode=request.state.training_mode,
    )
    return {
        "incident_id": incident_id,
        "missing_fields": missing,
        "suggested_actions": [
            "Confirm loss estimate and property use.",
            "Review hybrid EMS linkage for NEMSIS export.",
        ],
        "summary": suggestion,
        "ai_registry_id": ai_record.id,
        "advisory_level": ai_record.advisory_level,
        "model_version": ai_record.model_version,
    }


@router.post("/exports/nfirs", status_code=status.HTTP_201_CREATED)
def export_nfirs(
    payload: FireExportRequest,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = (
        scoped_query(db, FireIncident, user.org_id, request.state.training_mode)
        .filter(FireIncident.incident_id == payload.incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incident not found")
    export_payload = {
        "format": "NFIRS",
        "incident_id": payload.incident_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    record = _persist_fire_export(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NFIRS",
        payload=export_payload,
        event_type="fire.export.nfirs_created",
    )
    _emit_export_generated_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NFIRS",
        payload=export_payload,
        record=record,
    )
    return {"status": "ok", "export": export_payload}


@router.post("/exports/neris", status_code=status.HTTP_201_CREATED)
def export_neris(
    payload: FireExportRequest,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = (
        scoped_query(db, FireIncident, user.org_id, request.state.training_mode)
        .filter(FireIncident.incident_id == payload.incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incident not found")
    export_payload = {
        "format": "NERIS",
        "incident_id": payload.incident_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    record = _persist_fire_export(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NERIS",
        payload=export_payload,
        event_type="fire.export.neris_created",
    )
    _emit_export_generated_event(
        db=db,
        request=request,
        user=user,
        incident=incident,
        export_type="NERIS",
        payload=export_payload,
        record=record,
    )
    return {"status": "ok", "export": export_payload}


@router.get("/exports/history")
def list_exports(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return (
        scoped_query(db, FireExportRecord, user.org_id, request.state.training_mode)
        .order_by(FireExportRecord.created_at.desc())
        .all()
    )
