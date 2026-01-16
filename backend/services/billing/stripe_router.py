import json
from hashlib import sha256

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import require_roles
from models.billing_accounts import BillingInvoice, BillingWebhookReceipt
from models.user import User, UserRole
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import scoped_query
from services.billing.stripe_service import (
    create_checkout_session,
    handle_stripe_event,
    payload_hash,
)

router = APIRouter(prefix="/api/billing/stripe", tags=["Stripe Billing"])


class CheckoutCreate(BaseModel):
    invoice_id: str
    success_url: str
    cancel_url: str


@router.post("/checkout-session")
def create_checkout(
    payload: CheckoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    invoice = (
        scoped_query(db, BillingInvoice, user.org_id, None)
        .filter(BillingInvoice.id == payload.invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.amount_due <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice balance cleared")
    session = create_checkout_session(user.org_id, invoice, payload.success_url, payload.cancel_url)
    audit_and_event(
        db=db,
        request=None,
        user=user,
        action="create",
        resource="stripe_checkout",
        classification="BILLING_SENSITIVE",
        after_state=session,
        event_type="billing.patient_payment.initiated",
        event_payload={"invoice_id": invoice.id, "session_id": session["id"]},
    )
    return session


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("stripe-signature", "")
    signature_valid = False

    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload=raw_body,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
            signature_valid = True
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    else:
        event = json.loads(raw_body.decode("utf-8") or "{}")

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event id")

    existing = db.query(BillingWebhookReceipt).filter(BillingWebhookReceipt.event_id == event_id).first()
    if existing:
        return {"status": "duplicate"}

    receipt = BillingWebhookReceipt(
        provider="stripe",
        event_id=event_id,
        event_type=event.get("type", ""),
        signature_valid=signature_valid,
        payload_hash=payload_hash(raw_body),
        payload_json=event if signature_valid else {},
        processing_status="processing",
    )
    apply_training_mode(receipt, request)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    org_id = None
    metadata = event.get("data", {}).get("object", {}).get("metadata") or {}
    if metadata.get("org_id"):
        org_id = int(metadata.get("org_id"))
        receipt.org_id = org_id
        db.commit()

    result = handle_stripe_event(db, event, org_id, signature_valid)
    receipt.processing_status = result.get("status", "processed")
    db.commit()
    return {"status": receipt.processing_status}
