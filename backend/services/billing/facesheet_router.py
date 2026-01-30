from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.epcr import Patient
from models.user import User, UserRole
from services.billing.facesheet_retriever import FacesheetRetriever
from services.telnyx.helpers import require_telnyx_enabled
from utils.tenancy import get_scoped_record


router = APIRouter(prefix="/api/billing/facesheet", tags=["Billing", "Facesheet"], dependencies=[Depends(require_module("BILLING"))])


class FacesheetRequest(BaseModel):
    epcr_patient_id: int


@router.post("/request")
def request_facesheet(
    payload: FacesheetRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    require_telnyx_enabled()
    patient = get_scoped_record(db, request, Patient, payload.epcr_patient_id, user, resource_label="epcr")
    service = FacesheetRetriever(db, user.org_id)
    response = service.auto_fetch_facesheet(request, user, patient)
    return response


@router.get("/status/{epcr_patient_id}")
def facesheet_status(
    epcr_patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    require_telnyx_enabled()
    patient = get_scoped_record(db, request, Patient, epcr_patient_id, user, resource_label="epcr")
    service = FacesheetRetriever(db, user.org_id)
    return service.facesheet_status(patient)


@router.post("/send-fax")
def send_facesheet_request_fax(
    payload: FacesheetRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    """Send an outbound fax to the facility requesting a facesheet. Call after /request when details.outbound_fax_available is true."""
    require_telnyx_enabled()
    patient = get_scoped_record(db, request, Patient, payload.epcr_patient_id, user, resource_label="epcr")
    service = FacesheetRetriever(db, user.org_id)
    return service.send_facesheet_request_fax(patient)
