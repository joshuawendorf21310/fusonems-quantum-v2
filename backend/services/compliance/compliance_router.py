from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.compliance import AccessAudit, ComplianceAlert
from models.user import UserRole

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


class AlertCreate(BaseModel):
    category: str
    severity: str = "Medium"
    message: str


class AuditCreate(BaseModel):
    user_email: str
    action: str
    resource: str
    outcome: str = "Allowed"


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    alert = ComplianceAlert(**payload.dict())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    return db.query(ComplianceAlert).order_by(ComplianceAlert.created_at.desc()).all()


@router.post("/audits", status_code=status.HTTP_201_CREATED)
def log_audit(
    payload: AuditCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    audit = AccessAudit(**payload.dict())
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


@router.get("/audits")
def list_audits(db: Session = Depends(get_db)):
    return db.query(AccessAudit).order_by(AccessAudit.created_at.desc()).all()
