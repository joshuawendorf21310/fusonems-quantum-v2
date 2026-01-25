from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_telehealth_db
from core.security import require_roles
from models.carefusion_billing import (
    CarefusionAuditEvent,
    CarefusionClaim,
    CarefusionLedgerEntry,
    CarefusionPayerRouting,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(prefix="/api/carefusion", tags=["Carefusion Billing"])


class LedgerCreate(BaseModel):
    entry_type: str = "debit"
    account: str = "telehealth_ar"
    amount: int
    currency: str = "usd"
    reference_type: str = ""
    reference_id: str = ""
    payload: dict = {}


class ClaimCreate(BaseModel):
    encounter_id: str = ""
    payer: str
    payload: dict = {}


class PayerRoutingCreate(BaseModel):
    payer: str
    route: str
    rules: dict = {}


@router.get("/ledger")
def list_ledger(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    entries = (
        scoped_query(db, CarefusionLedgerEntry, user.org_id, request.state.training_mode)
        .order_by(CarefusionLedgerEntry.created_at.desc())
        .all()
    )
    return [model_snapshot(entry) for entry in entries]


@router.post("/ledger", status_code=status.HTTP_201_CREATED)
def create_ledger_entry(
    payload: LedgerCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    entry = CarefusionLedgerEntry(org_id=user.org_id, **payload.dict())
    apply_training_mode(entry, request)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit = CarefusionAuditEvent(
        org_id=user.org_id,
        actor=user.email,
        action="create",
        resource="carefusion_ledger_entry",
        after_state=model_snapshot(entry),
    )
    db.add(audit)
    db.commit()
    return model_snapshot(entry)


@router.get("/claims")
def list_claims(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    claims = (
        scoped_query(db, CarefusionClaim, user.org_id, request.state.training_mode)
        .order_by(CarefusionClaim.created_at.desc())
        .all()
    )
    return [model_snapshot(claim) for claim in claims]


@router.post("/claims", status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    claim = CarefusionClaim(org_id=user.org_id, **payload.dict())
    apply_training_mode(claim, request)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    audit = CarefusionAuditEvent(
        org_id=user.org_id,
        actor=user.email,
        action="create",
        resource="carefusion_claim",
        after_state=model_snapshot(claim),
    )
    db.add(audit)
    db.commit()
    return model_snapshot(claim)


@router.get("/payer-routing")
def list_payer_routing(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    routes = (
        scoped_query(db, CarefusionPayerRouting, user.org_id, request.state.training_mode)
        .order_by(CarefusionPayerRouting.created_at.desc())
        .all()
    )
    return [model_snapshot(route) for route in routes]


@router.post("/payer-routing", status_code=status.HTTP_201_CREATED)
def create_payer_routing(
    payload: PayerRoutingCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    route = CarefusionPayerRouting(org_id=user.org_id, **payload.dict())
    apply_training_mode(route, request)
    db.add(route)
    db.commit()
    db.refresh(route)
    audit = CarefusionAuditEvent(
        org_id=user.org_id,
        actor=user.email,
        action="create",
        resource="carefusion_payer_routing",
        after_state=model_snapshot(route),
    )
    db.add(audit)
    db.commit()
    return model_snapshot(route)


@router.get("/audit")
def list_audit(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    events = (
        scoped_query(db, CarefusionAuditEvent, user.org_id, request.state.training_mode)
        .order_by(CarefusionAuditEvent.created_at.desc())
        .all()
    )
    return [model_snapshot(event) for event in events]
