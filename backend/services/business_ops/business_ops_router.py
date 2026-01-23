from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.business_ops import BusinessOpsTask
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(
    prefix="/api/business-ops",
    tags=["BusinessOps"],
    dependencies=[Depends(require_module("BUSINESS_OPS"))],
)


class TaskCreate(BaseModel):
    title: str
    owner: str
    priority: str = "Normal"
    metadata: dict = {}


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    task = BusinessOpsTask(
        **payload.model_dump(exclude={"metadata"}),
        task_metadata=payload.metadata,
        org_id=user.org_id,
    )
    apply_training_mode(task, request)
    db.add(task)
    db.commit()
    db.refresh(task)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="business_ops_task",
        classification=task.classification,
        after_state=model_snapshot(task),
        event_type="business_ops.task.created",
        event_payload={"task_id": task.id},
    )
    return task


@router.get("/tasks")
def list_tasks(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, BusinessOpsTask, user.org_id, request.state.training_mode).order_by(
        BusinessOpsTask.created_at.desc()
    ).all()
