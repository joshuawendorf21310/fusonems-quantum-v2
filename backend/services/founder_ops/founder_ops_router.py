from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles, require_mfa
from models.founder_ops import DataGovernanceRule, IncidentCommand, PricingPlan, PwaDistribution
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/founder-ops",
    tags=["Founder Ops"],
    dependencies=[Depends(require_module("FOUNDER")), Depends(require_mfa)],
)


class PwaCreate(BaseModel):
    platform: str = "web"
    current_version: str = ""
    pending_version: str = ""
    status: str = "enabled"
    rules: dict = {}


class PricingCreate(BaseModel):
    plan_name: str
    status: str = "active"
    pricing: dict = {}
    limits: dict = {}


class IncidentCreate(BaseModel):
    title: str
    status: str = "open"
    severity: str = "medium"
    summary: str = ""
    actions: list = []


class GovernanceCreate(BaseModel):
    rule_type: str = "retention"
    status: str = "active"
    settings: dict = {}


@router.get("/pwa")
def list_pwa(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    return scoped_query(db, PwaDistribution, user.org_id, request.state.training_mode).order_by(
        PwaDistribution.created_at.desc()
    )


@router.post("/pwa", status_code=status.HTTP_201_CREATED)
def create_pwa(
    payload: PwaCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    record = PwaDistribution(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="pwa_distribution",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="founder_ops.pwa.created",
        event_payload={"pwa_id": record.id},
    )
    return record


@router.get("/pricing")
def list_pricing(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    return scoped_query(db, PricingPlan, user.org_id, request.state.training_mode).order_by(
        PricingPlan.created_at.desc()
    )


@router.post("/pricing", status_code=status.HTTP_201_CREATED)
def create_pricing(
    payload: PricingCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    record = PricingPlan(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="pricing_plan",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="founder_ops.pricing.created",
        event_payload={"pricing_id": record.id},
    )
    return record


@router.get("/incidents")
def list_incidents(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    return scoped_query(db, IncidentCommand, user.org_id, request.state.training_mode).order_by(
        IncidentCommand.created_at.desc()
    )


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    record = IncidentCommand(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="incident_command",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="founder_ops.incident.created",
        event_payload={"incident_id": record.id},
    )
    return record


@router.get("/governance")
def list_governance(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    return scoped_query(db, DataGovernanceRule, user.org_id, request.state.training_mode).order_by(
        DataGovernanceRule.created_at.desc()
    )


@router.post("/governance", status_code=status.HTTP_201_CREATED)
def create_governance(
    payload: GovernanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder)),
):
    record = DataGovernanceRule(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="data_governance_rule",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="founder_ops.governance.created",
        event_payload={"rule_id": record.id},
    )
    return record
