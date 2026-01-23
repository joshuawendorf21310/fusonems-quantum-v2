from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.qa import QACase, QARemediation, QARubric, QAReview
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/qa",
    tags=["QA Review"],
    dependencies=[Depends(require_module("QA"))],
)


class RubricCreate(BaseModel):
    name: str
    version: str = "v1"
    status: str = "active"
    criteria: list[dict] = []


class CaseCreate(BaseModel):
    case_type: str = "clinical"
    priority: str = "Normal"
    status: str = "queued"
    trigger: str = "manual"
    linked_run_id: str = ""
    linked_patient_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_at: Optional[datetime] = None


class ReviewCreate(BaseModel):
    case_id: int
    rubric_id: Optional[int] = None
    scores: dict = {}
    summary: str = ""
    determination: str = "pending"
    remediation_required: bool = False


class RemediationCreate(BaseModel):
    case_id: int
    plan: str
    status: str = "open"
    assigned_to: Optional[int] = None
    due_at: Optional[datetime] = None


@router.get("/rubrics")
def list_rubrics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    return scoped_query(db, QARubric, user.org_id, request.state.training_mode).order_by(
        QARubric.created_at.desc()
    )


@router.post("/rubrics", status_code=status.HTTP_201_CREATED)
def create_rubric(
    payload: RubricCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    rubric = QARubric(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(rubric, request)
    db.add(rubric)
    db.commit()
    db.refresh(rubric)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="qa_rubric",
        classification="NON_PHI",
        after_state=model_snapshot(rubric),
        event_type="qa.rubric.created",
        event_payload={"rubric_id": rubric.id},
    )
    return model_snapshot(rubric)


@router.get("/cases")
def list_cases(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    return scoped_query(db, QACase, user.org_id, request.state.training_mode).order_by(
        QACase.created_at.desc()
    )


@router.post("/cases", status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    case = QACase(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(case, request)
    db.add(case)
    db.commit()
    db.refresh(case)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="qa_case",
        classification="PHI",
        after_state=model_snapshot(case),
        event_type="qa.case.created",
        event_payload={"case_id": case.id},
    )
    return model_snapshot(case)


@router.post("/reviews", status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    case = (
        scoped_query(db, QACase, user.org_id, request.state.training_mode)
        .filter(QACase.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Case not found")
    rubric = None
    if payload.rubric_id is not None:
        rubric = (
            scoped_query(db, QARubric, user.org_id, request.state.training_mode)
            .filter(QARubric.id == payload.rubric_id)
            .first()
        )
        if not rubric:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rubric not found")
    review = QAReview(
        org_id=user.org_id,
        reviewer_id=user.id,
        **payload.model_dump(),
    )
    apply_training_mode(review, request)
    db.add(review)
    db.commit()
    db.refresh(review)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="qa_review",
        classification="PHI",
        after_state=model_snapshot(review),
        event_type="qa.review.created",
        event_payload={"review_id": review.id, "case_id": case.id, "rubric_id": rubric.id if rubric else None},
    )
    return model_snapshot(review)


@router.post("/remediations", status_code=status.HTTP_201_CREATED)
def create_remediation(
    payload: RemediationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director)),
):
    case = (
        scoped_query(db, QACase, user.org_id, request.state.training_mode)
        .filter(QACase.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Case not found")
    remediation = QARemediation(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(remediation, request)
    db.add(remediation)
    db.commit()
    db.refresh(remediation)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="qa_remediation",
        classification="PHI",
        after_state=model_snapshot(remediation),
        event_type="qa.remediation.created",
        event_payload={"remediation_id": remediation.id, "case_id": case.id},
    )
    return model_snapshot(remediation)
