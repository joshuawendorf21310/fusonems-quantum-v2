from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.user import UserRole
from models.validation import DataValidationIssue

router = APIRouter(prefix="/api/validation", tags=["Validation"])


class ValidationScan(BaseModel):
    entity_type: str
    entity_id: str
    patient_name: str | None = None
    date_of_birth: str | None = None
    insurance_id: str | None = None
    encounter_code: str | None = None
    claim_amount: float | None = None


@router.post("/scan", status_code=status.HTTP_201_CREATED)
def scan_payload(
    payload: ValidationScan,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    issues = []
    if not payload.patient_name:
        issues.append("Missing patient name")
    if not payload.date_of_birth:
        issues.append("Missing date of birth")
    if not payload.insurance_id:
        issues.append("Missing insurance ID")
    if not payload.encounter_code:
        issues.append("Missing encounter code")
    if payload.claim_amount is not None and payload.claim_amount <= 0:
        issues.append("Claim amount must be greater than zero")

    stored = []
    for issue in issues:
        record = DataValidationIssue(
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            severity="High" if "Missing" in issue else "Medium",
            issue=issue,
        )
        db.add(record)
        stored.append(record)

    db.commit()
    return {"issues": issues, "count": len(issues)}


@router.get("/issues")
def list_issues(db: Session = Depends(get_db)):
    return db.query(DataValidationIssue).order_by(DataValidationIssue.created_at.desc()).all()
