from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from typing import Optional
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from core.config import settings
from models.email import EmailAttachmentLink, EmailLabel, EmailMessage, EmailMessageLabel, EmailThread
from models.organization import Organization
from models.quantum_documents import DocumentFile, RetentionPolicy
from core.security import hash_password
from models.user import User
from utils.decision import DecisionBuilder, finalize_decision_packet
from utils.events import event_bus
from utils.storage import build_storage_key, get_storage_backend
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

import imaplib
import email

# === IMAP Polling for Self-Hosted Mailu ===
def poll_inbound_imap(db, request):
    """
    Polls the IMAP inbox for new messages and ingests them.
    This is a stub for integration; production should use a background task or scheduler.
    """
    imap_host = settings.IMAP_HOST
    imap_port = settings.IMAP_PORT
    imap_user = settings.IMAP_USERNAME
    imap_pass = settings.IMAP_PASSWORD
    imap_tls = settings.IMAP_USE_TLS
    if not imap_host or not imap_user or not imap_pass:
        raise Exception("IMAP settings not configured")
    if imap_tls:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
    else:
        mail = imaplib.IMAP4(imap_host, imap_port)
    mail.login(imap_user, imap_pass)
    mail.select("INBOX")
    typ, data = mail.search(None, 'UNSEEN')
    if not data or not data[0]:
        mail.logout()
        return
    for num in data[0].split():
        typ, msg_data = mail.fetch(num, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                # Convert msg to dict payload for ingest_inbound
                body_plain = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body_plain = (part.get_payload(decode=True) or b"").decode(errors="ignore")
                            break
                        if part.get_content_type() == "text/html" and not body_plain:
                            body_plain = (part.get_payload(decode=True) or b"").decode(errors="ignore")
                else:
                    body_plain = (msg.get_payload(decode=True) or b"").decode(errors="ignore")
                payload = {
                    "From": msg.get("From"),
                    "To": msg.get("To"),
                    "Subject": msg.get("Subject"),
                    "TextBody": body_plain,
                    "body_plain": body_plain,
                }
                ingest_inbound(db, request, payload)
        mail.store(num, '+FLAGS', '\\Seen')
    mail.logout()

def verify_postmark_signature(raw_body: bytes, request: Request) -> None:
    if not settings.POSTMARK_REQUIRE_SIGNATURE:
        return
    signature = request.headers.get("X-Postmark-Signature") or request.headers.get("x-postmark-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Postmark signature")
    if not settings.POSTMARK_SERVER_TOKEN:
        raise HTTPException(status_code=401, detail="Missing Postmark server token")
    digest = hmac.new(settings.POSTMARK_SERVER_TOKEN.encode("utf-8"), raw_body, hashlib.sha256).digest()
    signature_expected = base64.b64encode(digest).decode("utf-8")
    if not hmac.compare_digest(signature_expected, signature):
        raise HTTPException(status_code=401, detail="Invalid Postmark signature")


def _normalize_subject(subject: str) -> str:
    value = (subject or "").strip()
    while value.lower().startswith(("re:", "fw:")):
        value = value.split(":", 1)[1].strip()
    return value.lower()


def _resolve_org(db: Session, to_addresses: list[str]) -> Organization | None:
    domains = [addr.split("@")[-1].lower() for addr in to_addresses if "@" in addr]
    if not domains:
        return None
    return (
        db.query(Organization)
        .filter(Organization.email_domain.in_(domains))
        .order_by(Organization.id.asc())
        .first()
    )


def _resolve_thread(
    db: Session,
    org_id: int,
    subject: str,
    message_id: str,
    references: list[str],
    in_reply_to: str,
) -> EmailThread:
    normalized_subject = _normalize_subject(subject)
    if in_reply_to:
        existing = (
            db.query(EmailMessage)
            .filter(EmailMessage.org_id == org_id, EmailMessage.message_id == in_reply_to)
            .first()
        )
        if existing:
            return db.query(EmailThread).filter(EmailThread.id == existing.thread_id).first()
    if references:
        existing = (
            db.query(EmailMessage)
            .filter(EmailMessage.org_id == org_id, EmailMessage.message_id.in_(references))
            .first()
        )
        if existing:
            return db.query(EmailThread).filter(EmailThread.id == existing.thread_id).first()
    thread = (
        db.query(EmailThread)
        .filter(EmailThread.org_id == org_id, EmailThread.normalized_subject == normalized_subject)
        .order_by(EmailThread.created_at.desc())
        .first()
    )
    if thread:
        return thread
    thread = EmailThread(
        org_id=org_id,
        subject=subject,
        normalized_subject=normalized_subject,
        created_by=None,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def _ensure_label(db: Session, org_id: int, name: str, color: str = "orange") -> EmailLabel:
    slug = name.strip().lower().replace(" ", "-")
    label = (
        db.query(EmailLabel)
        .filter(EmailLabel.org_id == org_id, EmailLabel.slug == slug)
        .first()
    )
    if label:
        return label
    label = EmailLabel(org_id=org_id, name=name, slug=slug, color=color)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def _apply_labels(db: Session, org_id: int, message: EmailMessage, attachments: list[dict]) -> list[str]:
    applied = []
    subject = message.subject.lower()
    body = message.body_plain.lower()
    rules = [
        ("Billing", "BILLING", "EMAIL.LABEL.BILLING.v1", ["invoice", "payment", "cms", "edi", "claim"]),
        ("Legal", "LEGAL", "EMAIL.LABEL.LEGAL.v1", ["subpoena", "legal", "court", "discovery", "hold"]),
        ("OCR", "OPS", "EMAIL.LABEL.OCR.v1", ["scan", "ocr"]),
        ("Compliance", "OPS", "EMAIL.LABEL.COMPLIANCE.v1", ["retention", "policy", "compliance"]),
    ]
    for label_name, _, _, keywords in rules:
        if any(keyword in subject or keyword in body for keyword in keywords):
            label = _ensure_label(db, org_id, label_name)
            db.add(
                EmailMessageLabel(
                    org_id=org_id,
                    message_id=message.id,
                    label_id=label.id,
                    applied_by=None,
                    applied_by_system=True,
                )
            )
            applied.append(label.slug)
    if attachments:
        label = _ensure_label(db, org_id, "Attachments")
        db.add(
            EmailMessageLabel(
                org_id=org_id,
                message_id=message.id,
                label_id=label.id,
                applied_by=None,
                applied_by_system=True,
            )
        )
        applied.append(label.slug)
    db.commit()
    return applied


def _classify_message(subject: str, body: str) -> str:
    subject = (subject or "").lower()
    body = (body or "").lower()
    if any(keyword in subject or keyword in body for keyword in ["invoice", "payment", "cms", "edi", "claim"]):
        return "billing"
    if any(keyword in subject or keyword in body for keyword in ["subpoena", "legal", "court", "discovery", "hold"]):
        return "legal"
    return "ops"


def ingest_inbound(
    db: Session,
    request: Request,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record_type = payload.get("RecordType") or payload.get("record_type") or "Inbound"
    if record_type.lower() != "inbound":
        return {"status": "ignored"}

    to_addresses = payload.get("To") or payload.get("ToFull") or []
    to_list = []
    if isinstance(to_addresses, str):
        to_list = [to_addresses]
    elif isinstance(to_addresses, list):
        for entry in to_addresses:
            if isinstance(entry, str):
                to_list.append(entry)
            elif isinstance(entry, dict):
                to_list.append(entry.get("Email", ""))
    org = _resolve_org(db, to_list)
    if not org:
        raise HTTPException(status_code=404, detail="Unknown org domain")

    subject = payload.get("Subject", "")
    message_id = payload.get("MessageID") or payload.get("MessageId") or ""
    in_reply_to = payload.get("InReplyTo") or ""
    references = payload.get("References") or []
    sender = payload.get("From") or ""
    body_plain = payload.get("TextBody") or payload.get("body_plain") or ""
    body_html = payload.get("HtmlBody") or ""
    thread = _resolve_thread(db, org.id, subject, message_id, references, in_reply_to)

    classification = _classify_message(subject, body_plain)
    message = EmailMessage(
        org_id=org.id,
        thread_id=thread.id,
        classification=classification,
        direction="inbound",
        status="received",
        sender=sender,
        recipients=to_list,
        cc=payload.get("Cc") or [],
        bcc=payload.get("Bcc") or [],
        subject=subject,
        normalized_subject=_normalize_subject(subject),
        body_plain=body_plain,
        body_html=body_html,
        message_id=message_id or str(uuid4()),
        in_reply_to=in_reply_to,
        references=references if isinstance(references, list) else [references],
        postmark_record_type=record_type,
        meta={"transport": payload.get("transport", "postmark"), "spam_score": payload.get("SpamScore"), "spam_status": payload.get("SpamStatus")},
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    thread.last_message_at = message.created_at
    db.commit()

    attachments = payload.get("Attachments") or []
    attachment_links = []
    for attachment in attachments:
        content = attachment.get("Content") or ""
        if not content:
            continue
        decoded = base64.b64decode(content)
        sha256 = hashlib.sha256(decoded).hexdigest()
        filename = attachment.get("Name", "attachment")
        storage_key = build_storage_key(org.id, f"email/{sha256}/{filename}")
        get_storage_backend().write_bytes(storage_key, decoded)
        policy_key = f"email_{classification}" if classification in {"billing", "legal"} else "email_ops"
        policy = (
            db.query(RetentionPolicy)
            .filter(RetentionPolicy.org_id == org.id, RetentionPolicy.applies_to == policy_key)
            .first()
        )
        doc = DocumentFile(
            org_id=org.id,
            folder_id=None,
            filename=attachment.get("Name", "attachment"),
            content_type=attachment.get("ContentType", "application/octet-stream"),
            size_bytes=attachment.get("ContentLength", len(decoded)),
            storage_key=storage_key,
            sha256=sha256,
            classification=classification,
            tags=["email"],
            status="ACTIVE",
            retention_policy_id=policy.id if policy else None,
        )
        apply_training_mode(doc, request)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        link = EmailAttachmentLink(
            org_id=org.id,
            message_id=message.id,
            document_id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            sha256=doc.sha256,
        )
        db.add(link)
        db.commit()
        attachment_links.append(model_snapshot(link))

    labels = _apply_labels(db, org.id, message, attachments)

    builder = DecisionBuilder(component="email_ingest", component_version="v1")
    if payload.get("SpamStatus") == "Spam" or (payload.get("SpamScore") or 0) > 5:
        builder.add_reason(
            "EMAIL.SPAM.BLOCK.v1",
            "Inbound email flagged as spam.",
            severity="High",
            decision="BLOCK",
        )
    if not builder.reasons:
        builder.add_reason(
            "EMAIL.INGEST.ALLOW.v1",
            "Inbound email accepted.",
            severity="Low",
            decision="ALLOW",
        )
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=_system_user(db, org.id),
        builder=builder,
        input_payload={"message_id": message.id, "labels": labels},
        classification=message.classification,
        action="email_ingest",
        resource="email_message",
        reason_code="SMART_POLICY",
    )
    audit_and_event(
        db=db,
        request=request,
        user=_system_user(db, org.id),
        action="receive",
        resource="email_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="email.received",
        event_payload={"message_id": message.id, "thread_id": thread.id},
    )
    event_bus.publish(
        db=db,
        org_id=org.id,
        event_type="email.inbound.received",
        payload={"message_id": message.id, "thread_id": thread.id, "labels": labels},
        actor_id=None,
        actor_role="system",
        device_id="",
        server_time=getattr(request.state, "server_time", datetime.now(timezone.utc)),
        drift_seconds=getattr(request.state, "drift_seconds", 0),
        drifted=getattr(request.state, "drifted", False),
        training_mode=getattr(request.state, "training_mode", False),
    )
    return {
        "message": model_snapshot(message),
        "attachments": attachment_links,
        "labels": labels,
        "decision": decision,
    }


def _system_user(db: Session, org_id: int) -> User:
    user = db.query(User).filter(User.org_id == org_id, User.email == "system@fusonems.local").first()
    if user:
        return user
    user = User(
        org_id=org_id,
        email="system@fusonems.local",
        full_name="System Integration",
        hashed_password=hash_password("system"),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
