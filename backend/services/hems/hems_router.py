from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_hems_db
from core.guards import require_module
from core.security import require_roles, require_on_shift, require_trusted_device
from models.hems import (
    HemsAircraft,
    HemsAssignment,
    HemsBillingPacket,
    HemsChart,
    HemsCrew,
    HemsHandoff,
    HemsIncidentLink,
    HemsMission,
    HemsQualityReview,
    HemsRiskAssessment,
)
from models.user import User, UserRole
from utils.ai_registry import register_ai_output
from utils.legal import enforce_legal_hold
from utils.tenancy import get_scoped_record, scoped_query
from utils.time import utc_now
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.workflows import upsert_workflow_state
from models.hems import HemsMissionTimeline

router = APIRouter(
    prefix="/api/hems",
    tags=["HEMS"],
    dependencies=[Depends(require_module("HEMS"))],
)


class MissionCreate(BaseModel):
    mission_type: str = "scene"
    requesting_party: str
    pickup_location: str
    destination_location: str
    patient_global_id: str | None = None
    correlation_id: str | None = None


class MissionStatusUpdate(BaseModel):
    status: str
    notes: str = ""


class AircraftCreate(BaseModel):
    tail_number: str
    capability_flags: dict = {}
    availability: str = "Available"
    maintenance_status: str = "Green"


class CrewCreate(BaseModel):
    full_name: str
    role: str
    duty_status: str = "Ready"
    readiness_flags: dict = {}


class AssignmentCreate(BaseModel):
    crew_id: int
    aircraft_id: Optional[int] = None
    assignment_role: str = ""


class RiskCreate(BaseModel):
    weather_summary: str = ""
    risk_score: float = 0.0
    constraints: dict = {}


class ChartUpdate(BaseModel):
    vitals_trends: dict = {}
    ventilator_settings: dict = {}
    infusions: list = []
    procedures: list = []
    handoff_summary: str = ""


class HandoffCreate(BaseModel):
    receiving_clinician: str
    signature: str = ""
    notes: str = ""


class BillingCreate(BaseModel):
    transport_type: str
    miles: float
    time_minutes: int
    justification: str = ""


class LinkCreate(BaseModel):
    ground_incident_id: str = ""
    epcr_id: str = ""


class HemsQAFlag(BaseModel):
    mission_id: int
    reviewer: str = ""
    notes: str = ""
    compliance_flags: list = []


class HemsQAResolve(BaseModel):
    status: str = "closed"
    determination: str = "pass"
    notes: str = ""


@router.post("/missions", status_code=status.HTTP_201_CREATED)
def create_mission(
    payload: MissionCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(
        require_roles(UserRole.admin, UserRole.dispatcher, UserRole.hems_supervisor)
    ),
):
    mission = HemsMission(
        org_id=user.org_id,
        mission_type=payload.mission_type,
        requesting_party=payload.requesting_party,
        pickup_location=payload.pickup_location,
        destination_location=payload.destination_location,
        patient_global_id=payload.patient_global_id or "",
        correlation_id=payload.correlation_id or "",
        status="intake",
    )
    apply_training_mode(mission, request)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    timeline = HemsMissionTimeline(
        org_id=user.org_id,
        mission_id=mission.id,
        status="intake",
        notes="Mission intake created",
    )
    apply_training_mode(timeline, request)
    db.add(timeline)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_mission",
        classification=mission.classification,
        after_state=model_snapshot(mission),
        event_type="hems.mission.created",
        event_payload={
            "mission_id": mission.id,
            "correlation_id": mission.correlation_id,
        },
        schema_name="hems",
    )
    upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key="hems_mission_acceptance",
        resource_type="hems_mission",
        resource_id=str(mission.id),
        status="started",
        last_step="intake",
        metadata={"mission_type": mission.mission_type},
        classification=mission.classification,
        training_mode=request.state.training_mode,
    )
    return model_snapshot(mission)


@router.get("/missions")
def list_missions(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, HemsMission, user.org_id, request.state.training_mode).order_by(
        HemsMission.created_at.desc()
    ).all()


@router.get("/missions/{mission_id}")
def get_mission(
    mission_id: int,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles()),
):
    return get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")


@router.post("/missions/{mission_id}/status")
def update_status(
    mission_id: int,
    payload: MissionStatusUpdate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.dispatcher,
            UserRole.hems_supervisor,
            UserRole.pilot,
            UserRole.flight_nurse,
            UserRole.flight_medic,
        )
    ),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    enforce_legal_hold(db, user.org_id, "hems_mission", str(mission.id), "update")
    before = model_snapshot(mission)
    mission.status = payload.status
    timeline = HemsMissionTimeline(
        org_id=user.org_id,
        mission_id=mission.id,
        status=payload.status,
        notes=payload.notes,
    )
    apply_training_mode(timeline, request)
    db.add(timeline)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="hems_mission",
        classification=mission.classification,
        before_state=before,
        after_state=model_snapshot(mission),
        event_type="HEMS_MISSION_STATUS_CHANGED",
        event_payload={"mission_id": mission.id, "status": payload.status},
        schema_name="hems",
    )
    if payload.status in {"accepted", "complete", "cancel"}:
        upsert_workflow_state(
            db=db,
            org_id=user.org_id,
            workflow_key="hems_mission_acceptance",
            resource_type="hems_mission",
            resource_id=str(mission.id),
            status="completed" if payload.status != "cancel" else "interrupted",
            last_step=payload.status,
            interruption_reason="mission_cancelled" if payload.status == "cancel" else "",
            metadata={"mission_status": payload.status},
            classification=mission.classification,
            training_mode=request.state.training_mode,
        )
    return {"status": "ok", "mission_id": mission.id}


@router.post("/aircraft", status_code=status.HTTP_201_CREATED)
def create_aircraft(
    payload: AircraftCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.aviation_qa)),
):
    aircraft = HemsAircraft(org_id=user.org_id, **payload.dict())
    apply_training_mode(aircraft, request)
    db.add(aircraft)
    db.commit()
    db.refresh(aircraft)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_aircraft",
        classification=aircraft.classification,
        after_state=model_snapshot(aircraft),
        event_type="HEMS_AIRCRAFT_ASSIGNED",
        event_payload={"aircraft_id": aircraft.id, "tail_number": aircraft.tail_number},
        schema_name="hems",
    )
    return aircraft


@router.get("/aircraft")
def list_aircraft(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, HemsAircraft, user.org_id, request.state.training_mode).order_by(
        HemsAircraft.tail_number.asc()
    ).all()


@router.post("/crew", status_code=status.HTTP_201_CREATED)
def create_crew(
    payload: CrewCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.aviation_qa)),
):
    crew = HemsCrew(org_id=user.org_id, **payload.dict())
    apply_training_mode(crew, request)
    db.add(crew)
    db.commit()
    db.refresh(crew)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_crew",
        classification=crew.classification,
        after_state=model_snapshot(crew),
        event_type="HEMS_CREW_ASSIGNED",
        event_payload={"crew_id": crew.id, "role": crew.role},
        schema_name="hems",
    )
    return crew


@router.get("/crew")
def list_crew(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, HemsCrew, user.org_id, request.state.training_mode).order_by(
        HemsCrew.full_name.asc()
    ).all()


@router.post("/missions/{mission_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_resources(
    mission_id: int,
    payload: AssignmentCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.dispatcher)),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    assignment = HemsAssignment(
        org_id=user.org_id,
        mission_id=mission.id,
        crew_id=payload.crew_id,
        aircraft_id=payload.aircraft_id,
        assignment_role=payload.assignment_role,
    )
    apply_training_mode(assignment, request)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="assign",
        resource="hems_assignment",
        classification=assignment.classification,
        after_state=model_snapshot(assignment),
        event_type="HEMS_CREW_ASSIGNED",
        event_payload={"assignment_id": assignment.id, "mission_id": mission.id},
        schema_name="hems",
    )
    return assignment


@router.post("/missions/{mission_id}/risk", status_code=status.HTTP_201_CREATED)
def create_risk(
    mission_id: int,
    payload: RiskCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(
        require_roles(UserRole.pilot, UserRole.hems_supervisor, UserRole.aviation_qa, UserRole.admin)
    ),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    risk = HemsRiskAssessment(
        org_id=user.org_id,
        mission_id=mission.id,
        weather_summary=payload.weather_summary,
        risk_score=payload.risk_score,
        constraints=payload.constraints,
    )
    apply_training_mode(risk, request)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    ai_record = register_ai_output(
        db=db,
        org_id=user.org_id,
        model_name="quantum-ai",
        model_version="v1.0",
        prompt="hems_risk_assessment",
        output_text=f"Risk score {risk.risk_score}. {risk.weather_summary}",
        advisory_level="ADVISORY",
        classification=risk.classification,
        input_refs=[{"resource": "hems_mission", "id": mission.id}],
        config_snapshot={"module": "hems_risk"},
        training_mode=request.state.training_mode,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_risk",
        classification=risk.classification,
        after_state=model_snapshot(risk),
        event_type="HEMS_RISK_ASSESSMENT_CREATED",
        event_payload={"risk_id": risk.id, "mission_id": mission.id},
        schema_name="hems",
    )
    return {"risk": risk, "ai_registry_id": ai_record.id}


@router.post("/missions/{mission_id}/chart", status_code=status.HTTP_201_CREATED)
def upsert_chart(
    mission_id: int,
    payload: ChartUpdate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.flight_nurse, UserRole.flight_medic, UserRole.admin)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    enforce_legal_hold(db, user.org_id, "hems_chart", str(mission.id), "update")
    chart = scoped_query(db, HemsChart, user.org_id, request.state.training_mode).filter(
        HemsChart.mission_id == mission.id
    ).first()
    before = model_snapshot(chart)
    if not chart:
        chart = HemsChart(org_id=user.org_id, mission_id=mission.id)
        apply_training_mode(chart, request)
    chart.vitals_trends = payload.vitals_trends
    chart.ventilator_settings = payload.ventilator_settings
    chart.infusions = payload.infusions
    chart.procedures = payload.procedures
    chart.handoff_summary = payload.handoff_summary
    db.add(chart)
    db.commit()
    db.refresh(chart)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="hems_chart",
        classification=chart.classification,
        before_state=before,
        after_state=model_snapshot(chart),
        event_type="HEMS_CHART_UPDATED",
        event_payload={"chart_id": chart.id, "mission_id": mission.id},
        schema_name="hems",
    )
    upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key="hems_charting",
        resource_type="hems_chart",
        resource_id=str(mission.id),
        status="resumed" if chart.vitals_trends else "started",
        last_step="chart_update",
        metadata={"mission_id": mission.id},
        classification=chart.classification,
        training_mode=request.state.training_mode,
    )
    return chart


@router.post("/missions/{mission_id}/handoff", status_code=status.HTTP_201_CREATED)
def create_handoff(
    mission_id: int,
    payload: HandoffCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.flight_nurse, UserRole.flight_medic, UserRole.admin)),
    _: User = Depends(require_on_shift),
    __: User = Depends(require_trusted_device),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    enforce_legal_hold(db, user.org_id, "hems_handoff", str(mission.id), "update")
    handoff = HemsHandoff(
        org_id=user.org_id,
        mission_id=mission.id,
        receiving_clinician=payload.receiving_clinician,
        signature=payload.signature,
        notes=payload.notes,
    )
    apply_training_mode(handoff, request)
    db.add(handoff)
    db.commit()
    db.refresh(handoff)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_handoff",
        classification=handoff.classification,
        after_state=model_snapshot(handoff),
        event_type="HEMS_HANDOFF_COMPLETED",
        event_payload={"handoff_id": handoff.id, "mission_id": mission.id},
        schema_name="hems",
    )
    return handoff


@router.post("/missions/{mission_id}/billing", status_code=status.HTTP_201_CREATED)
def create_billing_packet(
    mission_id: int,
    payload: BillingCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin)),
):
    if request.state.training_mode:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TRAINING_MODE_EXPORT_BLOCKED")
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    packet = HemsBillingPacket(
        org_id=user.org_id,
        mission_id=mission.id,
        transport_type=payload.transport_type,
        miles=payload.miles,
        time_minutes=payload.time_minutes,
        justification=payload.justification,
    )
    apply_training_mode(packet, request)
    db.add(packet)
    db.commit()
    db.refresh(packet)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_billing_packet",
        classification=packet.classification,
        after_state=model_snapshot(packet),
        event_type="HEMS_BILLING_PACKET_CREATED",
        event_payload={"packet_id": packet.id, "mission_id": mission.id},
        schema_name="hems",
    )
    upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key="hems_billing_export",
        resource_type="hems_billing_packet",
        resource_id=str(packet.id),
        status="started",
        last_step="packet_created",
        metadata={"mission_id": mission.id},
        classification=packet.classification,
        training_mode=request.state.training_mode,
    )
    return packet


@router.post("/missions/{mission_id}/link", status_code=status.HTTP_201_CREATED)
def link_ground(
    mission_id: int,
    payload: LinkCreate,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.dispatcher,
            UserRole.hems_supervisor,
            UserRole.flight_nurse,
            UserRole.flight_medic,
        )
    ),
):
    mission = get_scoped_record(db, request, HemsMission, mission_id, user, resource_label="hems")
    link = HemsIncidentLink(
        org_id=user.org_id,
        mission_id=mission.id,
        ground_incident_id=payload.ground_incident_id,
        epcr_id=payload.epcr_id,
    )
    apply_training_mode(link, request)
    db.add(link)
    db.commit()
    db.refresh(link)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_incident_link",
        classification=link.classification,
        after_state=model_snapshot(link),
        event_type="hems.mission.linked",
        event_payload={"link_id": link.id, "mission_id": mission.id},
        schema_name="hems",
    )
    return link


@router.get("/dashboard")
def hems_dashboard(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles()),
):
    active = scoped_query(db, HemsMission, user.org_id, request.state.training_mode).filter(
        HemsMission.status.in_(["intake", "accepted", "lifted", "enroute"])
    )
    return {
        "active_missions": active.count(),
        "ready_aircraft": 3,
        "crew_ready": "92%",
        "weather_risk": "Moderate",
        "last_update": utc_now().isoformat(),
    }


@router.post("/simulate", status_code=status.HTTP_201_CREATED)
def simulate_mission(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(
        require_roles(UserRole.admin, UserRole.dispatcher, UserRole.hems_supervisor)
    ),
):
    if not request.state.training_mode:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TRAINING_MODE_REQUIRED")
    mission = HemsMission(
        org_id=user.org_id,
        mission_type="scene",
        requesting_party="Demo Ground EMS",
        pickup_location="Training LZ Alpha",
        destination_location="Demo Trauma Center",
        status="accepted",
        correlation_id=f"SIM-{datetime.utcnow().strftime('%H%M%S')}",
    )
    apply_training_mode(mission, request)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    for status_label in [
        "accepted",
        "lifted",
        "patient_contact",
        "depart_scene",
        "enroute_dest",
        "landed",
    ]:
        timeline = HemsMissionTimeline(
            org_id=user.org_id,
            mission_id=mission.id,
            status=status_label,
            notes="Simulated timeline event",
        )
        apply_training_mode(timeline, request)
        db.add(timeline)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="simulate",
        resource="hems_mission",
        classification=mission.classification,
        after_state=model_snapshot(mission),
        event_type="hems.mission.simulated",
        event_payload={"mission_id": mission.id, "simulated": True},
        schema_name="hems",
    )
    upsert_workflow_state(
        db=db,
        org_id=user.org_id,
        workflow_key="hems_mission_acceptance",
        resource_type="hems_mission",
        resource_id=str(mission.id),
        status="completed",
        last_step="simulated",
        metadata={"simulated": True},
        classification=mission.classification,
        training_mode=request.state.training_mode,
    )
    return mission


@router.get("/qa")
def list_hems_qa(
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.aviation_qa)),
):
    return scoped_query(
        db, HemsQualityReview, user.org_id, request.state.training_mode
    ).order_by(HemsQualityReview.created_at.desc())


@router.post("/qa", status_code=status.HTTP_201_CREATED)
def flag_hems_qa(
    payload: HemsQAFlag,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.aviation_qa)),
):
    mission = (
        scoped_query(db, HemsMission, user.org_id, request.state.training_mode)
        .filter(HemsMission.id == payload.mission_id)
        .first()
    )
    if not mission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mission not found")
    review = HemsQualityReview(org_id=user.org_id, **payload.dict())
    apply_training_mode(review, request)
    db.add(review)
    db.commit()
    db.refresh(review)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="hems_quality_review",
        classification=review.classification,
        after_state=model_snapshot(review),
        event_type="hems.qa.created",
        event_payload={"review_id": review.id, "mission_id": mission.id},
        schema_name="hems",
    )
    return review


@router.post("/qa/{review_id}/resolve")
def resolve_hems_qa(
    review_id: int,
    payload: HemsQAResolve,
    request: Request,
    db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.hems_supervisor, UserRole.aviation_qa)),
):
    review = (
        scoped_query(db, HemsQualityReview, user.org_id, request.state.training_mode)
        .filter(HemsQualityReview.id == review_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    before = model_snapshot(review)
    review.status = payload.status
    review.determination = payload.determination
    review.notes = payload.notes
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="hems_quality_review",
        classification=review.classification,
        before_state=before,
        after_state=model_snapshot(review),
        event_type="hems.qa.resolved",
        event_payload={"review_id": review.id},
        schema_name="hems",
    )
    return {"status": "ok", "review_id": review.id}
