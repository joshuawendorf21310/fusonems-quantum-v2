from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.business_ops import BusinessOpsTask
from models.user import UserRole


router = APIRouter(prefix="/api/business-ops", tags=["BusinessOps"])


class TaskCreate(BaseModel):
    title: str
    owner: str
    priority: str = "Normal"
    metadata: dict = {}


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
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


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return db.query(BusinessOpsTask).order_by(BusinessOpsTask.created_at.desc()).all()
