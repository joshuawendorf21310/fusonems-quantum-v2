from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.auth import create_access_token
from core.security import hash_password
from models.session import Session as UserSession
from models.organization import Organization
from models.user import User


def _seed_user(db: Session, email: str, org_name: str, role: str = "billing") -> tuple[User, str]:
    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)
    user = User(email=email, password_hash=hash_password("pass"), role=role, org_id=org.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    token, expires_at = create_access_token(subject=str(user.id), org_id=str(org.id), role=user.role)
    session = UserSession(user_id=user.id, token=token, expires_at=expires_at)
    db.add(session)
    db.commit()
    return user, token


def test_billing_invoice_org_isolation(client):
    db = SessionLocal()
    try:
        _, token_a = _seed_user(db, "billing-a@example.com", "OrgA", "billing")
        _, token_b = _seed_user(db, "billing-b@example.com", "OrgB", "billing")
    finally:
        db.close()

    create_payload = {
        "invoice_number": "INV-001",
        "customer_id": "cust-001",
        "items": [{"description": "Transport", "quantity": 1, "unit_price": 25000}],
    }
    response = client.post(
        "/api/billing/invoices",
        json=create_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    response = client.get(
        f"/api/billing/invoices/{invoice_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


def test_billing_requires_auth(client):
    response = client.get("/api/billing/invoices")
    assert response.status_code == 401


def test_stripe_webhook_idempotent(client):
    event = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {"metadata": {"org_id": "1"}}},
    }
    response = client.post("/api/payments/stripe/webhook", json=event)
    assert response.status_code == 200
    response = client.post("/api/payments/stripe/webhook", json=event)
    assert response.status_code == 200
    assert response.json()["status"] == "duplicate"
