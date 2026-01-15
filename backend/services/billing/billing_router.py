from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import require_roles
from models.billing import BillingRecord
from models.business_ops import BusinessOpsTask
from models.user import UserRole


router = APIRouter(prefix="/api/billing", tags=["Billing"])


class BillingCreate(BaseModel):
    patient_name: str
    invoice_number: str
    payer: str
    amount_due: float
    status: str = "Open"
    claim_payload: dict = {}


class BillingResponse(BillingCreate):
    id: int

    class Config:
        from_attributes = True


class BusinessOpsCreate(BaseModel):
    title: str
    owner: str
    priority: str = "Normal"
    metadata: dict = {}


@router.post("/invoices", response_model=BillingResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: BillingCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = BillingRecord(**payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/invoices", response_model=list[BillingResponse])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(BillingRecord).order_by(BillingRecord.created_at.desc()).all()


@router.post("/office-ally/submit")
def submit_claims(_user=Depends(require_roles(UserRole.admin))):
    if not settings.OFFICEALLY_FTP_HOST:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Office Ally FTP not configured",
        )
    return {"status": "queued", "provider": "Office Ally"}


@router.post("/business-ops/tasks", status_code=status.HTTP_201_CREATED)
def create_business_task(
    payload: BusinessOpsCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    task = BusinessOpsTask(
        **payload.dict(exclude={"metadata"}), task_metadata=payload.metadata
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
