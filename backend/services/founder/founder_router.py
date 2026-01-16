from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.founder import FounderMetric
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(
    prefix="/api/founder",
    tags=["Founder"],
    dependencies=[Depends(require_module("FOUNDER"))],
)


class MetricCreate(BaseModel):
    category: str
    value: str
    details: dict = {}


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    metric = FounderMetric(**payload.dict(), org_id=user.org_id)
    apply_training_mode(metric, request)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="founder_metric",
        classification=metric.classification,
        after_state=model_snapshot(metric),
        event_type="founder.metric.created",
        event_payload={"metric_id": metric.id},
    )
    return metric


@router.get("/metrics")
def list_metrics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, FounderMetric, user.org_id, request.state.training_mode).order_by(
        FounderMetric.created_at.desc()
    ).all()
