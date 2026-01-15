from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.founder import FounderMetric
from models.user import UserRole


router = APIRouter(prefix="/api/founder", tags=["Founder"])


class MetricCreate(BaseModel):
    category: str
    value: str
    details: dict = {}


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    metric = FounderMetric(**payload.dict())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/metrics")
def list_metrics(db: Session = Depends(get_db)):
    return db.query(FounderMetric).order_by(FounderMetric.created_at.desc()).all()
