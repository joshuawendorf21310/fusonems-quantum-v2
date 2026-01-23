from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.email import EmailAttachmentLink, EmailLabel, EmailMessage, EmailMessageLabel, EmailThread
from models.quantum_documents import RetentionPolicy
from models.user import User, UserRole
from utils.decision import DecisionBuilder, finalize_decision_packet
from utils.legal import get_active_hold
from utils.tenancy import scoped_query
from utils.write_ops import audit_and_event, model_snapshot

from services.email.email_ingest_service import ingest_inbound, verify_postmark_signature
from services.email.email_transport_service import send_outbound

router = APIRouter(
    prefix="/api/email",
    tags=["Email"],
    dependencies=[Depends(require_module("EMAIL"))],
)


def _retention_blocked(policy: RetentionPolicy | None, created_at: datetime | None) -> bool:
    if not policy or policy.retention_days is None or created_at is None:
        return False
    created_at_aware = created_at.replace(tzinfo=timezone.utc)
    return created_at_aware + timedelta(days=policy.retention_days) > datetime.now(timezone.utc)


def _policy_decision(
    db: Session,
    request: Request,
    user: User,
    message: EmailMessage,
    action: str,
    policy: RetentionPolicy | None = None,
    hold=None,
) -> dict:
    builder = DecisionBuilder(component="email_policy", component_version="v1")
    if hold:
        builder.add_reason(
            "EMAIL.LEGAL_HOLD.BLOCK.v1",
            "Legal hold is active. Email is frozen.",
            severity="High",
            decision="BLOCK",
        )
        builder.add_next_action(
            "request_release",
            "Request legal hold release",
            f"/api/legal/holds/{hold.id}/request_release",
            "legal",
        )
    if policy and _retention_blocked(policy, message.created_at):
        builder.add_reason(
            "EMAIL.RETENTION.BLOCK_DELETE.v1",
            "Retention policy blocks deletion.",
            severity="High",
            decision="BLOCK",
        )
        builder.add_next_action(
            "export_discovery",
            "Create discovery export instead",
            "/api/documents/exports/discovery",
            "admin",
        )
    if not builder.reasons:
        builder.add_reason(
            "EMAIL.ACTION.ALLOW.v1",
            "Policy checks passed.",
            severity="Low",
            decision="ALLOW",
        )
    return finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload={"message_id": message.id, "action": action},
        classification=message.classification,
        action=f"email_{action}",
        resource="email_message",
        reason_code="SMART_POLICY",
    )


@router.post("/inbound/postmark")
async def inbound_postmark(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    verify_postmark_signature(raw_body, request)
    payload = await request.json()
    return ingest_inbound(db, request, payload)


@router.post("/send", status_code=status.HTTP_201_CREATED)
def send_email(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.billing)),
):
    return send_outbound(db, request, user, payload)


@router.get("/threads")
def list_threads(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, EmailThread, user.org_id, request.state.training_mode)
    if status_filter:
        query = query.filter(EmailThread.status == status_filter)
    return query.order_by(EmailThread.created_at.desc()).all()


@router.get("/threads/{thread_id}")
def get_thread(
    thread_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    thread = (
        scoped_query(db, EmailThread, user.org_id, request.state.training_mode)
        .filter(EmailThread.id == thread_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = (
        scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
        .filter(EmailMessage.thread_id == thread_id)
        .order_by(EmailMessage.created_at.asc())
        .all()
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="email_thread",
        classification="OPS",
        after_state={"thread_id": thread_id},
        event_type="email.thread.read",
        event_payload={"thread_id": thread_id},
        reason_code="READ",
    )
    return {"thread": thread, "messages": messages}


@router.get("/messages")
def list_messages(
    request: Request,
    thread_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
    if thread_id:
        query = query.filter(EmailMessage.thread_id == thread_id)
    return query.order_by(EmailMessage.created_at.desc()).all()


@router.get("/messages/{message_id}/attachments")
def list_attachments(
    message_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return (
        scoped_query(db, EmailAttachmentLink, user.org_id, request.state.training_mode)
        .filter(EmailAttachmentLink.message_id == message_id)
        .order_by(EmailAttachmentLink.created_at.desc())
        .all()
    )


@router.get("/labels")
def list_labels(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, EmailLabel, user.org_id, request.state.training_mode).order_by(
        EmailLabel.name.asc()
    ).all()


@router.post("/messages/{message_id}/labels")
def apply_label(
    message_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    label_slug = payload.get("label", "")
    if not label_slug:
        raise HTTPException(status_code=422, detail="Label required")
    message = (
        scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
        .filter(EmailMessage.id == message_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    label = (
        db.query(EmailLabel)
        .filter(EmailLabel.org_id == user.org_id, EmailLabel.slug == label_slug)
        .first()
    )
    if not label:
        label = EmailLabel(org_id=user.org_id, name=label_slug.title(), slug=label_slug)
        db.add(label)
        db.commit()
        db.refresh(label)
    db.add(
        EmailMessageLabel(
            org_id=user.org_id,
            message_id=message.id,
            label_id=label.id,
            applied_by=user.id,
            applied_by_system=False,
        )
    )
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="label",
        resource="email_message",
        classification=message.classification,
        after_state={"message_id": message.id, "label": label.slug},
        event_type="email.label.applied",
        event_payload={"message_id": message.id, "label": label.slug},
    )
    return {"status": "ok", "label": label.slug}


@router.post("/messages/{message_id}/archive")
def archive_message(
    message_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    message = (
        scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
        .filter(EmailMessage.id == message_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.status = "archived"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="archive",
        resource="email_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="email.archived",
        event_payload={"message_id": message.id},
    )
    return {"status": "archived"}


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.medical_director)),
):
    message = (
        scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
        .filter(EmailMessage.id == message_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    hold = get_active_hold(db, user.org_id, "email_message", str(message.id))
    policy_key = f"email_{message.classification}" if message.classification in {"billing", "legal"} else "email_ops"
    policy = (
        db.query(RetentionPolicy)
        .filter(RetentionPolicy.org_id == user.org_id, RetentionPolicy.applies_to == policy_key)
        .first()
    )
    decision = _policy_decision(db, request, user, message, "delete", policy=policy, hold=hold)
    if decision["decision"] == "BLOCK":
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    message.status = "deleted_pending"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="delete_request",
        resource="email_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="email.delete_requested",
        event_payload={"message_id": message.id},
    )
    return {"status": "queued", "decision": decision}


@router.get("/search")
def search_messages(
    q: str,
    request: Request,
    label: Optional[str] = None,
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    has_attachments: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, EmailMessage, user.org_id, request.state.training_mode)
    if q:
        like = f"%{q}%"
        query = query.filter((EmailMessage.subject.ilike(like)) | (EmailMessage.body_plain.ilike(like)))
    if sender:
        query = query.filter(EmailMessage.sender.ilike(f"%{sender}%"))
    if recipient:
        query = query.filter(EmailMessage.recipients.contains([recipient]))
    if start:
        query = query.filter(EmailMessage.created_at >= datetime.fromisoformat(start))
    if end:
        query = query.filter(EmailMessage.created_at <= datetime.fromisoformat(end))
    if label:
        query = query.join(EmailMessageLabel, EmailMessageLabel.message_id == EmailMessage.id).join(
            EmailLabel, EmailLabel.id == EmailMessageLabel.label_id
        ).filter(EmailLabel.slug == label)
    if has_attachments is True:
        query = query.join(EmailAttachmentLink, EmailAttachmentLink.message_id == EmailMessage.id)
    return query.order_by(EmailMessage.created_at.desc()).all()
