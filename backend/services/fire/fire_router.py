from datetime import datetime
import json
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
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
    FirePersonnel,
    FirePreventionRecord,
    FireTrainingRecord,
)
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.ai_registry import register_ai_output
from utils.legal import enforce_legal_hold
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
    priority: str = "Routine"
    hybrid_ems: bool = False
    ems_incident_id: str = ""
    loss_estimate: float = 0.0
    property_use: str = ""
    situation_found: str = ""
    narrative: str = ""


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


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    incident = FireIncident(
        org_id=user.org_id,
        incident_id=f"FIR-{uuid4().hex[:8].upper()}",
        incident_type=payload.incident_type,
        incident_category=payload.incident_category,
        incident_subtype=payload.incident_subtype,
        location=payload.location,
        priority=payload.priority,
        hybrid_ems=payload.hybrid_ems,
        ems_incident_id=payload.ems_incident_id,
        loss_estimate=payload.loss_estimate,
        property_use=payload.property_use,
        situation_found=payload.situation_found,
        narrative=payload.narrative,
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
    before = model_snapshot(incident)
    for field, value in payload.dict(exclude_none=True).items():
        setattr(incident, field, value)
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
    before = model_snapshot(incident)
    for field, value in payload.dict(exclude_none=True).items():
        setattr(incident, field, value)
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
    return incident


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
    incident.approved_at = payload.approved_at or datetime.utcnow()
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
    apparatus = FireApparatus(**payload.dict(), org_id=user.org_id)
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
    record = FireApparatusInventory(**payload.dict(), org_id=user.org_id)
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
    record = FirePersonnel(**payload.dict(), org_id=user.org_id)
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
    return assignment


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
    record = FireTrainingRecord(**payload.dict(), org_id=user.org_id)
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
    record = FirePreventionRecord(**payload.dict(), org_id=user.org_id)
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
        "generated_at": datetime.utcnow().isoformat(),
    }
    record = FireExportRecord(
        org_id=user.org_id,
        export_type="NFIRS",
        incident_id=payload.incident_id,
        payload=json.dumps(export_payload),
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
        event_type="fire.export.nfirs_created",
        event_payload={"export_id": record.id, "export_type": "NFIRS", "incident_id": incident.incident_id},
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
        "generated_at": datetime.utcnow().isoformat(),
    }
    record = FireExportRecord(
        org_id=user.org_id,
        export_type="NERIS",
        incident_id=payload.incident_id,
        payload=json.dumps(export_payload),
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
        event_type="fire.export.neris_created",
        event_payload={"export_id": record.id, "export_type": "NERIS", "incident_id": incident.incident_id},
    )
    return {"status": "ok", "export": export_payload}


@router.get("/exports/history")
def list_exports(
    request: Request,
    db: Session = Depends(get_fire_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(
        db, FireExportRecord, user.org_id, request.state.training_mode
    ).order_by(FireExportRecord.created_at.desc())
