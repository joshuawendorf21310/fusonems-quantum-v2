from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from core.upgrade import check_upgrade_readiness
from models.compliance import AccessAudit, ForensicAuditLog
from models.event import EventLog
from models.founder import FounderMetric
from models.jobs import JobQueue
from models.module_registry import ModuleRegistry
from models.organization import Organization
from models.user import User, UserRole
from services.email.email_transport_service import send_outbound
from services.mail.mail_router import MessageCreate, _send_telnyx_message
from services.storage.health_service import StorageHealthService
from utils.tenancy import get_scoped_record, scoped_query
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
    metric = FounderMetric(**payload.model_dump(), org_id=user.org_id)
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


def _queue_summary(db: Session, org_id: int) -> dict:
    base = db.query(JobQueue).filter(JobQueue.org_id == org_id)
    total = base.count()
    pending = base.filter(JobQueue.status == "queued").count()
    with_errors = base.filter(JobQueue.last_error != "").count()
    error_rate = round(with_errors / total, 3) if total else 0.0
    return {
        "total": total,
        "queued": pending,
        "errors": with_errors,
        "error_rate": error_rate,
    }


def _module_health(db: Session, org_id: int) -> tuple[list[dict], bool]:
    modules = scoped_query(db, ModuleRegistry, org_id, None).order_by(ModuleRegistry.module_key.asc()).all()
    rows: list[dict] = []
    active_degradation = False
    for module in modules:
        degraded = module.health_state != "HEALTHY" or not module.enabled or module.kill_switch
        if degraded:
            active_degradation = True
        rows.append(
            {
                "module_key": module.module_key,
                "health_state": module.health_state,
                "enabled": module.enabled,
                "kill_switch": module.kill_switch,
                "degraded": degraded,
            }
        )
    return rows, active_degradation


def _critical_audits(db: Session, org_id: int, limit: int = 50) -> list[dict]:
    filter_expr = or_(
        ForensicAuditLog.action.ilike("%auth%"),
        ForensicAuditLog.resource.ilike("%billing%"),
        ForensicAuditLog.resource.ilike("%merge%"),
        ForensicAuditLog.action.ilike("%merge%"),
        ForensicAuditLog.action.ilike("%lock%"),
        ForensicAuditLog.action.ilike("%export%"),
    )
    records = (
        db.query(ForensicAuditLog)
        .filter(ForensicAuditLog.org_id == org_id)
        .filter(filter_expr)
        .order_by(ForensicAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": record.id,
            "actor_email": record.actor_email,
            "actor_role": record.actor_role,
            "action": record.action,
            "resource": record.resource,
            "outcome": record.outcome,
            "reason_code": record.reason_code,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]


@router.get("/overview")
def founder_overview(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    orgs = scoped_query(db, Organization, user.org_id, None).all()
    modules, active_degradation = _module_health(db, user.org_id)
    queue = _queue_summary(db, user.org_id)
    audits = _critical_audits(db, user.org_id)
    response = {
        "orgs": [
            {"id": org.id, "name": org.name, "status": org.status, "lifecycle_state": org.lifecycle_state}
            for org in orgs
        ],
        "module_health": modules,
        "active_degradation": active_degradation,
        "queue_summary": queue,
        "critical_audits": audits,
    }
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_overview",
        classification="OPS",
        after_state=response,
        event_type="founder.overview.viewed",
        event_payload={"org_count": len(orgs)},
    )
    return response


@router.get("/orgs/{org_id}/health")
def org_health(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    org = get_scoped_record(
        db,
        request,
        Organization,
        org_id,
        user,
        resource_label="organization",
    )
    upgrade_status = check_upgrade_readiness(db, org.id)
    modules, active_degradation = _module_health(db, org.id)
    last_event = (
        db.query(EventLog)
        .filter(EventLog.org_id == org.id)
        .order_by(EventLog.created_at.desc())
        .first()
    )
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_events = (
        db.query(EventLog)
        .filter(EventLog.org_id == org.id, EventLog.created_at >= one_hour_ago)
        .count()
    )
    queue = _queue_summary(db, org.id)
    payload = {
        "org_id": org.id,
        "org_name": org.name,
        "upgrade": upgrade_status,
        "module_health": modules,
        "active_degradation": active_degradation,
        "recent_events_last_hour": recent_events,
        "last_event_at": last_event.created_at.isoformat() if last_event else None,
        "queue_summary": queue,
    }
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_org_health",
        classification="NON_PHI",
        after_state=payload,
        event_type="founder.org.health.viewed",
        event_payload={"org_id": org.id},
    )
    return payload


@router.get("/orgs/{org_id}/users")
def org_users(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    org = get_scoped_record(
        db,
        request,
        Organization,
        org_id,
        user,
        resource_label="organization",
    )
    users = scoped_query(db, User, org.id, request.state.training_mode).order_by(User.created_at.desc()).all()
    records = []
    for person in users:
        last_login = (
            db.query(AccessAudit)
            .filter(AccessAudit.org_id == org.id, AccessAudit.user_email == person.email, AccessAudit.action.ilike("%login%"))
            .order_by(AccessAudit.created_at.desc())
            .first()
        )
        records.append(
            {
                "id": person.id,
                "email": person.email,
                "full_name": person.full_name,
                "role": person.role,
                "last_login": last_login.created_at.isoformat() if last_login else None,
            }
        )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_org_users",
        classification="NON_PHI",
        after_state={"org_id": org.id, "user_count": len(records)},
        event_type="founder.org.users.viewed",
        event_payload={"org_id": org.id},
    )
    return records


class NotificationSMS(BaseModel):
    recipient: str
    message: str
    context: str | None = None


class NotificationEmail(BaseModel):
    to: EmailStr
    subject: str
    body: str
    context: str | None = None


class CallScriptPayload(BaseModel):
    recipient_name: str | None = None
    reason: str | None = None
    incident_id: str | None = None


def _ensure_telnyx_ready():
    if not settings.TELNYX_API_KEY or not settings.TELNYX_NUMBER:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Telnyx is not configured for this tenant",
        )


@router.post("/notify/sms")
def notify_sms(
    payload: NotificationSMS,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    _ensure_telnyx_ready()
    message_payload = MessageCreate(channel="sms", recipient=payload.recipient, body=payload.message)
    telnyx_id = _send_telnyx_message(message_payload)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="notify",
        resource="founder_sms",
        classification="OPS",
        after_state={"recipient": payload.recipient, "telnyx_id": telnyx_id},
        event_type="founder.sms.sent",
        event_payload={
            "recipient": payload.recipient,
            "context": payload.context,
            "telnyx_id": telnyx_id,
        },
    )
    return {"status": "sent", "telnyx_id": telnyx_id}


@router.post("/notify/email")
def notify_email(
    payload: NotificationEmail,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    # Email transport uses SMTP/IMAP (Mailu) as primary method
    # Postmark is optional - check SMTP configuration instead
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Email transport (SMTP) is not configured. Please configure SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD.",
        )
    result = send_outbound(
        db=db,
        request=request,
        user=user,
        payload={
            "classification": "OPS",
            "subject": payload.subject,
            "body_plain": payload.body,
            "body_html": payload.body,
            "recipients": [payload.to],
        },
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="notify",
        resource="founder_email",
        classification="OPS",
        after_state={"recipients": [payload.to], "subject": payload.subject},
        event_type="founder.email.sent",
        event_payload={"recipient": payload.to, "context": payload.context},
    )
    return result


@router.post("/notify/call_script")
def notify_call_script(
    payload: CallScriptPayload,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    org = (
        db.query(Organization)
        .filter(Organization.id == user.org_id)
        .first()
    )
    caller = user.full_name or "Founder Console"
    now_label = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    script = [
        f"Hi {payload.recipient_name or 'there'}, this is {caller} with FusionEMS Quantum.",
        f"We are reaching out on behalf of {org.name if org else 'your organization'} regarding {payload.reason or 'a platform matter'}.",
        f"Reference ID: {payload.incident_id or 'N/A'} • {now_label}",
        "Summarize the issue, verify the org context, and confirm the actions you will take.",
        "If no Telnyx call placement is possible, log the details and hand-off via secure channel.",
    ]
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="call_script",
        resource="founder_call_script",
        classification="NON_PHI",
        after_state={"recipient": payload.recipient_name},
        event_type="founder.call_script.generated",
        event_payload={"recipient": payload.recipient_name, "incident_id": payload.incident_id},
    )
    return {"script": script, "timestamp": now_label}


@router.get("/storage/health")
def storage_health(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    health = StorageHealthService.get_storage_health(db, org_id=str(user.org_id))
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_storage_health",
        classification="OPS",
        after_state={"status": health["status"]},
        event_type="founder.storage.health.viewed",
        event_payload={"status": health["status"]},
    )
    
    return health


@router.get("/storage/activity")
def storage_activity(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    activity = StorageHealthService.get_recent_storage_activity(
        db, 
        org_id=str(user.org_id),
        limit=limit
    )
    
    return {
        "activity": activity,
        "count": len(activity)
    }


@router.get("/storage/breakdown")
def storage_breakdown(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    breakdown = StorageHealthService.get_storage_breakdown(db, org_id=str(user.org_id))
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_storage_breakdown",
        classification="OPS",
        after_state=breakdown,
        event_type="founder.storage.breakdown.viewed",
        event_payload={"systems": breakdown["total_systems"]},
    )
    
    return breakdown


@router.get("/storage/failures")
def storage_failures(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    failures = StorageHealthService.get_failed_operations(
        db,
        org_id=str(user.org_id),
        limit=limit
    )
    
    return {
        "failures": failures,
        "count": len(failures)
    }


@router.get("/system/health")
def unified_system_health(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    from services.founder.system_health_service import SystemHealthService
    
    health = SystemHealthService.get_unified_system_health(db, user.org_id)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="founder_system_health",
        classification="OPS",
        after_state={"overall_status": health["overall_status"]},
        event_type="founder.system.health.viewed",
        event_payload={
            "status": health["overall_status"],
            "critical_issues": len(health["critical_issues"]),
            "warnings": len(health["warnings"])
        },
    )
    
    return health


@router.get("/builders/health")
def builders_health(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.ops_admin)),
):
    from services.founder.system_health_service import SystemHealthService

    builders = SystemHealthService.get_builder_systems_health(db, user.org_id)

    return {
        "builders": builders,
        "timestamp": datetime.utcnow().isoformat()
    }


# ---------- NEMSIS version watch: check for NEMSIS standard updates and notify founders ----------

@router.get("/nemsis-watch/status")
def nemsis_watch_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Return last known NEMSIS version and last check time (no external fetch)."""
    from services.founder.nemsis_watch_service import get_or_create_watch_row
    row = get_or_create_watch_row(db)
    return {
        "last_known_version": row.last_known_version,
        "last_checked_at": row.last_checked_at.isoformat() if row.last_checked_at else None,
        "last_notified_version": row.last_notified_version,
    }


@router.post("/nemsis-watch/check")
def nemsis_watch_check(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Check nemsis.org for current version; if newer than last known, notify founders (in-app + email)."""
    from services.founder.nemsis_watch_service import check_nemsis_version
    return check_nemsis_version(db)


# ---------- Founder AI Assistant: ChatGPT-like fix / add / enhance / suggest / self-heal ----------

class AIAssistantChatRequest(BaseModel):
    message: str
    allow_self_heal: bool = False
    history: list[dict[str, str]] | None = None


@router.post("/ai-assistant/chat")
async def ai_assistant_chat(
    payload: AIAssistantChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Chat with the founder AI assistant. Optional self-heal runs safe actions (retry failed jobs, NEMSIS check)."""
    from services.founder.ai_assistant_service import chat as ai_chat
    result = await ai_chat(
        db=db,
        org_id=user.org_id,
        user_message=payload.message.strip(),
        allow_self_heal=payload.allow_self_heal,
        history=payload.history,
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="chat",
        resource="founder_ai_assistant",
        classification="OPS",
        after_state={"allow_self_heal": payload.allow_self_heal, "actions_count": len(result.get("actions_taken", []))},
        event_type="founder.ai_assistant.chat",
        event_payload={"actions_taken": len(result.get("actions_taken", []))},
    )
    return result
