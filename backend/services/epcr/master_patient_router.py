from fastapi import APIRouter, Depends, Request, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.epcr import MasterPatient, MasterPatientMerge
from models.user import User, UserRole
from utils.tenancy import get_scoped_record
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(
    prefix="/api",
    tags=["ePCR"],
    dependencies=[Depends(require_module("EPCR"))],
)


class MasterPatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    phone: str = ""
    address: str = ""


class MasterPatientResponse(MasterPatientCreate):
    id: int
    merged_into_id: int | None = None

    class Config:
        from_attributes = True


class MasterPatientMergeRequest(BaseModel):
    from_master_patient_id: int
    reason: str = ""


@router.post("/master_patients", response_model=MasterPatientResponse, status_code=status.HTTP_201_CREATED)
def create_master_patient(
    payload: MasterPatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    master_patient = MasterPatient(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(master_patient, request)
    db.add(master_patient)
    db.commit()
    db.refresh(master_patient)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="master_patient",
        classification=master_patient.classification,
        after_state=model_snapshot(master_patient),
        event_type="epcr.master_patient.created",
        event_payload={"master_patient_id": master_patient.id},
    )
    return master_patient


@router.get("/master_patients/{master_patient_id}", response_model=MasterPatientResponse)
def get_master_patient(
    master_patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    master_patient = get_scoped_record(db, request, MasterPatient, master_patient_id, user, resource_label="master_patient")
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="master_patient",
        classification=master_patient.classification,
        after_state=model_snapshot(master_patient),
        event_type="epcr.master_patient.read",
        event_payload={"master_patient_id": master_patient.id},
        reason_code="READ",
    )
    return master_patient


@router.post("/master_patients/{master_patient_id}/merge", status_code=status.HTTP_201_CREATED)
def merge_master_patient(
    master_patient_id: int,
    payload: MasterPatientMergeRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    to_patient = get_scoped_record(db, request, MasterPatient, master_patient_id, user, resource_label="master_patient")
    from_patient = get_scoped_record(
        db, request, MasterPatient, payload.from_master_patient_id, user, resource_label="master_patient"
    )
    if from_patient.id == to_patient.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot merge into itself")
    if from_patient.merged_into_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source master patient already merged")
    merge = MasterPatientMerge(
        org_id=user.org_id,
        from_id=from_patient.id,
        to_id=to_patient.id,
        reason=payload.reason,
        actor=str(user.id),
    )
    from_patient.merged_into_id = to_patient.id
    apply_training_mode(merge, request)
    db.add(merge)
    db.commit()
    db.refresh(merge)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="merge",
        resource="master_patient_merge",
        classification=to_patient.classification,
        after_state=model_snapshot(merge),
        event_type="epcr.master_patient.merged",
        event_payload={
            "from_master_patient_id": from_patient.id,
            "to_master_patient_id": to_patient.id,
            "reason": payload.reason,
        },
    )
    return {"status": "merged", "merge_id": merge.id}
