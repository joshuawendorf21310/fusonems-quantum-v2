from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.inventory import (
    InventoryControlledLog,
    InventoryCount,
    InventoryCountItem,
    InventoryItem,
    InventoryLocation,
    InventoryLot,
    InventoryMovement,
    InventoryPurchaseOrder,
    InventoryPurchaseOrderItem,
    InventoryRecall,
    InventoryRigCheck,
    InventorySupplyKit,
    InventorySupplyKitItem,
    InventoryUnitStock,
    InventoryUsageLog,
)
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
    description: str = ""
    category: str = "supply"
    subcategory: str = ""
    sku: str = ""
    barcode: str = ""
    ndc_code: str = ""
    manufacturer: str = ""
    manufacturer_part: str = ""
    unit_of_measure: str = "each"
    unit_cost: float = 0.0
    par_level: int = 0
    reorder_point: int = 0
    reorder_quantity: int = 0
    quantity_on_hand: int = 0
    location: str = ""
    bin_location: str = ""
    supplier_name: str = ""
    supplier_sku: str = ""
    lead_time_days: int = 7
    is_controlled: bool = False
    dea_schedule: str | None = None
    requires_refrigeration: bool = False
    is_single_use: bool = True
    is_critical: bool = False


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    par_level: int | None = None
    reorder_point: int | None = None
    unit_cost: float | None = None
    supplier_name: str | None = None
    is_critical: bool | None = None
    is_active: bool | None = None


class LotCreate(BaseModel):
    item_id: int
    lot_number: str
    serial_number: str = ""
    expiration_date: datetime | None = None
    manufacture_date: datetime | None = None
    quantity: int = 0
    unit_cost: float = 0.0
    po_number: str = ""
    location_name: str = ""


class LocationCreate(BaseModel):
    name: str
    location_type: str = "station"
    parent_location_id: int | None = None
    address: str = ""
    is_vehicle: bool = False
    vehicle_id: int | None = None


class UnitStockCreate(BaseModel):
    location_id: int
    item_id: int
    lot_id: int | None = None
    quantity: int = 0
    par_level: int = 0
    bin_location: str = ""


class MovementCreate(BaseModel):
    item_id: int
    lot_id: int | None = None
    movement_type: str = "transfer"
    quantity: int = 0
    from_location_id: int | None = None
    from_location: str = ""
    to_location_id: int | None = None
    to_location: str = ""
    reference_type: str = ""
    reference_id: int | None = None
    reason: str = ""


class ControlledLogCreate(BaseModel):
    item_id: int
    lot_id: int | None = None
    location_id: int | None = None
    transaction_type: str
    quantity: int
    patient_id: int | None = None
    incident_id: int | None = None
    witness_id: int | None = None
    witness_name: str = ""
    waste_amount: float = 0.0
    waste_reason: str = ""
    seal_number_broken: str = ""
    seal_number_new: str = ""
    notes: str = ""
    signature: str = ""
    witness_signature: str = ""


class SupplyKitCreate(BaseModel):
    name: str
    kit_type: str = "custom"
    description: str = ""
    is_template: bool = False


class KitItemCreate(BaseModel):
    kit_id: int
    item_id: int
    quantity_required: int = 1
    is_critical: bool = False
    notes: str = ""


class RecallCreate(BaseModel):
    item_id: int
    recall_number: str
    recall_class: str = ""
    affected_lots: list = []
    reason: str = ""
    instructions: str = ""
    fda_recall_id: str = ""
    date_issued: datetime | None = None


class PurchaseOrderCreate(BaseModel):
    supplier_name: str = ""
    notes: str = ""


class POItemCreate(BaseModel):
    po_id: int
    item_id: int
    quantity_ordered: int = 0
    unit_cost: float = 0.0


class CountCreate(BaseModel):
    location_id: int | None = None
    count_type: str = "cycle"


class CountItemCreate(BaseModel):
    count_id: int
    item_id: int
    lot_id: int | None = None
    counted_quantity: int


class UsageLogCreate(BaseModel):
    item_id: int
    lot_id: int | None = None
    location_id: int | None = None
    incident_id: int | None = None
    patient_id: int | None = None
    quantity_used: int = 1
    usage_reason: str = "patient_care"
    notes: str = ""


class RigCheckCreate(BaseModel):
    location_id: int | None = None
    unit_id: str = ""
    check_type: str = "daily"
    findings: list = []
    signature: str = ""


@router.get("/dashboard")
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    base = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode)
    lots = scoped_query(db, InventoryLot, user.org_id, request.state.training_mode)
    controlled = scoped_query(db, InventoryControlledLog, user.org_id, request.state.training_mode)

    total_items = base.count()
    low_stock = base.filter(InventoryItem.quantity_on_hand <= InventoryItem.reorder_point).count()
    out_of_stock = base.filter(InventoryItem.quantity_on_hand == 0).count()
    controlled_items = base.filter(InventoryItem.is_controlled == True).count()

    now = datetime.utcnow()
    expired = lots.filter(InventoryLot.expiration_date < now, InventoryLot.quantity > 0).count()
    expiring_30 = lots.filter(
        InventoryLot.expiration_date >= now,
        InventoryLot.expiration_date <= now + timedelta(days=30),
        InventoryLot.quantity > 0
    ).count()
    expiring_90 = lots.filter(
        InventoryLot.expiration_date >= now,
        InventoryLot.expiration_date <= now + timedelta(days=90),
        InventoryLot.quantity > 0
    ).count()

    today = now.date()
    cs_today = controlled.filter(sqlfunc.date(InventoryControlledLog.created_at) == today).count()

    total_value = db.query(sqlfunc.sum(InventoryItem.quantity_on_hand * InventoryItem.unit_cost)).filter(
        InventoryItem.org_id == user.org_id
    ).scalar() or 0

    return {
        "total_items": total_items,
        "low_stock_items": low_stock,
        "out_of_stock_items": out_of_stock,
        "controlled_items": controlled_items,
        "expired_lots": expired,
        "expiring_30_days": expiring_30,
        "expiring_90_days": expiring_90,
        "controlled_transactions_today": cs_today,
        "total_inventory_value": round(total_value, 2),
    }


@router.get("/items")
def list_items(
    request: Request,
    category: str | None = None,
    is_controlled: bool | None = None,
    low_stock: bool = False,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode)
    if category:
        query = query.filter(InventoryItem.category == category)
    if is_controlled is not None:
        query = query.filter(InventoryItem.is_controlled == is_controlled)
    if low_stock:
        query = query.filter(InventoryItem.quantity_on_hand <= InventoryItem.reorder_point)
    if search:
        query = query.filter(
            (InventoryItem.name.ilike(f"%{search}%")) |
            (InventoryItem.sku.ilike(f"%{search}%")) |
            (InventoryItem.barcode.ilike(f"%{search}%"))
        )
    items = query.order_by(InventoryItem.name).offset(offset).limit(limit).all()
    return [model_snapshot(item) for item in items]


@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    lots = scoped_query(db, InventoryLot, user.org_id, request.state.training_mode).filter(
        InventoryLot.item_id == item_id, InventoryLot.quantity > 0
    ).all()
    return {
        **model_snapshot(item),
        "lots": [model_snapshot(lot) for lot in lots],
    }


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    item = InventoryItem(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(item, request)
    db.add(item)
    db.commit()
    db.refresh(item)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="inventory_item",
        classification="OPS", after_state=model_snapshot(item),
        event_type="inventory.item.created", event_payload={"item_id": item.id},
    )
    return model_snapshot(item)


@router.patch("/items/{item_id}")
def update_item(
    item_id: int,
    payload: ItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    before = model_snapshot(item)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    audit_and_event(
        db=db, request=request, user=user, action="update", resource="inventory_item",
        classification="OPS", before_state=before, after_state=model_snapshot(item),
        event_type="inventory.item.updated", event_payload={"item_id": item.id},
    )
    return model_snapshot(item)


@router.get("/items/{item_id}/barcode")
def get_barcode(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "item_id": item.id,
        "name": item.name,
        "sku": item.sku,
        "barcode": item.barcode or item.sku or f"INV-{item.id:06d}",
        "ndc": item.ndc_code,
    }


@router.post("/items/lookup")
def lookup_by_barcode(
    barcode: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        (InventoryItem.barcode == barcode) | (InventoryItem.sku == barcode)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return model_snapshot(item)


@router.get("/lots")
def list_lots(
    request: Request,
    item_id: int | None = None,
    expiring_days: int | None = None,
    expired: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryLot, user.org_id, request.state.training_mode)
    if item_id:
        query = query.filter(InventoryLot.item_id == item_id)
    now = datetime.utcnow()
    if expired:
        query = query.filter(InventoryLot.expiration_date < now)
    elif expiring_days:
        query = query.filter(
            InventoryLot.expiration_date >= now,
            InventoryLot.expiration_date <= now + timedelta(days=expiring_days)
        )
    lots = query.filter(InventoryLot.quantity > 0).order_by(InventoryLot.expiration_date).limit(200).all()
    return [model_snapshot(lot) for lot in lots]


@router.post("/lots", status_code=status.HTTP_201_CREATED)
def create_lot(
    payload: LotCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == payload.item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    lot = InventoryLot(
        org_id=user.org_id,
        received_by=user.id,
        quantity_available=payload.quantity,
        **payload.model_dump()
    )
    apply_training_mode(lot, request)
    db.add(lot)
    item.quantity_on_hand += payload.quantity
    db.commit()
    db.refresh(lot)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="inventory_lot",
        classification="OPS", after_state=model_snapshot(lot),
        event_type="inventory.lot.received", event_payload={"lot_id": lot.id, "item_id": item.id, "quantity": payload.quantity},
    )
    return model_snapshot(lot)


@router.get("/lots/expiring")
def get_expiring_lots(
    request: Request,
    days: int = 90,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    now = datetime.utcnow()
    lots = scoped_query(db, InventoryLot, user.org_id, request.state.training_mode).filter(
        InventoryLot.expiration_date <= now + timedelta(days=days),
        InventoryLot.quantity > 0
    ).order_by(InventoryLot.expiration_date).all()

    result = []
    for lot in lots:
        item = db.query(InventoryItem).filter(InventoryItem.id == lot.item_id).first()
        days_until = (lot.expiration_date - now).days if lot.expiration_date else None
        result.append({
            **model_snapshot(lot),
            "item_name": item.name if item else "",
            "item_category": item.category if item else "",
            "days_until_expiration": days_until,
            "is_expired": days_until < 0 if days_until is not None else False,
            "value_at_risk": lot.quantity * (lot.unit_cost or 0),
        })
    return result


@router.get("/locations")
def list_locations(
    request: Request,
    location_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryLocation, user.org_id, request.state.training_mode)
    if location_type:
        query = query.filter(InventoryLocation.location_type == location_type)
    locations = query.filter(InventoryLocation.is_active == True).order_by(InventoryLocation.name).all()
    return [model_snapshot(loc) for loc in locations]


@router.post("/locations", status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    location = InventoryLocation(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(location, request)
    db.add(location)
    db.commit()
    db.refresh(location)
    return model_snapshot(location)


@router.get("/locations/{location_id}/stock")
def get_location_stock(
    location_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    stock = scoped_query(db, InventoryUnitStock, user.org_id, request.state.training_mode).filter(
        InventoryUnitStock.location_id == location_id
    ).all()
    result = []
    for s in stock:
        item = db.query(InventoryItem).filter(InventoryItem.id == s.item_id).first()
        result.append({
            **model_snapshot(s),
            "item_name": item.name if item else "",
            "item_category": item.category if item else "",
            "below_par": s.quantity < s.par_level,
        })
    return result


@router.post("/unit-stock", status_code=status.HTTP_201_CREATED)
def create_unit_stock(
    payload: UnitStockCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    stock = InventoryUnitStock(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(stock, request)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return model_snapshot(stock)


@router.get("/movements")
def list_movements(
    request: Request,
    item_id: int | None = None,
    movement_type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryMovement, user.org_id, request.state.training_mode)
    if item_id:
        query = query.filter(InventoryMovement.item_id == item_id)
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    movements = query.order_by(InventoryMovement.created_at.desc()).limit(limit).all()
    return [model_snapshot(m) for m in movements]


@router.post("/movements", status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: MovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == payload.item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    movement = InventoryMovement(
        org_id=user.org_id,
        performed_by=user.id,
        cost=payload.quantity * item.unit_cost,
        **payload.model_dump()
    )
    apply_training_mode(movement, request)
    db.add(movement)
    db.commit()
    db.refresh(movement)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="inventory_movement",
        classification="OPS", after_state=model_snapshot(movement),
        event_type="inventory.movement.created", event_payload={"movement_id": movement.id},
    )
    return model_snapshot(movement)


@router.get("/controlled")
def list_controlled_items(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    items = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.is_controlled == True
    ).order_by(InventoryItem.dea_schedule, InventoryItem.name).all()
    return [model_snapshot(item) for item in items]


@router.get("/controlled/logs")
def list_controlled_logs(
    request: Request,
    item_id: int | None = None,
    transaction_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryControlledLog, user.org_id, request.state.training_mode)
    if item_id:
        query = query.filter(InventoryControlledLog.item_id == item_id)
    if transaction_type:
        query = query.filter(InventoryControlledLog.transaction_type == transaction_type)
    if start_date:
        query = query.filter(InventoryControlledLog.created_at >= start_date)
    if end_date:
        query = query.filter(InventoryControlledLog.created_at <= end_date)
    logs = query.order_by(InventoryControlledLog.created_at.desc()).limit(limit).all()
    return [model_snapshot(log) for log in logs]


@router.post("/controlled/logs", status_code=status.HTTP_201_CREATED)
def create_controlled_log(
    payload: ControlledLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == payload.item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.is_controlled:
        raise HTTPException(status_code=400, detail="Item is not a controlled substance")

    balance_before = item.quantity_on_hand
    if payload.transaction_type in ["administer", "waste", "transfer_out", "adjustment_down"]:
        if payload.quantity > balance_before:
            raise HTTPException(status_code=400, detail="Insufficient quantity")
        balance_after = balance_before - payload.quantity
    elif payload.transaction_type in ["receive", "transfer_in", "adjustment_up"]:
        balance_after = balance_before + payload.quantity
    else:
        balance_after = balance_before

    if payload.transaction_type in ["administer", "waste"] and item.dea_schedule in ["II", "III"]:
        if not payload.witness_id and not payload.witness_signature:
            raise HTTPException(status_code=400, detail="Witness required for Schedule II/III substances")

    log = InventoryControlledLog(
        org_id=user.org_id,
        employee_id=user.id,
        employee_name=f"{user.first_name} {user.last_name}",
        balance_before=balance_before,
        balance_after=balance_after,
        waste_witnessed=bool(payload.witness_id or payload.witness_signature),
        **payload.model_dump()
    )
    apply_training_mode(log, request)
    db.add(log)
    item.quantity_on_hand = balance_after
    db.commit()
    db.refresh(log)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="controlled_substance_log",
        classification="PHI", after_state=model_snapshot(log),
        event_type="inventory.controlled.transaction",
        event_payload={
            "log_id": log.id,
            "item_id": item.id,
            "transaction_type": payload.transaction_type,
            "quantity": payload.quantity,
            "dea_schedule": item.dea_schedule,
        },
    )
    return model_snapshot(log)


@router.get("/controlled/report")
def get_controlled_report(
    request: Request,
    start_date: datetime,
    end_date: datetime,
    item_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    query = scoped_query(db, InventoryControlledLog, user.org_id, request.state.training_mode).filter(
        InventoryControlledLog.created_at >= start_date,
        InventoryControlledLog.created_at <= end_date
    )
    if item_id:
        query = query.filter(InventoryControlledLog.item_id == item_id)
    logs = query.order_by(InventoryControlledLog.created_at).limit(1000).all()  # Limit to prevent memory issues

    items = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.is_controlled == True
    ).all()
    item_map = {i.id: i for i in items}

    summary = {}
    for log in logs:
        item = item_map.get(log.item_id)
        if not item:
            continue
        if item.id not in summary:
            summary[item.id] = {
                "item_id": item.id,
                "item_name": item.name,
                "dea_schedule": item.dea_schedule,
                "opening_balance": log.balance_before,
                "received": 0,
                "administered": 0,
                "wasted": 0,
                "transferred_out": 0,
                "transferred_in": 0,
                "adjustments": 0,
                "closing_balance": log.balance_after,
                "transactions": [],
            }
        if log.transaction_type == "receive":
            summary[item.id]["received"] += log.quantity
        elif log.transaction_type == "administer":
            summary[item.id]["administered"] += log.quantity
        elif log.transaction_type == "waste":
            summary[item.id]["wasted"] += log.quantity
        elif log.transaction_type == "transfer_out":
            summary[item.id]["transferred_out"] += log.quantity
        elif log.transaction_type == "transfer_in":
            summary[item.id]["transferred_in"] += log.quantity
        summary[item.id]["closing_balance"] = log.balance_after
        summary[item.id]["transactions"].append({
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "type": log.transaction_type,
            "quantity": log.quantity,
            "balance": log.balance_after,
            "employee": log.employee_name,
            "witness": log.witness_name,
            "patient_id": log.patient_id,
        })

    return {
        "report_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": f"{user.first_name} {user.last_name}",
        "substances": list(summary.values()),
    }


@router.get("/controlled/discrepancies")
def get_discrepancies(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    logs = scoped_query(db, InventoryControlledLog, user.org_id, request.state.training_mode).filter(
        InventoryControlledLog.discrepancy_noted == True
    ).order_by(InventoryControlledLog.created_at.desc()).limit(50).all()
    return [model_snapshot(log) for log in logs]


@router.get("/supply-kits")
def list_supply_kits(
    request: Request,
    kit_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventorySupplyKit, user.org_id, request.state.training_mode)
    if kit_type:
        query = query.filter(InventorySupplyKit.kit_type == kit_type)
    kits = query.filter(InventorySupplyKit.is_active == True).order_by(InventorySupplyKit.name).all()
    return [model_snapshot(kit) for kit in kits]


@router.get("/supply-kits/{kit_id}")
def get_supply_kit(
    kit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    kit = scoped_query(db, InventorySupplyKit, user.org_id, request.state.training_mode).filter(
        InventorySupplyKit.id == kit_id
    ).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")
    kit_items = scoped_query(db, InventorySupplyKitItem, user.org_id, request.state.training_mode).filter(
        InventorySupplyKitItem.kit_id == kit_id
    ).all()

    items_detail = []
    for ki in kit_items:
        item = db.query(InventoryItem).filter(InventoryItem.id == ki.item_id).first()
        items_detail.append({
            **model_snapshot(ki),
            "item_name": item.name if item else "",
            "item_sku": item.sku if item else "",
            "quantity_available": item.quantity_on_hand if item else 0,
            "is_stocked": (item.quantity_on_hand >= ki.quantity_required) if item else False,
        })

    return {
        **model_snapshot(kit),
        "items": items_detail,
        "total_items": len(kit_items),
        "items_stocked": sum(1 for i in items_detail if i["is_stocked"]),
    }


@router.post("/supply-kits", status_code=status.HTTP_201_CREATED)
def create_supply_kit(
    payload: SupplyKitCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    kit = InventorySupplyKit(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(kit, request)
    db.add(kit)
    db.commit()
    db.refresh(kit)
    return model_snapshot(kit)


@router.post("/supply-kits/items", status_code=status.HTTP_201_CREATED)
def add_kit_item(
    payload: KitItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    kit_item = InventorySupplyKitItem(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(kit_item, request)
    db.add(kit_item)
    db.commit()
    db.refresh(kit_item)
    return model_snapshot(kit_item)


@router.get("/recalls")
def list_recalls(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryRecall, user.org_id, request.state.training_mode)
    if status:
        query = query.filter(InventoryRecall.status == status)
    recalls = query.order_by(InventoryRecall.created_at.desc()).limit(500).all()  # Limit to prevent memory issues
    return [model_snapshot(recall) for recall in recalls]


@router.post("/recalls", status_code=status.HTTP_201_CREATED)
def create_recall(
    payload: RecallCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    recall = InventoryRecall(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(recall, request)
    db.add(recall)
    db.commit()
    db.refresh(recall)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="inventory_recall",
        classification="OPS", after_state=model_snapshot(recall),
        event_type="inventory.recall.created", event_payload={"recall_id": recall.id},
    )
    return model_snapshot(recall)


@router.get("/purchase-orders")
def list_purchase_orders(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    query = scoped_query(db, InventoryPurchaseOrder, user.org_id, request.state.training_mode)
    if status:
        query = query.filter(InventoryPurchaseOrder.status == status)
    pos = query.order_by(InventoryPurchaseOrder.created_at.desc()).all()
    return [model_snapshot(po) for po in pos]


@router.post("/purchase-orders", status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{user.org_id:03d}"
    po = InventoryPurchaseOrder(
        org_id=user.org_id,
        po_number=po_number,
        created_by=user.id,
        **payload.model_dump()
    )
    apply_training_mode(po, request)
    db.add(po)
    db.commit()
    db.refresh(po)
    return model_snapshot(po)


@router.get("/reorder-suggestions")
def get_reorder_suggestions(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    items = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.quantity_on_hand <= InventoryItem.reorder_point,
        InventoryItem.is_active == True
    ).order_by(
        (InventoryItem.quantity_on_hand == 0).desc(),
        InventoryItem.is_critical.desc()
    ).all()

    suggestions = []
    for item in items:
        qty_to_order = max(item.reorder_quantity, item.par_level - item.quantity_on_hand)
        suggestions.append({
            "item_id": item.id,
            "name": item.name,
            "sku": item.sku,
            "category": item.category,
            "current_qty": item.quantity_on_hand,
            "par_level": item.par_level,
            "reorder_point": item.reorder_point,
            "suggested_order_qty": qty_to_order,
            "unit_cost": item.unit_cost,
            "estimated_cost": qty_to_order * item.unit_cost,
            "supplier": item.supplier_name,
            "lead_time_days": item.lead_time_days,
            "is_critical": item.is_critical,
            "is_out_of_stock": item.quantity_on_hand == 0,
        })
    return suggestions


@router.get("/counts")
def list_counts(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryCount, user.org_id, request.state.training_mode)
    if status:
        query = query.filter(InventoryCount.status == status)
    counts = query.order_by(InventoryCount.created_at.desc()).limit(50).all()
    return [model_snapshot(count) for count in counts]


@router.post("/counts", status_code=status.HTTP_201_CREATED)
def start_count(
    payload: CountCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    count = InventoryCount(
        org_id=user.org_id,
        performed_by=user.id,
        **payload.model_dump()
    )
    apply_training_mode(count, request)
    db.add(count)
    db.commit()
    db.refresh(count)
    return model_snapshot(count)


@router.post("/counts/{count_id}/items", status_code=status.HTTP_201_CREATED)
def record_count_item(
    count_id: int,
    payload: CountItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    count = scoped_query(db, InventoryCount, user.org_id, request.state.training_mode).filter(
        InventoryCount.id == count_id
    ).first()
    if not count:
        raise HTTPException(status_code=404, detail="Count not found")
    item = db.query(InventoryItem).filter(InventoryItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    variance = payload.counted_quantity - item.quantity_on_hand
    count_item = InventoryCountItem(
        org_id=user.org_id,
        count_id=count_id,
        item_id=payload.item_id,
        lot_id=payload.lot_id,
        expected_quantity=item.quantity_on_hand,
        counted_quantity=payload.counted_quantity,
        variance=variance,
    )
    apply_training_mode(count_item, request)
    db.add(count_item)
    count.items_counted += 1
    if variance != 0:
        count.discrepancies_found += 1
    db.commit()
    db.refresh(count_item)
    return model_snapshot(count_item)


@router.get("/usage")
def list_usage(
    request: Request,
    item_id: int | None = None,
    incident_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryUsageLog, user.org_id, request.state.training_mode)
    if item_id:
        query = query.filter(InventoryUsageLog.item_id == item_id)
    if incident_id:
        query = query.filter(InventoryUsageLog.incident_id == incident_id)
    if start_date:
        query = query.filter(InventoryUsageLog.created_at >= start_date)
    if end_date:
        query = query.filter(InventoryUsageLog.created_at <= end_date)
    logs = query.order_by(InventoryUsageLog.created_at.desc()).limit(limit).all()
    return [model_snapshot(log) for log in logs]


@router.post("/usage", status_code=status.HTTP_201_CREATED)
def record_usage(
    payload: UsageLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    item = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).filter(
        InventoryItem.id == payload.item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    log = InventoryUsageLog(
        org_id=user.org_id,
        used_by=user.id,
        unit_cost=item.unit_cost,
        total_cost=payload.quantity_used * item.unit_cost,
        **payload.model_dump()
    )
    apply_training_mode(log, request)
    db.add(log)
    item.quantity_on_hand = max(0, item.quantity_on_hand - payload.quantity_used)
    db.commit()
    db.refresh(log)
    return model_snapshot(log)


@router.get("/usage/cost-report")
def get_usage_cost_report(
    request: Request,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    logs = scoped_query(db, InventoryUsageLog, user.org_id, request.state.training_mode).filter(
        InventoryUsageLog.created_at >= start_date,
        InventoryUsageLog.created_at <= end_date
    ).all()

    by_category = {}
    by_incident = {}
    total_cost = 0

    for log in logs:
        item = db.query(InventoryItem).filter(InventoryItem.id == log.item_id).first()
        if not item:
            continue
        cat = item.category
        if cat not in by_category:
            by_category[cat] = {"category": cat, "quantity": 0, "cost": 0}
        by_category[cat]["quantity"] += log.quantity_used
        by_category[cat]["cost"] += log.total_cost
        total_cost += log.total_cost

        if log.incident_id:
            if log.incident_id not in by_incident:
                by_incident[log.incident_id] = {"incident_id": log.incident_id, "items": 0, "cost": 0}
            by_incident[log.incident_id]["items"] += log.quantity_used
            by_incident[log.incident_id]["cost"] += log.total_cost

    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "total_cost": round(total_cost, 2),
        "total_items_used": sum(c["quantity"] for c in by_category.values()),
        "by_category": list(by_category.values()),
        "by_incident": list(by_incident.values()),
        "average_cost_per_incident": round(total_cost / len(by_incident), 2) if by_incident else 0,
    }


@router.get("/rig-checks")
def list_rig_checks(
    request: Request,
    unit_id: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    query = scoped_query(db, InventoryRigCheck, user.org_id, request.state.training_mode)
    if unit_id:
        query = query.filter(InventoryRigCheck.unit_id == unit_id)
    checks = query.order_by(InventoryRigCheck.created_at.desc()).limit(limit).all()
    return [model_snapshot(check) for check in checks]


@router.post("/rig-checks", status_code=status.HTTP_201_CREATED)
def create_rig_check(
    payload: RigCheckCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    check = InventoryRigCheck(
        org_id=user.org_id,
        performed_by=f"{user.first_name} {user.last_name}",
        performed_by_id=user.id,
        status="pass" if not payload.findings else "fail",
        items_failed=len([f for f in payload.findings if f.get("status") == "fail"]),
        items_expired=len([f for f in payload.findings if f.get("expired")]),
        items_below_par=len([f for f in payload.findings if f.get("below_par")]),
        **payload.model_dump()
    )
    apply_training_mode(check, request)
    db.add(check)
    db.commit()
    db.refresh(check)
    audit_and_event(
        db=db, request=request, user=user, action="create", resource="inventory_rig_check",
        classification="OPS", after_state=model_snapshot(check),
        event_type="inventory.rig_check.created", event_payload={"check_id": check.id, "unit_id": check.unit_id},
    )
    return model_snapshot(check)


@router.get("/analytics/turnover")
def get_turnover_analytics(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    start = datetime.utcnow() - timedelta(days=days)
    usage = scoped_query(db, InventoryUsageLog, user.org_id, request.state.training_mode).filter(
        InventoryUsageLog.created_at >= start
    ).all()

    item_usage = {}
    for log in usage:
        if log.item_id not in item_usage:
            item_usage[log.item_id] = 0
        item_usage[log.item_id] += log.quantity_used

    items = scoped_query(db, InventoryItem, user.org_id, request.state.training_mode).limit(1000).all()  # Limit to prevent memory issues
    item_map = {i.id: i for i in items}

    turnover = []
    for item_id, used in item_usage.items():
        item = item_map.get(item_id)
        if item and item.par_level > 0:
            rate = used / days
            days_of_stock = item.quantity_on_hand / rate if rate > 0 else 999
            turnover.append({
                "item_id": item.id,
                "name": item.name,
                "category": item.category,
                "quantity_used": used,
                "daily_usage_rate": round(rate, 2),
                "current_stock": item.quantity_on_hand,
                "days_of_stock_remaining": round(days_of_stock, 1),
                "par_level": item.par_level,
                "reorder_recommended": days_of_stock < item.lead_time_days,
            })

    turnover.sort(key=lambda x: x["days_of_stock_remaining"])
    return turnover[:50]
