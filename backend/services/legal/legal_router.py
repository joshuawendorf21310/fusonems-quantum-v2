from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.legal import Addendum, LegalHold, OverrideRequest
from models.user import User, UserRole
from utils.legal import enforce_legal_hold
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/legal-hold",
    tags=["Legal"],
    dependencies=[Depends(require_module("COMPLIANCE"))],
)


class LegalHoldCreate(BaseModel):
    scope_type: str
    scope_id: str
    reason: str = ""


class AddendumCreate(BaseModel):
    resource_type: str
    resource_id: str
    note: str


class OverrideCreate(BaseModel):
    override_type: str
    resource_type: str
    resource_id: str
    reason_code: str
    notes: str = ""


@router.post("", status_code=status.HTTP_201_CREATED)
def create_hold(
    payload: LegalHoldCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    hold = LegalHold(
        org_id=user.org_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        reason=payload.reason,
        created_by=user.email,
    )
    apply_training_mode(hold, request)
    db.add(hold)
    db.commit()
    db.refresh(hold)
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="legal_hold",
            classification=hold.classification,
            after_state=model_snapshot(hold),
            event_type="legal_hold.created",
            event_payload={"hold_id": hold.id},
        )
    return model_snapshot(hold)


@router.get("")
def list_holds(
    request: Request,
    scope_type: str | None = None,
    scope_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, LegalHold, user.org_id, request.state.training_mode)
    if scope_type:
        query = query.filter(LegalHold.scope_type == scope_type)
    if scope_id:
        query = query.filter(LegalHold.scope_id == scope_id)
    return query.order_by(LegalHold.created_at.desc()).all()


@router.post("/{hold_id}/release")
def release_hold(
    hold_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    hold = scoped_query(db, LegalHold, user.org_id, request.state.training_mode).filter(
        LegalHold.id == hold_id
    ).first()
    if not hold:
        return {"status": "not_found"}
    before = model_snapshot(hold)
    hold.status = "Released"
    hold.released_at = datetime.now(timezone.utc)
    db.commit()
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="release",
            resource="legal_hold",
            classification=hold.classification,
            before_state=before,
            after_state=model_snapshot(hold),
            event_type="legal_hold.released",
            event_payload={"hold_id": hold.id},
        )
    return {"status": "released", "hold_id": hold.id}


@router.post("/addenda", status_code=status.HTTP_201_CREATED)
def create_addendum(
    payload: AddendumCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.medical_director)),
):
    enforce_legal_hold(db, user.org_id, payload.resource_type, payload.resource_id, "addendum")
    addendum = Addendum(
        org_id=user.org_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        note=payload.note,
        author=user.email,
    )
    apply_training_mode(addendum, request)
    db.add(addendum)
    db.commit()
    db.refresh(addendum)
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="addendum",
            resource="addendum",
            classification=addendum.classification,
            after_state=model_snapshot(addendum),
            event_type="legal_hold.addendum.created",
            event_payload={"addendum_id": addendum.id},
        )
    return model_snapshot(addendum)


@router.get("/addenda")
def list_addenda(
    resource_type: str,
    resource_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return (
        scoped_query(db, Addendum, user.org_id, request.state.training_mode)
        .filter(Addendum.resource_type == resource_type, Addendum.resource_id == resource_id)
        .order_by(Addendum.created_at.desc())
        .all()
    )


@router.post("/overrides", status_code=status.HTTP_201_CREATED)
def create_override(
    payload: OverrideCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.medical_director, UserRole.hems_supervisor)),
):
    override = OverrideRequest(
        org_id=user.org_id,
        override_type=payload.override_type,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        reason_code=payload.reason_code,
        notes=payload.notes,
        created_by=user.email,
    )
    apply_training_mode(override, request)
    db.add(override)
    db.commit()
    db.refresh(override)
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="override_request",
            classification=override.classification,
            after_state=model_snapshot(override),
            event_type="legal_hold.override.created",
            event_payload={"override_id": override.id},
        )
    return model_snapshot(override)


@router.post("/overrides/{override_id}/approve")
def approve_override(
    override_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.medical_director)),
):
    override = scoped_query(db, OverrideRequest, user.org_id, request.state.training_mode).filter(
        OverrideRequest.id == override_id
    ).first()
    if not override:
        return {"status": "not_found"}
    before = model_snapshot(override)
    override.status = "Approved"
    override.approved_by = user.email
    override.approved_at = datetime.now(timezone.utc)
    db.commit()
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="approve",
            resource="override_request",
            classification=override.classification,
            before_state=before,
            after_state=model_snapshot(override),
            event_type="legal_hold.override.approved",
            event_payload={"override_id": override.id},
        )
    return {"status": "approved", "override_id": override.id}
