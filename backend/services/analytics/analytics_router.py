from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.analytics import AnalyticsMetric, UsageEvent
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_module("ANALYTICS"))],
)


class MetricCreate(BaseModel):
    metric_key: str
    metric_value: str
    window: str = "24h"
    tags: dict = {}


class MetricResponse(MetricCreate):
    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UsageCreate(BaseModel):
    event_key: str
    module_key: str
    payload: dict = {}
    classification: str = "OPS"


class UsageResponse(BaseModel):
    id: int
    event_key: str
    module_key: str
    classification: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/metrics", response_model=list[MetricResponse])
def list_metrics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    metrics = scoped_query(db, AnalyticsMetric, user.org_id, request.state.training_mode).order_by(
        AnalyticsMetric.created_at.desc()
    )
    return [
        MetricResponse(
            id=metric.id,
            metric_key=metric.metric_key,
            metric_value=metric.metric_value,
            window=metric.window,
            tags=metric.tags,
            created_at=metric.created_at.isoformat() if metric.created_at else None,
        )
        for metric in metrics
    ]


@router.post("/metrics", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    metric = AnalyticsMetric(org_id=user.org_id, **payload.dict())
    apply_training_mode(metric, request)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="analytics_metric",
        classification="OPS",
        after_state=model_snapshot(metric),
        event_type="analytics.metric.created",
        event_payload={"metric_id": metric.id},
    )
    return MetricResponse(
        id=metric.id,
        metric_key=metric.metric_key,
        metric_value=metric.metric_value,
        window=metric.window,
        tags=metric.tags,
        created_at=metric.created_at.isoformat() if metric.created_at else None,
    )


@router.get("/usage", response_model=list[UsageResponse])
def list_usage(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    records = scoped_query(db, UsageEvent, user.org_id, request.state.training_mode).order_by(
        UsageEvent.created_at.desc()
    )
    return [
        UsageResponse(
            id=record.id,
            event_key=record.event_key,
            module_key=record.module_key,
            classification=record.classification,
            created_at=record.created_at.isoformat() if record.created_at else None,
        )
        for record in records
    ]


@router.post("/usage", response_model=UsageResponse, status_code=status.HTTP_201_CREATED)
def create_usage(
    payload: UsageCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    record = UsageEvent(
        org_id=user.org_id,
        event_key=payload.event_key,
        module_key=payload.module_key,
        payload=payload.payload,
        classification=payload.classification,
        actor_id=user.id,
    )
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="usage_event",
        classification=payload.classification,
        after_state=model_snapshot(record),
        event_type="analytics.usage.created",
        event_payload={"usage_id": record.id},
    )
    return UsageResponse(
        id=record.id,
        event_key=record.event_key,
        module_key=record.module_key,
        classification=record.classification,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )
