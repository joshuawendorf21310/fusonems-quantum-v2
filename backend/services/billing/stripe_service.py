import hashlib
import uuid
from datetime import datetime

import stripe
from sqlalchemy.orm import Session

from core.config import settings
from models.billing_accounts import (
    BillingInvoice,
    BillingLedgerEntry,
    BillingPayment,
    BillingWebhookReceipt,
)
from services.documents.billing_pdf_service import generate_receipt_pdf
from models.feature_flags import FeatureFlag
from models.module_registry import ModuleRegistry
from models.user import User
from utils.write_ops import audit_and_event, model_snapshot


PRICE_TO_MODULE = {
    settings.STRIPE_PRICE_ID_CAD: "CAD",
    settings.STRIPE_PRICE_ID_EPCR: "EPCR",
    settings.STRIPE_PRICE_ID_BILLING: "BILLING",
    settings.STRIPE_PRICE_ID_COMMS: "COMMS",
    settings.STRIPE_PRICE_ID_SCHEDULING: "SCHEDULING",
    settings.STRIPE_PRICE_ID_FIRE: "FIRE",
    settings.STRIPE_PRICE_ID_HEMS: "HEMS",
    settings.STRIPE_PRICE_ID_INVENTORY: "INVENTORY",
    settings.STRIPE_PRICE_ID_TRAINING: "TRAINING",
    settings.STRIPE_PRICE_ID_QA_LEGAL: "COMPLIANCE",
}


def _set_stripe_key() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY missing")
    stripe.api_key = settings.STRIPE_SECRET_KEY


def payload_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize_org_id(org_id: int | str) -> str:
    try:
        return str(uuid.UUID(str(org_id)))
    except (TypeError, ValueError):
        return str(org_id)


def _get_system_user(db: Session, org_id: int | str) -> User:
    normalized = _normalize_org_id(org_id)
    user = db.query(User).filter(User.org_id == normalized, User.email == "system@fusonems.local").first()
    if user:
        return user
    user = User(
        org_id=normalized,
        email="system@fusonems.local",
        full_name="System Integration",
        hashed_password="",
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def resolve_invoice(db: Session, org_id: int, metadata: dict) -> BillingInvoice | None:
    invoice_id = metadata.get("invoice_id")
    invoice_number = metadata.get("invoice_number")
    query = db.query(BillingInvoice).filter(BillingInvoice.org_id == _normalize_org_id(org_id))
    if invoice_id:
        return query.filter(BillingInvoice.id == invoice_id).first()
    if invoice_number:
        return query.filter(BillingInvoice.invoice_number == invoice_number).first()
    return None


def upsert_feature_flags(db: Session, org_id: int | str, subscription_items: list[dict]) -> None:
    normalized = _normalize_org_id(org_id)
    active_prices = {item.get("price", {}).get("id") for item in subscription_items}
    for price_id, module_key in PRICE_TO_MODULE.items():
        if not price_id:
            continue
        enabled = price_id in active_prices
        flag = (
            db.query(FeatureFlag)
            .filter(
                FeatureFlag.org_id == normalized,
                FeatureFlag.module_key == module_key,
                FeatureFlag.flag_key == "stripe_entitlement",
            )
            .first()
        )
        if not flag:
            flag = FeatureFlag(
                org_id=normalized,
                module_key=module_key,
                flag_key="stripe_entitlement",
                enabled=enabled,
                rules={"source": "stripe"},
            )
            db.add(flag)
        else:
            flag.enabled = enabled
        if settings.STRIPE_ENFORCE_ENTITLEMENTS:
            module = (
                db.query(ModuleRegistry)
                .filter(ModuleRegistry.org_id == normalized, ModuleRegistry.module_key == module_key)
                .first()
            )
            if module:
                module.enabled = enabled
    db.commit()


def record_payment(
    db: Session,
    org_id: int | str,
    invoice: BillingInvoice,
    provider_payment_id: str,
    amount: int,
    status: str,
    method: str,
    metadata: dict,
) -> BillingPayment:
    payment = BillingPayment(
        org_id=_normalize_org_id(org_id),
        invoice_id=invoice.id,
        provider="stripe",
        provider_payment_id=provider_payment_id,
        amount=amount,
        status=status,
        method=method,
        received_at=datetime.utcnow(),
        meta_data=metadata,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def record_ledger_entries(db: Session, org_id: int | str, payment: BillingPayment) -> None:
    normalized = _normalize_org_id(org_id)
    debit = BillingLedgerEntry(
        org_id=normalized,
        entry_type="debit",
        account="Cash",
        amount=payment.amount,
        currency="usd",
        reference_type="payment",
        reference_id=payment.id,
    )
    credit = BillingLedgerEntry(
        org_id=normalized,
        entry_type="credit",
        account="AR",
        amount=payment.amount,
        currency="usd",
        reference_type="payment",
        reference_id=payment.id,
    )
    db.add(debit)
    db.add(credit)
    db.commit()


def update_invoice_balance(invoice: BillingInvoice, payment: BillingPayment) -> None:
    invoice.amount_paid += payment.amount
    invoice.amount_due = max(invoice.total - invoice.amount_paid, 0)
    if invoice.amount_due == 0:
        invoice.status = "PAID"
    elif invoice.amount_paid > 0:
        invoice.status = "PARTIALLY_PAID"


def handle_stripe_event(db: Session, event: dict, org_id: str | None, signature_valid: bool) -> dict:
    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {}) or {}
    metadata = data_object.get("metadata") or {}
    resolved_org_id = org_id or metadata.get("org_id")

    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    } and resolved_org_id:
        items = data_object.get("items", {}).get("data", [])
        upsert_feature_flags(db, resolved_org_id, items)
        return {"status": "entitlements_updated"}

    if not resolved_org_id:
        return {"status": "no_org"}

    invoice = resolve_invoice(db, resolved_org_id, metadata)
    if not invoice:
        return {"status": "invoice_not_found"}

    system_user = _get_system_user(db, resolved_org_id)

    if event_type in {"payment_intent.succeeded", "invoice.payment_succeeded", "invoice.paid"}:
        amount = data_object.get("amount_received") or data_object.get("amount") or 0
        payment = record_payment(
            db,
            resolved_org_id,
            invoice,
            data_object.get("id", ""),
            int(amount),
            "succeeded",
            "card",
            metadata,
        )
        update_invoice_balance(invoice, payment)
        db.commit()
        record_ledger_entries(db, resolved_org_id, payment)
        try:
            generate_receipt_pdf(db, invoice, payment)
        except Exception:
            pass
        audit_and_event(
            db=db,
            request=None,
            user=system_user,
            action="update",
            resource="billing_payment",
            classification="BILLING_SENSITIVE",
            after_state=model_snapshot(payment),
            event_type="billing.patient_payment.succeeded",
            event_payload={"invoice_id": invoice.id, "payment_id": payment.id},
        )
        return {"status": "payment_recorded"}

    if event_type in {"payment_intent.payment_failed", "invoice.payment_failed"}:
        amount = data_object.get("amount") or 0
        payment = record_payment(
            db,
            resolved_org_id,
            invoice,
            data_object.get("id", ""),
            int(amount),
            "failed",
            "card",
            metadata,
        )
        audit_and_event(
            db=db,
            request=None,
            user=system_user,
            action="update",
            resource="billing_payment",
            classification="BILLING_SENSITIVE",
            after_state=model_snapshot(payment),
            event_type="billing.patient_payment.failed",
            event_payload={"invoice_id": invoice.id, "payment_id": payment.id},
        )
        return {"status": "payment_failed_recorded"}

    if event_type in {"charge.refunded", "charge.dispute.created", "charge.dispute.closed"}:
        payment = record_payment(
            db,
            resolved_org_id,
            invoice,
            data_object.get("id", ""),
            int(data_object.get("amount") or 0),
            "refunded" if event_type == "charge.refunded" else "disputed",
            "card",
            metadata,
        )
        audit_and_event(
            db=db,
            request=None,
            user=system_user,
            action="update",
            resource="billing_payment",
            classification="BILLING_SENSITIVE",
            after_state=model_snapshot(payment),
            event_type=f"billing.stripe.{event_type}",
            event_payload={"invoice_id": invoice.id, "payment_id": payment.id},
        )
        return {"status": "payment_refund_recorded"}

    return {"status": "ignored"}


def create_checkout_session(
    org_id: int,
    invoice: BillingInvoice,
    success_url: str,
    cancel_url: str,
    idempotency_key: str | None = None,
    patient_account_id: str | None = None,
) -> dict:
    _set_stripe_key()
    metadata = {
        "org_id": str(org_id),
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
    }
    if patient_account_id:
        metadata["patient_account_id"] = patient_account_id
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": invoice.currency,
                    "product_data": {"name": settings.BILLING_BRAND_NAME},
                    "unit_amount": invoice.amount_due,
                },
            }
        ],
        metadata=metadata,
        payment_intent_data={"metadata": metadata},
        idempotency_key=idempotency_key,
    )
    return {"id": session.id, "url": session.url}
