import base64
import hashlib
import hmac
import json

from core.config import settings
from core.database import SessionLocal
from models.email import EmailAttachmentLink, EmailMessage
from models.organization import Organization


def _register(client, email, org_name, role="admin"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Email User",
            "password": "securepass",
            "role": role,
            "organization_name": org_name,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _set_org_domain(org_name, domain):
    session = SessionLocal()
    org = session.query(Organization).filter(Organization.name == org_name).first()
    org.email_domain = domain
    session.commit()
    session.close()


def _postmark_signature(body: bytes, token: str) -> str:
    digest = hmac.new(token.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_postmark_signature_required(client):
    original = settings.POSTMARK_REQUIRE_SIGNATURE
    settings.POSTMARK_REQUIRE_SIGNATURE = True
    response = client.post("/api/email/inbound/postmark", json={"RecordType": "Inbound"})
    settings.POSTMARK_REQUIRE_SIGNATURE = original
    assert response.status_code == 401


def test_inbound_email_creates_document_and_labels(client, tmp_path):
    original = settings.POSTMARK_REQUIRE_SIGNATURE
    settings.POSTMARK_REQUIRE_SIGNATURE = True
    settings.DOCS_STORAGE_LOCAL_DIR = str(tmp_path)
    settings.POSTMARK_SERVER_TOKEN = "postmark-test"

    headers = _register(client, "email@example.com", "EmailOrg")
    _set_org_domain("EmailOrg", "fusonems.test")

    attachment_content = base64.b64encode(b"email-attachment").decode("utf-8")
    payload = {
        "RecordType": "Inbound",
        "From": "billing@payer.test",
        "To": "billing@fusonems.test",
        "Subject": "Invoice INV-1001",
        "TextBody": "Invoice attached for processing.",
        "MessageID": "msg-1001",
        "Attachments": [
            {
                "Name": "invoice.pdf",
                "Content": attachment_content,
                "ContentType": "application/pdf",
                "ContentLength": 12,
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = _postmark_signature(body, settings.POSTMARK_SERVER_TOKEN)
    response = client.post(
        "/api/email/inbound/postmark",
        data=body,
        headers={"X-Postmark-Signature": signature, "Content-Type": "application/json"},
    )
    settings.POSTMARK_REQUIRE_SIGNATURE = original
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["subject"] == "Invoice INV-1001"
    assert "billing" in data["labels"]

    session = SessionLocal()
    message = session.query(EmailMessage).filter(EmailMessage.message_id == "msg-1001").first()
    attachment = (
        session.query(EmailAttachmentLink)
        .filter(EmailAttachmentLink.message_id == message.id)
        .first()
    )
    session.close()
    assert message is not None
    assert attachment is not None


def test_outbound_email_creates_record(client):
    original = settings.POSTMARK_SEND_DISABLED
    settings.POSTMARK_SEND_DISABLED = True
    try:
        headers = _register(client, "outbound@example.com", "OutboundOrg")
        response = client.post(
            "/api/email/send",
            headers=headers,
            json={
                "sender": "ops@fusonems.test",
                "recipients": ["ops@agency.test"],
                "subject": "Ops Update",
                "body_plain": "Status update",
                "classification": "ops",
            },
        )
    finally:
        settings.POSTMARK_SEND_DISABLED = original
    assert response.status_code == 201
    payload = response.json()
    assert payload["message"]["status"] == "sent"


def test_email_search_returns_message(client):
    original = settings.POSTMARK_SEND_DISABLED
    settings.POSTMARK_SEND_DISABLED = True
    try:
        headers = _register(client, "search@example.com", "SearchEmailOrg")
        response = client.post(
            "/api/email/send",
            headers=headers,
            json={
                "sender": "ops@fusonems.test",
                "recipients": ["ops@agency.test"],
                "subject": "Searchable Subject",
                "body_plain": "Search content here.",
                "classification": "ops",
            },
        )
    finally:
        settings.POSTMARK_SEND_DISABLED = original
    assert response.status_code == 201
    response = client.get("/api/email/search?q=Searchable", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1


def test_email_delete_blocked_by_legal_hold(client):
    headers = _register(client, "hold-email@example.com", "HoldEmailOrg")
    _set_org_domain("HoldEmailOrg", "hold.fusonems.test")
    settings.POSTMARK_SEND_DISABLED = True
    response = client.post(
        "/api/email/send",
        headers=headers,
        json={
            "sender": "ops@fusonems.test",
            "recipients": ["ops@agency.test"],
            "subject": "Hold this",
            "body_plain": "Legal hold inbound.",
            "classification": "ops",
        },
    )
    message_id = response.json()["message"]["id"]
    hold_payload = {"scope_type": "email_message", "scope_id": str(message_id), "reason": "legal"}
    response = client.post("/api/legal-hold", json=hold_payload, headers=headers)
    assert response.status_code == 201
    response = client.delete(f"/api/email/messages/{message_id}", headers=headers)
    assert response.status_code == 423
    assert response.json()["decision"] == "BLOCK"
