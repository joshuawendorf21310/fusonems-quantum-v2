from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.compliance import AccessAudit, ComplianceAlert, ForensicAuditLog
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/compliance",
    tags=["Compliance"],
    dependencies=[Depends(require_module("COMPLIANCE"))],
)


class AlertCreate(BaseModel):
    category: str
    severity: str = "Medium"
    message: str


class AuditCreate(BaseModel):
    user_email: str
    action: str
    resource: str
    outcome: str = "Allowed"


class ForensicCreate(BaseModel):
    action: str
    resource: str
    reason_code: str = ""
    device_fingerprint: str = ""
    ip_address: str = ""
    session_id: str = ""
    before_state: dict | None = None
    after_state: dict | None = None
    outcome: str = "Allowed"


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    alert = ComplianceAlert(**payload.dict(), org_id=user.org_id)
    apply_training_mode(alert, request)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="compliance_alert",
        classification=alert.classification,
        after_state=model_snapshot(alert),
        event_type="compliance.alert.created",
        event_payload={"alert_id": alert.id},
    )
    return alert


@router.get("/alerts")
def list_alerts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, ComplianceAlert, user.org_id, request.state.training_mode).order_by(
        ComplianceAlert.created_at.desc()
    ).all()


@router.post("/audits", status_code=status.HTTP_201_CREATED)
def log_audit(
    payload: AuditCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    audit = AccessAudit(**payload.dict(), org_id=user.org_id)
    apply_training_mode(audit, request)
    db.add(audit)
    db.commit()
    db.refresh(audit)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="access_audit",
        classification=audit.classification,
        after_state=model_snapshot(audit),
        event_type="compliance.audit.created",
        event_payload={"audit_id": audit.id},
    )
    return audit


@router.get("/audits")
def list_audits(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, AccessAudit, user.org_id, request.state.training_mode).order_by(
        AccessAudit.created_at.desc()
    ).all()


@router.post("/forensic", status_code=status.HTTP_201_CREATED)
def create_forensic(
    payload: ForensicCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    record = ForensicAuditLog(
        org_id=user.org_id,
        actor_email=user.email,
        actor_role=user.role,
        action=payload.action,
        resource=payload.resource,
        reason_code=payload.reason_code,
        device_fingerprint=payload.device_fingerprint,
        ip_address=payload.ip_address,
        session_id=payload.session_id,
        before_state=payload.before_state,
        after_state=payload.after_state,
        outcome=payload.outcome,
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
        resource="forensic_audit",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="compliance.forensic.created",
        event_payload={"forensic_id": record.id},
    )
    return record


@router.get("/forensic")
def list_forensic(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, ForensicAuditLog, user.org_id, request.state.training_mode).order_by(
        ForensicAuditLog.created_at.desc()
    ).all()
