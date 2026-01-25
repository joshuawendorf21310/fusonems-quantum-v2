import hashlib
import json
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import require_roles
from models.billing_accounts import BillingInvoice
from models.billing_batch5 import BillingPaymentEvent, BillingPortalToken
from models.user import User, UserRole
from services.billing.stripe_service import (
    _get_system_user,
    create_checkout_session,
    handle_stripe_event,
    resolve_invoice,
)
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(prefix="/api/payments/stripe", tags=["Stripe Payments"])


class CheckoutRequest(BaseModel):
    invoiceId: str


class PortalCheckoutRequest(BaseModel):
    token: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/checkout")
def create_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    org_id = str(user.org_id)
    invoice = (
        db.query(BillingInvoice)
        .filter(BillingInvoice.org_id == org_id, BillingInvoice.id == payload.invoiceId)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.amount_due <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice balance cleared")
    if not settings.APP_BASE_URL:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="APP_BASE_URL missing")
    success_url = f"{settings.APP_BASE_URL}/patient-portal?payment=success"
    cancel_url = f"{settings.APP_BASE_URL}/patient-portal?payment=cancel"
    session = create_checkout_session(
        org_id,
        invoice,
        success_url,
        cancel_url,
        idempotency_key=f"invoice-{invoice.id}-{invoice.amount_due}",
    )
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
    return {"checkoutUrl": session["url"]}


@router.post("/portal-checkout")
def create_portal_checkout(payload: PortalCheckoutRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(payload.token)
    portal = db.query(BillingPortalToken).filter(BillingPortalToken.token_hash == token_hash).first()
    if not portal or portal.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token invalid or expired")
    invoice = (
        db.query(BillingInvoice)
        .filter(BillingInvoice.org_id == portal.org_id, BillingInvoice.id == portal.invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.amount_due <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice balance cleared")
    if not settings.APP_BASE_URL:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="APP_BASE_URL missing")
    success_url = f"{settings.APP_BASE_URL}/patient/pay/{payload.token}?status=success"
    cancel_url = f"{settings.APP_BASE_URL}/patient/pay/{payload.token}?status=cancel"
    session = create_checkout_session(
        portal.org_id,
        invoice,
        success_url,
        cancel_url,
        idempotency_key=f"portal-{portal.id}-{invoice.amount_due}",
        patient_account_id=portal.patient_account_id,
    )
    return {"checkoutUrl": session["url"]}


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

    existing = (
        db.query(BillingPaymentEvent)
        .filter(BillingPaymentEvent.provider_event_id == event_id)
        .first()
    )
    if existing:
        return {"status": "duplicate"}

    data_object = event.get("data", {}).get("object", {}) or {}
    metadata = data_object.get("metadata") or {}
    org_id = str(metadata.get("org_id")) if metadata.get("org_id") else None
    payment_event = BillingPaymentEvent(
        org_id=org_id,
        provider="stripe",
        provider_event_id=event_id,
        event_type=event.get("type", ""),
        status="received",
        payload=event if signature_valid else {},
    )
    apply_training_mode(payment_event, request)
    db.add(payment_event)
    db.commit()
    db.refresh(payment_event)

    try:
        result = handle_stripe_event(db, event, org_id, signature_valid)
        payment_event.status = result.get("status", "processed")
        db.commit()
    except Exception as exc:  # noqa: BLE001
        payment_event.status = "retry_pending"
        payment_event.last_error = str(exc)
        payment_event.retry_count += 1
        db.commit()
        raise

    if org_id:
        invoice = resolve_invoice(db, org_id, metadata)
        if invoice:
            system_user = _get_system_user(db, org_id)
            audit_and_event(
                db=db,
                request=None,
                user=system_user,
                action="update",
                resource="billing_invoice",
                classification="BILLING_SENSITIVE",
                after_state=model_snapshot(invoice),
                event_type="billing.invoice.payment_updated",
                event_payload={"invoice_id": invoice.id, "event_id": event_id},
            )
    return {"status": payment_event.status}
