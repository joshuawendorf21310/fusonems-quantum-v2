"""
Training Routes
FastAPI router with endpoints for training management, course catalog,
session scheduling, enrollment, requirements, FTO evaluations, and CEU tracking.
"""
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module, require_user
from core.security import require_roles
from models.training_management import (
    TrainingCourse,
    TrainingSession,
    TrainingEnrollment,
    TrainingRequirement,
    TrainingCompetency,
    FieldTrainingOfficerRecord,
    ContinuingEducationCredit,
    CourseStatus,
    TrainingStatus,
    EducationFollowUp,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query, get_scoped_record
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

from .course_service import CourseService


router = APIRouter(
    prefix="/api/training",
    tags=["Training Management"],
    dependencies=[Depends(require_module("TRAINING"))],
)


# ============================================================================
# Pydantic Models
# ============================================================================


class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    course_description: Optional[str] = None
    course_category: str
    duration_hours: float
    max_students: Optional[int] = None
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    ceu_credits: float = 0.0
    cme_credits: float = 0.0
    grants_certification: bool = False
    certification_name: Optional[str] = None
    certification_valid_months: Optional[int] = None
    course_materials_path: Optional[str] = None
    online_available: bool = False
    hands_on_required: bool = False
    mandatory: bool = False
    recurrence_months: Optional[int] = None


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_description: Optional[str] = None
    course_category: Optional[str] = None
    duration_hours: Optional[float] = None
    max_students: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    ceu_credits: Optional[float] = None
    cme_credits: Optional[float] = None
    grants_certification: Optional[bool] = None
    certification_name: Optional[str] = None
    certification_valid_months: Optional[int] = None
    mandatory: Optional[bool] = None
    recurrence_months: Optional[int] = None
    active: Optional[bool] = None


class CourseResponse(BaseModel):
    id: int
    course_code: str
    course_name: str
    course_description: Optional[str]
    course_category: str
    duration_hours: float
    max_students: Optional[int]
    prerequisites: Optional[List[str]]
    ceu_credits: float
    grants_certification: bool
    certification_name: Optional[str]
    mandatory: bool
    recurrence_months: Optional[int]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    course_id: int
    session_date: date
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    room: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    max_students: Optional[int] = None
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    course_id: int
    session_date: date
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    instructor_name: Optional[str]
    max_students: Optional[int]
    students_enrolled: int
    students_completed: int
    status: CourseStatus
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    id: int
    session_id: int
    personnel_id: int
    enrollment_date: datetime
    status: TrainingStatus
    attendance_confirmed: bool
    completion_date: Optional[date]
    final_score: Optional[float]
    passed: bool

    class Config:
        from_attributes = True


class RequirementResponse(BaseModel):
    id: int
    personnel_id: int
    course_id: int
    required_by_date: date
    status: TrainingStatus
    completed_date: Optional[date]
    next_due_date: Optional[date]

    class Config:
        from_attributes = True


class FTOEvaluationCreate(BaseModel):
    trainee_id: int
    fto_id: int
    program_start_date: date
    phase: Optional[str] = None
    shift_number: Optional[int] = None
    skills_checklist: Optional[Dict[str, Any]] = Field(default_factory=dict)
    daily_evaluation_score: Optional[float] = None
    communication_score: Optional[float] = None
    patient_care_score: Optional[float] = None
    driving_score: Optional[float] = None
    professionalism_score: Optional[float] = None
    fto_comments: Optional[str] = None
    trainee_self_assessment: Optional[str] = None
    passed_shift: bool = False


class FTOEvaluationResponse(BaseModel):
    id: int
    trainee_id: int
    fto_id: int
    program_start_date: date
    phase: Optional[str]
    shift_number: Optional[int]
    daily_evaluation_score: Optional[float]
    passed_shift: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CompetencyResponse(BaseModel):
    id: int
    personnel_id: int
    competency_name: str
    competency_category: str
    required_proficiency_level: Optional[str]
    current_proficiency_level: Optional[str]
    last_evaluated_date: Optional[date]
    next_evaluation_due: Optional[date]
    passed_last_evaluation: bool

    class Config:
        from_attributes = True


class CEUCreditCreate(BaseModel):
    personnel_id: int
    credit_type: str
    course_name: str
    provider: Optional[str] = None
    credit_hours: float
    completion_date: date
    certificate_number: Optional[str] = None
    certificate_path: Optional[str] = None
    reporting_period: Optional[str] = None


class CEUCreditResponse(BaseModel):
    id: int
    personnel_id: int
    credit_type: str
    course_name: str
    provider: Optional[str]
    credit_hours: float
    completion_date: date
    certificate_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentComplete(BaseModel):
    final_score: float
    passed: bool
    completion_date: Optional[date] = None


class TrainingSummaryResponse(BaseModel):
    requirements: List[RequirementResponse]
    enrollments: List[EnrollmentResponse]
    competencies: List[CompetencyResponse]
    fto_records: List[FTOEvaluationResponse]
    ceu_credits: List[CEUCreditResponse]


class CertificationExpirationResponse(BaseModel):
    expiring_90_days: int
    expiring_60_days: int
    expiring_30_days: int
    expired: int
    total_tracked: int


class CompetencyUpdate(BaseModel):
    current_proficiency_level: Optional[str] = None
    last_evaluated_date: Optional[date] = None
    evaluator_id: Optional[int] = None
    next_evaluation_due: Optional[date] = None
    passed_last_evaluation: Optional[bool] = None
    notes: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/courses", response_model=List[CourseResponse])
def get_courses(
    category: Optional[str] = Query(None, description="Filter by category"),
    mandatory_only: bool = Query(False, description="Show only mandatory courses"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Get course catalog with search and filtering.
    Categories: Clinical, Operations, Leadership, Compliance, Safety
    """
    courses = CourseService.get_courses(
        db=db,
        org_id=user.org_id,
        category=category,
        mandatory_only=mandatory_only,
        search=search,
    )
    return courses


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Create new training course (Admin/Supervisor only)"""
    course = CourseService.create_course(
        db=db,
        org_id=user.org_id,
        course_data=course_data.model_dump(exclude_unset=True),
    )

    apply_training_mode(course, request)
    try:
        db.commit()
        db.refresh(course)

        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="training_course",
            classification="OPS",
            after_state=model_snapshot(course),
            event_type="training.course.created",
            event_payload={"course_id": course.id, "course_name": course.course_name},
        )
    except Exception as e:
        db.rollback()
        raise

    return course


@router.patch("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Update training course (Admin/Supervisor only)"""
    course = CourseService.get_course_by_id(db, user.org_id, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    before = model_snapshot(course)

    updated_course = CourseService.update_course(
        db=db,
        org_id=user.org_id,
        course_id=course_id,
        course_data=course_data.model_dump(exclude_unset=True),
    )

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="training_course",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(updated_course),
        event_type="training.course.updated",
        event_payload={"course_id": course_id},
    )

    return updated_course


@router.get("/sessions", response_model=List[SessionResponse])
def get_training_sessions(
    course_id: Optional[int] = Query(None, description="Filter by course"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Get training sessions calendar with filtering"""
    sessions = CourseService.get_sessions(
        db=db,
        org_id=user.org_id,
        course_id=course_id,
        start_date=start_date,
        end_date=end_date,
    )
    return sessions


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_training_session(
    session_data: SessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Create new training session (Admin/Supervisor only)"""
    session = CourseService.create_session(
        db=db,
        org_id=user.org_id,
        session_data=session_data.model_dump(exclude_unset=True),
    )

    apply_training_mode(session, request)
    try:
        db.commit()
        db.refresh(session)

        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="training_session",
            classification="OPS",
            after_state=model_snapshot(session),
            event_type="training.session.created",
            event_payload={"session_id": session.id, "course_id": session.course_id},
        )
    except Exception as e:
        db.rollback()
        raise

    return session


@router.post("/sessions/{session_id}/enroll", response_model=EnrollmentResponse)
def enroll_in_session(
    session_id: int,
    personnel_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Enroll personnel in training session"""
    enrollment = CourseService.enroll_in_session(
        db=db,
        org_id=user.org_id,
        session_id=session_id,
        personnel_id=personnel_id,
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to enroll - session may be full or not found",
        )

    apply_training_mode(enrollment, request)
    try:
        db.commit()
        db.refresh(enrollment)

        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="training_enrollment",
            classification="OPS",
            after_state=model_snapshot(enrollment),
            event_type="training.enrollment.created",
            event_payload={
                "session_id": session_id,
                "personnel_id": personnel_id,
                "enrollment_id": enrollment.id,
            },
        )
    except Exception as e:
        db.rollback()
        raise

    return enrollment


@router.post("/enrollments/{enrollment_id}/complete", response_model=EnrollmentResponse)
def complete_enrollment(
    enrollment_id: int,
    completion_data: EnrollmentComplete,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Mark enrollment as completed with final score (Admin/Supervisor only)"""
    before_enrollment = (
        scoped_query(db, TrainingEnrollment, user.org_id)
        .filter(TrainingEnrollment.id == enrollment_id)
        .first()
    )

    if not before_enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    before = model_snapshot(before_enrollment)

    enrollment = CourseService.complete_enrollment(
        db=db,
        org_id=user.org_id,
        enrollment_id=enrollment_id,
        final_score=completion_data.final_score,
        passed=completion_data.passed,
        completion_date=completion_data.completion_date,
    )

    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="training_enrollment",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(enrollment),
        event_type="training.enrollment.completed",
        event_payload={
            "enrollment_id": enrollment_id,
            "passed": completion_data.passed,
            "final_score": completion_data.final_score,
        },
    )

    return enrollment


@router.get("/my-training", response_model=TrainingSummaryResponse)
def get_my_training(
    personnel_id: Optional[int] = Query(None, description="Personnel ID (defaults to current user)"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Get employee's training requirements and completions.
    If personnel_id not provided, uses current user's linked personnel record.
    """
    # If no personnel_id provided, could look up user.personnel_id if that relationship exists
    # For now, require explicit personnel_id
    if not personnel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="personnel_id required",
        )

    training_data = CourseService.get_personnel_training(
        db=db,
        org_id=user.org_id,
        personnel_id=personnel_id,
    )

    return {
        "requirements": training_data["requirements"],
        "enrollments": training_data["enrollments"],
        "competencies": training_data["competencies"],
        "fto_records": training_data["fto_records"],
        "ceu_credits": training_data["ceu_credits"],
    }


@router.get("/requirements/overdue", response_model=List[RequirementResponse])
def get_overdue_requirements(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Get all overdue training requirements (Admin/Supervisor only)"""
    overdue = CourseService.get_overdue_requirements(db=db, org_id=user.org_id)
    return overdue


@router.post("/fto/evaluation", response_model=FTOEvaluationResponse, status_code=status.HTTP_201_CREATED)
def submit_fto_evaluation(
    evaluation_data: FTOEvaluationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Submit FTO daily evaluation"""
    evaluation = CourseService.submit_fto_evaluation(
        db=db,
        org_id=user.org_id,
        evaluation_data=evaluation_data.model_dump(exclude_unset=True),
    )

    apply_training_mode(evaluation, request)
    try:
        db.commit()
        db.refresh(evaluation)

        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="fto_evaluation",
            classification="OPS",
            after_state=model_snapshot(evaluation),
            event_type="training.fto.evaluation.submitted",
            event_payload={
                "evaluation_id": evaluation.id,
                "trainee_id": evaluation.trainee_id,
                "fto_id": evaluation.fto_id,
                "passed_shift": evaluation.passed_shift,
            },
        )
    except Exception as e:
        db.rollback()
        raise

    return evaluation


@router.get("/competencies/{personnel_id}", response_model=List[CompetencyResponse])
def get_competency_matrix(
    personnel_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Get skills competency matrix for personnel"""
    competencies = CourseService.get_competency_matrix(
        db=db,
        org_id=user.org_id,
        personnel_id=personnel_id,
    )
    return competencies


@router.patch("/competencies/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    competency_id: int,
    competency_data: CompetencyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Update competency evaluation (Admin/Supervisor only)"""
    competency = (
        scoped_query(db, TrainingCompetency, user.org_id)
        .filter(TrainingCompetency.id == competency_id)
        .first()
    )

    if not competency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")

    before = model_snapshot(competency)

    updated_competency = CourseService.update_competency(
        db=db,
        org_id=user.org_id,
        competency_id=competency_id,
        evaluation_data=competency_data.model_dump(exclude_unset=True),
    )

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="training_competency",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(updated_competency),
        event_type="training.competency.updated",
        event_payload={"competency_id": competency_id},
    )

    return updated_competency


@router.post("/ceu-credits", response_model=CEUCreditResponse, status_code=status.HTTP_201_CREATED)
def submit_ceu_credit(
    ceu_data: CEUCreditCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Submit external CEU credit"""
    ceu = CourseService.submit_external_ceu(
        db=db,
        org_id=user.org_id,
        ceu_data=ceu_data.model_dump(exclude_unset=True),
    )

    apply_training_mode(ceu, request)
    try:
        db.commit()
        db.refresh(ceu)

        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="ceu_credit",
            classification="OPS",
            after_state=model_snapshot(ceu),
            event_type="training.ceu.submitted",
            event_payload={
                "ceu_id": ceu.id,
                "personnel_id": ceu.personnel_id,
                "credit_hours": ceu.credit_hours,
                "credit_type": ceu.credit_type,
            },
        )
    except Exception as e:
        db.rollback()
        raise

    return ceu


@router.post("/certifications/track-expirations", response_model=CertificationExpirationResponse)
def track_certification_expirations(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """
    Run automatic certification expiration tracking.
    Returns certifications expiring in 90, 60, and 30 days.
    Updates reminder flags and marks expired certifications.
    (Admin/Supervisor only)
    """
    result = CourseService.track_certification_expirations(db=db, org_id=user.org_id)

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="execute",
        resource="certification_tracking",
        classification="OPS",
        after_state=result,
        event_type="training.certifications.tracked",
        event_payload={
            "expired_count": result["expired"],
            "expiring_30_count": len(result["expiring_30_days"]),
            "total_tracked": result["total_tracked"],
        },
    )

    return {
        "expiring_90_days": len(result["expiring_90_days"]),
        "expiring_60_days": len(result["expiring_60_days"]),
        "expiring_30_days": len(result["expiring_30_days"]),
        "expired": len(result["expired"]),
        "total_tracked": result["total_tracked"],
    }


@router.post("/requirements/generate-recurring", response_model=List[RequirementResponse])
def generate_recurring_requirements(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """
    Generate training requirements for mandatory recurring courses.
    Checks completed requirements and creates new ones based on recurrence schedule.
    (Admin/Supervisor only)
    """
    requirements = CourseService.generate_recurring_requirements(db=db, org_id=user.org_id)

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="execute",
        resource="requirement_generation",
        classification="OPS",
        after_state={"generated_count": len(requirements)},
        event_type="training.requirements.generated",
        event_payload={"requirements_created": len(requirements)},
    )

    return requirements


@router.get("/education-follow-ups", response_model=List[Dict[str, Any]])
def get_education_follow_ups(
    personnel_id: Optional[int] = Query(None, description="Filter by personnel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.supervisor)),
):
    """Get education follow-ups from QA cases (Admin/Supervisor only)"""
    follow_ups = CourseService.get_education_follow_ups(
        db=db,
        org_id=user.org_id,
        personnel_id=personnel_id,
        status=status,
    )

    # Convert to dict for response
    return [model_snapshot(fu) for fu in follow_ups]
