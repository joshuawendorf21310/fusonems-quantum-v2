from __future__ import annotations

import httpx
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from core.config import settings
from models.email import EmailMessage, EmailThread
from models.quantum_documents import RetentionPolicy
from models.user import User
from utils.decision import DecisionBuilder, finalize_decision_packet
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


def _normalize_subject(subject: str) -> str:
    value = (subject or "").strip()
    while value.lower().startswith(("re:", "fw:")):
        value = value.split(":", 1)[1].strip()
    return value.lower()


def _resolve_thread(db: Session, user: User, subject: str, thread_id: int | None) -> EmailThread:
    if thread_id:
        thread = db.query(EmailThread).filter(EmailThread.org_id == user.org_id, EmailThread.id == thread_id).first()
        if thread:
            return thread
    normalized_subject = _normalize_subject(subject)
    thread = (
        db.query(EmailThread)
        .filter(
            EmailThread.org_id == user.org_id,
            EmailThread.normalized_subject == normalized_subject,
            EmailThread.status != "archived",
        )
        .order_by(EmailThread.created_at.desc())
        .first()
    )
    if thread:
        return thread
    thread = EmailThread(
        org_id=user.org_id,
        subject=subject or "",
        normalized_subject=normalized_subject,
        created_by=user.id,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def send_outbound(
    db: Session,
    request: Request,
    user: User,
    payload: dict,
) -> dict:
    thread = _resolve_thread(db, user, payload.get("subject") or "", payload.get("thread_id"))
    message = EmailMessage(
        org_id=user.org_id,
        thread_id=thread.id,
        classification=payload.get("classification", "ops"),
        direction="outbound",
        status="queued",
        sender=payload.get("sender", settings.POSTMARK_DEFAULT_SENDER),
        recipients=payload.get("recipients", []),
        cc=payload.get("cc", []),
        bcc=payload.get("bcc", []),
        subject=payload.get("subject", ""),
        normalized_subject=_normalize_subject(payload.get("subject", "")),
        body_plain=payload.get("body_plain", ""),
        body_html=payload.get("body_html", ""),
        meta=payload.get("metadata", {}),
        created_by=user.id,
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    thread.last_message_at = message.created_at
    db.commit()

    builder = DecisionBuilder(component="email_transport", component_version="v1")
    if not message.sender:
        builder.add_reason(
            "EMAIL.SENDER.MISSING.v1",
            "Sender is required for outbound email.",
            severity="High",
            decision="BLOCK",
        )
    if not message.recipients:
        builder.add_reason(
            "EMAIL.RECIPIENTS.MISSING.v1",
            "At least one recipient is required.",
            severity="High",
            decision="BLOCK",
        )
    if not builder.reasons:
        builder.add_reason(
            "EMAIL.SEND.ALLOW.v1",
            "Outbound email validated.",
            severity="Low",
            decision="ALLOW",
        )
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload={"message_id": message.id, "recipients": message.recipients},
        classification=message.classification,
        action="email_send",
        resource="email_message",
        reason_code="SMART_POLICY",
    )
    if decision["decision"] == "BLOCK":
        message.status = "blocked"
        db.commit()
        return {"message": model_snapshot(message), "decision": decision}

    if settings.POSTMARK_SEND_DISABLED:
        message.status = "sent"
        message.postmark_message_id = "postmark_disabled"
        db.commit()
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="send",
            resource="email_message",
            classification=message.classification,
            after_state=model_snapshot(message),
            event_type="email.sent",
            event_payload={"message_id": message.id, "mode": "disabled"},
        )
        return {"message": model_snapshot(message), "decision": decision}

    if not settings.POSTMARK_SERVER_TOKEN:
        raise HTTPException(status_code=412, detail="Postmark server token not configured")

    headers = {
        "X-Postmark-Server-Token": settings.POSTMARK_SERVER_TOKEN,
        "Content-Type": "application/json",
    }
    payload_data = {
        "From": message.sender,
        "To": ",".join(message.recipients),
        "Cc": ",".join(message.cc),
        "Bcc": ",".join(message.bcc),
        "Subject": message.subject,
        "TextBody": message.body_plain,
        "HtmlBody": message.body_html,
        "MessageStream": payload.get("message_stream", "outbound"),
        "Headers": [
            {"Name": "X-Thread-Id", "Value": str(thread.id)},
            {"Name": "X-Correlation-Id", "Value": payload.get("correlation_id", "")},
        ],
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{settings.POSTMARK_API_BASE}/email", json=payload_data, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Postmark send failed")
        data = response.json()
        message.status = "sent"
        message.postmark_message_id = data.get("MessageID", "")
        db.commit()
    except HTTPException:
        message.status = "failed"
        db.commit()
        raise
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="send",
        resource="email_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="email.sent",
        event_payload={"message_id": message.id, "postmark_id": message.postmark_message_id},
    )
    return {"message": model_snapshot(message), "decision": decision}
