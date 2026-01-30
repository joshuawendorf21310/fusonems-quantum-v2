from __future__ import annotations


import smtplib
import ssl
from email.message import EmailMessage as SMTPEmailMessage
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
        sender=payload.get("sender", getattr(settings, "POSTMARK_DEFAULT_SENDER", None) or settings.SMTP_USERNAME or settings.FOUNDER_EMAIL),
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


    # Send email using SMTP (Mailu)
    try:
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME
        smtp_pass = settings.SMTP_PASSWORD
        smtp_tls = settings.SMTP_USE_TLS
        if not smtp_host or not smtp_user or not smtp_pass:
            raise HTTPException(status_code=412, detail="SMTP settings not configured")

        email_msg = SMTPEmailMessage()
        email_msg["From"] = message.sender
        email_msg["To"] = ", ".join(message.recipients)
        if message.cc:
            email_msg["Cc"] = ", ".join(message.cc)
        if message.bcc:
            email_msg["Bcc"] = ", ".join(message.bcc)
        email_msg["Subject"] = message.subject
        email_msg.set_content(message.body_plain or message.body_html or "")
        if message.body_html:
            email_msg.add_alternative(message.body_html, subtype="html")

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_tls:
                server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.send_message(email_msg)
        message.status = "sent"
        db.commit()
    except Exception as exc:
        message.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"SMTP send failed: {exc}")

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="send",
        resource="email_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="email.sent",
        event_payload={"message_id": message.id},
    )
    return {"message": model_snapshot(message), "decision": decision}



def send_notification_email(to: str, subject: str, html_body: str, reply_to: str | None = None) -> None:
    """
    Lightweight helper for notification emails using the same Mailu SMTP settings.
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USERNAME
    smtp_pass = settings.SMTP_PASSWORD
    smtp_tls = settings.SMTP_USE_TLS
    sender = settings.SMTP_USERNAME or settings.SMTP_HOST

    if not smtp_host or not smtp_user or not smtp_pass:
        raise HTTPException(status_code=412, detail="SMTP settings not configured")

    email_msg = SMTPEmailMessage()
    email_msg["From"] = sender
    email_msg["To"] = to
    if reply_to:
        email_msg["Reply-To"] = reply_to
    email_msg["Subject"] = subject
    email_msg.set_content(html_body, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(email_msg)

def send_smtp_email_simple(
    to: str,
    subject: str,
    html_body: str,
    from_addr: str | None = None,
    text_body: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
) -> None:
    """
    Send a single email via SMTP (Mailu/self-hosted). No DB or Request.
    Raises ValueError if SMTP not configured; raises Exception on send failure.
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USERNAME
    smtp_pass = settings.SMTP_PASSWORD
    smtp_tls = settings.SMTP_USE_TLS
    sender = from_addr or smtp_user or getattr(settings, "NOREPLY_EMAIL", None) or getattr(settings, "SMTP_FROM_EMAIL", None) or (smtp_host or "noreply")
    if not smtp_host or not smtp_user or not smtp_pass:
        raise ValueError("SMTP settings not configured (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD)")
    email_msg = SMTPEmailMessage()
    email_msg["From"] = sender
    email_msg["To"] = to
    if cc:
        email_msg["Cc"] = ", ".join(cc)
    if bcc:
        email_msg["Bcc"] = ", ".join(bcc)
    if reply_to:
        email_msg["Reply-To"] = reply_to
    email_msg["Subject"] = subject
    if text_body and html_body:
        email_msg.set_content(text_body, subtype="plain")
        email_msg.add_alternative(html_body, subtype="html")
    elif html_body:
        email_msg.set_content(html_body, subtype="html")
    else:
        email_msg.set_content(text_body or "", subtype="plain")
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(email_msg)
