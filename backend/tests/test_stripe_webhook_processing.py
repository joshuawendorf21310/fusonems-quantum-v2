from types import SimpleNamespace

from core.database import SessionLocal
from models.billing_accounts import BillingCustomer, BillingInvoice, BillingLedgerEntry, BillingPayment, BillingWebhookReceipt
from models.organization import Organization
from services.billing import stripe_router
from core.config import settings


def _create_invoice():
    db = SessionLocal()
    org = Organization(name="BillingOrg", encryption_key="test")
    db.add(org)
    db.commit()
    db.refresh(org)
    org_id = org.id
    customer = BillingCustomer(org_id=org.id, customer_type="patient", display_name="Patient")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    invoice = BillingInvoice(
        org_id=org_id,
        invoice_number="INV-1001",
        customer_id=customer.id,
        status="PATIENT_INVOICED",
        currency="usd",
        total=10000,
        amount_due=10000,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    db.close()
    return org_id, invoice.id, invoice.invoice_number


def test_stripe_webhook_idempotency(client, monkeypatch):
    org_id, invoice_id, invoice_number = _create_invoice()
    original_secret = settings.STRIPE_WEBHOOK_SECRET
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"

    def fake_construct_event(payload, sig_header, secret):
        return {
            "id": "evt_1",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_1",
                    "amount": 10000,
                    "metadata": {"org_id": str(org_id), "invoice_id": invoice_id, "invoice_number": invoice_number},
                }
            },
        }

    monkeypatch.setattr(stripe_router, "stripe", SimpleNamespace(Webhook=SimpleNamespace(construct_event=fake_construct_event)))
    response = client.post("/api/billing/stripe/webhook", data=b"{}", headers={"stripe-signature": "sig"})
    assert response.status_code == 200
    response = client.post("/api/billing/stripe/webhook", data=b"{}", headers={"stripe-signature": "sig"})
    assert response.status_code == 200
    assert response.json()["status"] == "duplicate"
    settings.STRIPE_WEBHOOK_SECRET = original_secret


def test_stripe_payment_updates_invoice_and_ledger(client, monkeypatch):
    org_id, invoice_id, invoice_number = _create_invoice()
    original_secret = settings.STRIPE_WEBHOOK_SECRET
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"

    def fake_construct_event(payload, sig_header, secret):
        return {
            "id": "evt_2",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_2",
                    "amount": 10000,
                    "metadata": {"org_id": str(org_id), "invoice_id": invoice_id, "invoice_number": invoice_number},
                }
            },
        }

    monkeypatch.setattr(stripe_router, "stripe", SimpleNamespace(Webhook=SimpleNamespace(construct_event=fake_construct_event)))
    response = client.post("/api/billing/stripe/webhook", data=b"{}", headers={"stripe-signature": "sig"})
    assert response.status_code == 200

    db = SessionLocal()
    invoice = db.query(BillingInvoice).filter(BillingInvoice.id == invoice_id).first()
    payments = db.query(BillingPayment).filter(BillingPayment.invoice_id == invoice_id).all()
    ledger = db.query(BillingLedgerEntry).filter(BillingLedgerEntry.reference_type == "payment").all()
    receipts = db.query(BillingWebhookReceipt).filter(BillingWebhookReceipt.event_id == "evt_2").all()
    db.close()

    assert invoice.status == "PAID"
    assert invoice.amount_due == 0
    assert payments
    assert len(ledger) >= 2
    assert receipts
    settings.STRIPE_WEBHOOK_SECRET = original_secret
