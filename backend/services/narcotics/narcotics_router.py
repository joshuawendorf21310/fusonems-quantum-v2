from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles, require_mfa
from models.narcotics import NarcoticCustodyEvent, NarcoticDiscrepancy, NarcoticItem
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/narcotics",
    tags=["Narcotics"],
    dependencies=[Depends(require_module("NARCOTICS")), Depends(require_mfa)],
)


class NarcoticCreate(BaseModel):
    name: str
    schedule: str = "II"
    concentration: str = ""
    lot_number: str = ""
    expiration_date: str = ""
    quantity: str = "0"
    storage_location: str = ""
    status: str = "in_service"


class CustodyCreate(BaseModel):
    narcotic_id: int
    event_type: str
    from_location: str = ""
    to_location: str = ""
    quantity: str = "0"
    witness: str = ""
    notes: str = ""
    payload: dict = {}


class DiscrepancyCreate(BaseModel):
    narcotic_id: int
    severity: str = "High"
    summary: str = ""
    payload: dict = {}


@router.get("/items")
def list_items(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    items = (
        scoped_query(db, NarcoticItem, user.org_id, request.state.training_mode)
        .order_by(NarcoticItem.created_at.desc())
        .all()
    )
    return [model_snapshot(item) for item in items]


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    payload: NarcoticCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = NarcoticItem(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(item, request)
    db.add(item)
    db.commit()
    db.refresh(item)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="narcotic_item",
        classification=item.classification,
        after_state=model_snapshot(item),
        event_type="narcotics.item.created",
        event_payload={"narcotic_id": item.id},
    )
    return model_snapshot(item)


@router.post("/custody", status_code=status.HTTP_201_CREATED)
def log_custody(
    payload: CustodyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = (
        scoped_query(db, NarcoticItem, user.org_id, request.state.training_mode)
        .filter(NarcoticItem.id == payload.narcotic_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Narcotic not found")
    event = NarcoticCustodyEvent(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(event, request)
    db.add(event)
    db.commit()
    db.refresh(event)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="narcotic_custody",
        classification=event.classification,
        after_state=model_snapshot(event),
        event_type="narcotics.custody.created",
        event_payload={"custody_id": event.id, "narcotic_id": item.id, "event_type": event.event_type},
    )
    return model_snapshot(event)


@router.get("/custody")
def list_custody(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    events = (
        scoped_query(db, NarcoticCustodyEvent, user.org_id, request.state.training_mode)
        .order_by(NarcoticCustodyEvent.created_at.desc())
        .all()
    )
    return [model_snapshot(event) for event in events]


@router.post("/discrepancies", status_code=status.HTTP_201_CREATED)
def create_discrepancy(
    payload: DiscrepancyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = (
        scoped_query(db, NarcoticItem, user.org_id, request.state.training_mode)
        .filter(NarcoticItem.id == payload.narcotic_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Narcotic not found")
    record = NarcoticDiscrepancy(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="narcotic_discrepancy",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="narcotics.discrepancy.created",
        event_payload={"discrepancy_id": record.id, "narcotic_id": item.id},
    )
    return model_snapshot(record)


@router.get("/discrepancies")
def list_discrepancies(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    records = (
        scoped_query(db, NarcoticDiscrepancy, user.org_id, request.state.training_mode)
        .order_by(NarcoticDiscrepancy.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]
