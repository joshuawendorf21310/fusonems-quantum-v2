from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles, require_mfa
from models.legal_portal import LegalCase, LegalEvidence
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/legal-portal", tags=["Legal Portal"], dependencies=[Depends(require_mfa)])


class LegalCaseCreate(BaseModel):
    case_number: str
    status: str = "open"
    summary: str = ""
    payload: dict = {}


class LegalEvidenceCreate(BaseModel):
    case_id: int
    evidence_type: str = "document"
    status: str = "collected"
    payload: dict = {}


@router.get("/cases")
def list_cases(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    cases = (
        scoped_query(db, LegalCase, user.org_id, request.state.training_mode)
        .order_by(LegalCase.created_at.desc())
        .all()
    )
    return [model_snapshot(case) for case in cases]


@router.post("/cases", status_code=status.HTTP_201_CREATED)
def create_case(
    payload: LegalCaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    record = LegalCase(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="legal_case",
        classification="LEGAL_HOLD",
        after_state=model_snapshot(record),
        event_type="legal_portal.case.created",
        event_payload={"case_id": record.id},
    )
    return model_snapshot(record)


@router.get("/evidence")
def list_evidence(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    evidence = (
        scoped_query(db, LegalEvidence, user.org_id, request.state.training_mode)
        .order_by(LegalEvidence.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in evidence]


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
def create_evidence(
    payload: LegalEvidenceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    case = (
        scoped_query(db, LegalCase, user.org_id, request.state.training_mode)
        .filter(LegalCase.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Case not found")
    record = LegalEvidence(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="legal_evidence",
        classification="LEGAL_HOLD",
        after_state=model_snapshot(record),
        event_type="legal_portal.evidence.created",
        event_payload={"evidence_id": record.id, "case_id": case.id},
    )
    return model_snapshot(record)
