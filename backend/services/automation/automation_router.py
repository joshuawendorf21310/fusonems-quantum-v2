from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.automation import WorkflowRule, WorkflowTask
from models.user import UserRole

router = APIRouter(prefix="/api/automation", tags=["Automation"])


class RuleCreate(BaseModel):
    name: str
    trigger: str
    action: str


class TaskCreate(BaseModel):
    title: str
    owner: str
    priority: str = "Normal"
    notes: str = ""


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    rule = WorkflowRule(**payload.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    return db.query(WorkflowRule).order_by(WorkflowRule.created_at.desc()).all()


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    task = WorkflowTask(**payload.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return db.query(WorkflowTask).order_by(WorkflowTask.created_at.desc()).all()


@router.post("/assignments")
def assign_tasks(payload: dict):
    staff = payload.get("staff", [])
    if not staff:
        return {"assignments": []}
    sorted_staff = sorted(staff, key=lambda item: item.get("open_tasks", 0))
    return {"assignments": sorted_staff}


@router.get("/reminders")
def list_reminders():
    return {
        "reminders": [
            {
                "message": "3 ePCRs missing signatures",
                "priority": "High",
            },
            {
                "message": "Billing follow-up required for claim INV-2219",
                "priority": "Medium",
            },
        ]
    }
