from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.inventory import InventoryItem, InventoryMovement, InventoryRigCheck
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory"],
    dependencies=[Depends(require_module("INVENTORY"))],
)


class ItemCreate(BaseModel):
    name: str
    category: str = "medical"
    sku: str = ""
    manufacturer: str = ""
    unit: str = ""
    par_level: int = 0
    quantity_on_hand: int = 0
    location: str = ""
    status: str = "in_stock"


class MovementCreate(BaseModel):
    item_id: int
    movement_type: str = "transfer"
    quantity: int = 0
    from_location: str = ""
    to_location: str = ""
    reason: str = ""
    payload: dict = {}


class RigCheckCreate(BaseModel):
    unit_id: str
    status: str = "pass"
    findings: list = []
    performed_by: str = ""
    payload: dict = {}


@router.get("/items")
def list_items(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    items = (
        scoped_query(db, InventoryItem, user.org_id, request.state.training_mode)
        .order_by(InventoryItem.created_at.desc())
        .all()
    )
    return [model_snapshot(item) for item in items]


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = InventoryItem(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(item, request)
    db.add(item)
    db.commit()
    db.refresh(item)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="inventory_item",
        classification=item.classification,
        after_state=model_snapshot(item),
        event_type="inventory.item.created",
        event_payload={"item_id": item.id},
    )
    return model_snapshot(item)


@router.get("/movements")
def list_movements(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    movements = (
        scoped_query(db, InventoryMovement, user.org_id, request.state.training_mode)
        .order_by(InventoryMovement.created_at.desc())
        .all()
    )
    return [model_snapshot(movement) for movement in movements]


@router.post("/movements", status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: MovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = (
        scoped_query(db, InventoryItem, user.org_id, request.state.training_mode)
        .filter(InventoryItem.id == payload.item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Item not found")
    record = InventoryMovement(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="inventory_movement",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="inventory.movement.created",
        event_payload={"movement_id": record.id, "item_id": item.id},
    )
    return model_snapshot(record)


@router.get("/rig-checks")
def list_rig_checks(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    checks = (
        scoped_query(db, InventoryRigCheck, user.org_id, request.state.training_mode)
        .order_by(InventoryRigCheck.created_at.desc())
        .all()
    )
    return [model_snapshot(check) for check in checks]


@router.post("/rig-checks", status_code=status.HTTP_201_CREATED)
def create_rig_check(
    payload: RigCheckCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = InventoryRigCheck(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="inventory_rig_check",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="inventory.rig_check.created",
        event_payload={"rig_check_id": record.id},
    )
    return model_snapshot(record)
