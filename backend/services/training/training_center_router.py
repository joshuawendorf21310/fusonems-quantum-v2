from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.training_center import (
    CERecord,
    CredentialRecord,
    SkillCheckoff,
    TrainingCourse,
    TrainingEnrollment,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/training-center",
    tags=["Training Center"],
    dependencies=[Depends(require_module("TRAINING"))],
)


class CourseCreate(BaseModel):
    title: str
    category: str = "clinical"
    status: str = "active"
    version: str = "v1"
    prerequisites: list[str] = []
    credit_hours: int = 0


class EnrollmentCreate(BaseModel):
    course_id: int
    user_id: int
    status: str = "assigned"
    score: int = 0
    completed_at: Optional[datetime] = None


class CredentialCreate(BaseModel):
    user_id: int
    credential_type: str
    issuer: str = ""
    license_number: str = ""
    status: str = "active"
    expires_at: Optional[datetime] = None


class SkillCreate(BaseModel):
    user_id: int
    skill_name: str
    evaluator: str = ""
    status: str = "pending"
    score: int = 0
    expires_at: Optional[datetime] = None


class CECreate(BaseModel):
    user_id: int
    category: str = "state"
    hours: int = 0
    status: str = "pending"
    cycle: str = "2024"


@router.get("/courses")
def list_courses(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    courses = (
        scoped_query(db, TrainingCourse, user.org_id, request.state.training_mode)
        .order_by(TrainingCourse.created_at.desc())
        .all()
    )
    return [model_snapshot(course) for course in courses]


@router.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    course = TrainingCourse(org_id=user.org_id, **payload.dict())
    apply_training_mode(course, request)
    db.add(course)
    db.commit()
    db.refresh(course)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="training_course",
        classification="NON_PHI",
        after_state=model_snapshot(course),
        event_type="training.course.created",
        event_payload={"course_id": course.id},
    )
    return model_snapshot(course)


@router.get("/enrollments")
def list_enrollments(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    enrollments = (
        scoped_query(db, TrainingEnrollment, user.org_id, request.state.training_mode)
        .order_by(TrainingEnrollment.created_at.desc())
        .all()
    )
    return [model_snapshot(enrollment) for enrollment in enrollments]


@router.post("/enrollments", status_code=status.HTTP_201_CREATED)
def create_enrollment(
    payload: EnrollmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    course = (
        scoped_query(db, TrainingCourse, user.org_id, request.state.training_mode)
        .filter(TrainingCourse.id == payload.course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course not found")
    enrollee = (
        scoped_query(db, User, user.org_id, request.state.training_mode)
        .filter(User.id == payload.user_id)
        .first()
    )
    if not enrollee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    enrollment = TrainingEnrollment(org_id=user.org_id, **payload.dict())
    apply_training_mode(enrollment, request)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="training_enrollment",
        classification="NON_PHI",
        after_state=model_snapshot(enrollment),
        event_type="training.enrollment.created",
        event_payload={"enrollment_id": enrollment.id, "course_id": course.id, "user_id": enrollee.id},
    )
    return model_snapshot(enrollment)


@router.get("/credentials")
def list_credentials(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    records = (
        scoped_query(db, CredentialRecord, user.org_id, request.state.training_mode)
        .order_by(CredentialRecord.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
def create_credential(
    payload: CredentialCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    credential_user = (
        scoped_query(db, User, user.org_id, request.state.training_mode)
        .filter(User.id == payload.user_id)
        .first()
    )
    if not credential_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    record = CredentialRecord(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="credential_record",
        classification="NON_PHI",
        after_state=model_snapshot(record),
        event_type="training.credential.created",
        event_payload={"credential_id": record.id, "user_id": credential_user.id},
    )
    return model_snapshot(record)


@router.get("/skills")
def list_skills(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    skills = (
        scoped_query(db, SkillCheckoff, user.org_id, request.state.training_mode)
        .order_by(SkillCheckoff.created_at.desc())
        .all()
    )
    return [model_snapshot(skill) for skill in skills]


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    skill_user = (
        scoped_query(db, User, user.org_id, request.state.training_mode)
        .filter(User.id == payload.user_id)
        .first()
    )
    if not skill_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    skill = SkillCheckoff(org_id=user.org_id, **payload.dict())
    apply_training_mode(skill, request)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="skill_checkoff",
        classification="NON_PHI",
        after_state=model_snapshot(skill),
        event_type="training.skill.created",
        event_payload={"skill_id": skill.id, "user_id": skill_user.id},
    )
    return model_snapshot(skill)


@router.get("/ce")
def list_ce(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    records = (
        scoped_query(db, CERecord, user.org_id, request.state.training_mode)
        .order_by(CERecord.created_at.desc())
        .all()
    )
    return [model_snapshot(record) for record in records]


@router.post("/ce", status_code=status.HTTP_201_CREATED)
def create_ce(
    payload: CECreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    ce_user = (
        scoped_query(db, User, user.org_id, request.state.training_mode)
        .filter(User.id == payload.user_id)
        .first()
    )
    if not ce_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    record = CERecord(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="ce_record",
        classification="NON_PHI",
        after_state=model_snapshot(record),
        event_type="training.ce.created",
        event_payload={"ce_id": record.id, "user_id": ce_user.id},
    )
    return model_snapshot(record)
