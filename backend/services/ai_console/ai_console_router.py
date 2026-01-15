from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.ai_console import AiInsight
from models.user import UserRole


router = APIRouter(prefix="/api/ai_console", tags=["AI Console"])


class InsightCreate(BaseModel):
    category: str
    prompt: str
    response: str | None = None
    metrics: dict = {}


@router.post("/insights", status_code=status.HTTP_201_CREATED)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    insight = AiInsight(**payload.dict())
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/insights")
def list_insights(db: Session = Depends(get_db)):
    return db.query(AiInsight).order_by(AiInsight.created_at.desc()).all()


@router.get("/predictions")
def get_predictions():
    return {
        "call_volume_next_8h": [6, 5, 9, 12, 8, 4, 6, 5],
        "peak_window": "17:00-20:00",
        "recommendation": "Stage an additional ALS unit near Zone 4",
    }
