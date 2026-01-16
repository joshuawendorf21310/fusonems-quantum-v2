from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.fleet import FleetInspection, FleetMaintenance, FleetTelemetry, FleetVehicle
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/fleet",
    tags=["Fleet"],
    dependencies=[Depends(require_module("FLEET"))],
)


class VehicleCreate(BaseModel):
    vehicle_id: str
    call_sign: str = ""
    vehicle_type: str = "ALS"
    make: str = ""
    model: str = ""
    year: str = ""
    vin: str = ""
    status: str = "in_service"
    location: str = ""


class MaintenanceCreate(BaseModel):
    vehicle_id: int
    service_type: str = "maintenance"
    status: str = "scheduled"
    due_mileage: int = 0
    notes: str = ""
    payload: dict = {}


class InspectionCreate(BaseModel):
    vehicle_id: int
    status: str = "pass"
    findings: list = []
    performed_by: str = ""
    payload: dict = {}


class TelemetryCreate(BaseModel):
    vehicle_id: int
    latitude: str = ""
    longitude: str = ""
    speed: str = ""
    odometer: str = ""
    payload: dict = {}


@router.get("/vehicles")
def list_vehicles(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    vehicles = (
        scoped_query(db, FleetVehicle, user.org_id, request.state.training_mode)
        .order_by(FleetVehicle.created_at.desc())
        .all()
    )
    return [model_snapshot(vehicle) for vehicle in vehicles]


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = FleetVehicle(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fleet_vehicle",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="fleet.vehicle.created",
        event_payload={"vehicle_id": record.id},
    )
    return model_snapshot(record)


@router.get("/maintenance")
def list_maintenance(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    records = (
        scoped_query(db, FleetMaintenance, user.org_id, request.state.training_mode)
        .order_by(FleetMaintenance.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("/maintenance", status_code=status.HTTP_201_CREATED)
def create_maintenance(
    payload: MaintenanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    vehicle = (
        scoped_query(db, FleetVehicle, user.org_id, request.state.training_mode)
        .filter(FleetVehicle.id == payload.vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vehicle not found")
    record = FleetMaintenance(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fleet_maintenance",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="fleet.maintenance.created",
        event_payload={"maintenance_id": record.id, "vehicle_id": vehicle.id},
    )
    return model_snapshot(record)


@router.get("/inspections")
def list_inspections(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    records = (
        scoped_query(db, FleetInspection, user.org_id, request.state.training_mode)
        .order_by(FleetInspection.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("/inspections", status_code=status.HTTP_201_CREATED)
def create_inspection(
    payload: InspectionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    vehicle = (
        scoped_query(db, FleetVehicle, user.org_id, request.state.training_mode)
        .filter(FleetVehicle.id == payload.vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vehicle not found")
    record = FleetInspection(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fleet_inspection",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="fleet.inspection.created",
        event_payload={"inspection_id": record.id, "vehicle_id": vehicle.id},
    )
    return model_snapshot(record)


@router.get("/telemetry")
def list_telemetry(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    records = (
        scoped_query(db, FleetTelemetry, user.org_id, request.state.training_mode)
        .order_by(FleetTelemetry.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("/telemetry", status_code=status.HTTP_201_CREATED)
def create_telemetry(
    payload: TelemetryCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    vehicle = (
        scoped_query(db, FleetVehicle, user.org_id, request.state.training_mode)
        .filter(FleetVehicle.id == payload.vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vehicle not found")
    record = FleetTelemetry(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="fleet_telemetry",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="fleet.telemetry.created",
        event_payload={"telemetry_id": record.id, "vehicle_id": vehicle.id},
    )
    return model_snapshot(record)
