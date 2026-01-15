from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.investor_demo import InvestorMetric
from models.user import UserRole


router = APIRouter(prefix="/api/investor_demo", tags=["Investor Demo"])


class MetricCreate(BaseModel):
    name: str
    value: str
    context: dict = {}


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.investor)),
):
    metric = InvestorMetric(**payload.dict())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/metrics")
def list_metrics(db: Session = Depends(get_db)):
    return db.query(InvestorMetric).order_by(InvestorMetric.created_at.desc()).all()
