from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.automation import WorkflowRule, WorkflowTask
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/automation",
    tags=["Automation"],
    dependencies=[Depends(require_module("AUTOMATION"))],
)


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
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    rule = WorkflowRule(**payload.dict(), org_id=user.org_id)
    apply_training_mode(rule, request)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="automation_rule",
        classification=rule.classification,
        after_state=model_snapshot(rule),
        event_type="automation.rule.created",
        event_payload={"rule_id": rule.id},
    )
    return rule


@router.get("/rules")
def list_rules(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, WorkflowRule, user.org_id, request.state.training_mode).order_by(
        WorkflowRule.created_at.desc()
    ).all()


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    task = WorkflowTask(**payload.dict(), org_id=user.org_id)
    apply_training_mode(task, request)
    db.add(task)
    db.commit()
    db.refresh(task)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="automation_task",
        classification=task.classification,
        after_state=model_snapshot(task),
        event_type="automation.task.created",
        event_payload={"task_id": task.id},
    )
    return task


@router.get("/tasks")
def list_tasks(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, WorkflowTask, user.org_id, request.state.training_mode).order_by(
        WorkflowTask.created_at.desc()
    ).all()


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
