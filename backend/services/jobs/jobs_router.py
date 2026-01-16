from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.jobs import JobQueue, JobRun
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_module("JOBS"))],
)


class JobCreate(BaseModel):
    job_type: str
    payload: dict = {}
    scheduled_for: Optional[datetime] = None


class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    attempts: int
    scheduled_for: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[JobResponse])
def list_jobs(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    jobs = scoped_query(db, JobQueue, user.org_id, request.state.training_mode).order_by(
        JobQueue.created_at.desc()
    )
    return [
        JobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            attempts=job.attempts,
            scheduled_for=job.scheduled_for.isoformat() if job.scheduled_for else None,
            created_at=job.created_at.isoformat() if job.created_at else None,
        )
        for job in jobs
    ]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    job = JobQueue(
        org_id=user.org_id,
        job_type=payload.job_type,
        payload=payload.payload,
        scheduled_for=payload.scheduled_for,
    )
    apply_training_mode(job, request)
    db.add(job)
    db.commit()
    db.refresh(job)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="job_queue",
        classification="OPS",
        after_state=model_snapshot(job),
        event_type="jobs.job.created",
        event_payload={"job_id": job.id},
    )
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        attempts=job.attempts,
        scheduled_for=job.scheduled_for.isoformat() if job.scheduled_for else None,
        created_at=job.created_at.isoformat() if job.created_at else None,
    )


@router.post("/{job_id}/run", response_model=JobRunResponse)
def run_job(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    job = get_scoped_record(db, request, JobQueue, job_id, user, resource_label="job_queue")
    before = model_snapshot(job)
    job.status = "running"
    job.started_at = datetime.utcnow()
    job.attempts += 1
    run = JobRun(org_id=user.org_id, job_id=job.id, status="running")
    apply_training_mode(run, request)
    db.add(run)
    db.commit()
    db.refresh(run)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="run",
        resource="job_queue",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(job),
        event_type="jobs.job.run_started",
        event_payload={"job_id": job.id, "run_id": run.id},
    )
    return JobRunResponse(
        id=run.id,
        job_id=run.job_id,
        status=run.status,
        started_at=run.started_at.isoformat() if run.started_at else None,
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
    )
