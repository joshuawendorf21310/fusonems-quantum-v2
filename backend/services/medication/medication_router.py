from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.medication import MedicationAdministration, MedicationFormularyVersion, MedicationMaster
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/medication",
    tags=["Medication"],
    dependencies=[Depends(require_module("MEDICATION"))],
)


class MedicationCreate(BaseModel):
    name: str
    brand: str = ""
    drug_class: str = ""
    schedule: str = "non_controlled"
    concentration: str = ""
    routes: list[str] = []
    status: str = "active"


class AdministrationCreate(BaseModel):
    patient_id: int | None = None
    medication_name: str
    dose: str = ""
    dose_units: str = ""
    route: str = ""
    time_administered: str = ""
    notes: str = ""
    payload: dict = {}


class FormularyCreate(BaseModel):
    version: str = "v1"
    status: str = "active"
    notes: str = ""
    payload: dict = {}


@router.get("/master")
def list_master(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    return scoped_query(db, MedicationMaster, user.org_id, request.state.training_mode).order_by(
        MedicationMaster.created_at.desc()
    )


@router.post("/master", status_code=status.HTTP_201_CREATED)
def create_master(
    payload: MedicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = MedicationMaster(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="medication_master",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="medication.master.created",
        event_payload={"medication_id": record.id},
    )
    return record


@router.get("/administrations")
def list_administrations(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    return scoped_query(
        db, MedicationAdministration, user.org_id, request.state.training_mode
    ).order_by(MedicationAdministration.created_at.desc())


@router.post("/administrations", status_code=status.HTTP_201_CREATED)
def create_administration(
    payload: AdministrationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = MedicationAdministration(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="medication_administration",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="medication.administration.created",
        event_payload={"administration_id": record.id},
    )
    return record


@router.get("/formulary")
def list_formulary(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    return scoped_query(
        db, MedicationFormularyVersion, user.org_id, request.state.training_mode
    ).order_by(MedicationFormularyVersion.created_at.desc())


@router.post("/formulary", status_code=status.HTTP_201_CREATED)
def create_formulary(
    payload: FormularyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    record = MedicationFormularyVersion(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="medication_formulary",
        classification="OPS",
        after_state=model_snapshot(record),
        event_type="medication.formulary.created",
        event_payload={"formulary_id": record.id},
    )
    return record
