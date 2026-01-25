from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.billing_accounts import BillingInvoice, BillingPayment
from models.billing_batch5 import BillingDocument
from models.user import User, UserRole
from services.documents.billing_pdf_service import generate_invoice_pdf, generate_receipt_pdf
from utils.storage import get_storage_backend
from utils.tenancy import scoped_query
from utils.write_ops import audit_and_event, model_snapshot


router = APIRouter(prefix="/api/docs", tags=["Billing Documents"])


@router.get("/invoice/{invoice_id}.pdf")
def get_invoice_pdf(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    invoice = (
        scoped_query(db, BillingInvoice, user.org_id, request.state.training_mode)
        .filter(BillingInvoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    document = (
        scoped_query(db, BillingDocument, user.org_id, request.state.training_mode)
        .filter(BillingDocument.invoice_id == invoice.id, BillingDocument.doc_type == "invoice")
        .order_by(BillingDocument.created_at.desc())
        .first()
    )
    if not document:
        document = generate_invoice_pdf(db, invoice)
    storage = get_storage_backend()
    data = storage.read_bytes(document.storage_key)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="billing_document",
        classification=document.classification,
        after_state=model_snapshot(document),
        event_type="billing.document.accessed",
        event_payload={"document_id": document.id},
    )
    return StreamingResponse(
        content=iter([data]),
        media_type=document.content_type,
        headers={"Content-Disposition": f"inline; filename={document.file_name}"},
    )


@router.get("/receipt/{payment_id}.pdf")
def get_receipt_pdf(
    payment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    payment = (
        scoped_query(db, BillingPayment, user.org_id, request.state.training_mode)
        .filter(BillingPayment.id == payment_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    invoice = (
        scoped_query(db, BillingInvoice, user.org_id, request.state.training_mode)
        .filter(BillingInvoice.id == payment.invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    document = (
        scoped_query(db, BillingDocument, user.org_id, request.state.training_mode)
        .filter(BillingDocument.payment_id == payment.id, BillingDocument.doc_type == "receipt")
        .order_by(BillingDocument.created_at.desc())
        .first()
    )
    if not document:
        document = generate_receipt_pdf(db, invoice, payment)
    storage = get_storage_backend()
    data = storage.read_bytes(document.storage_key)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="billing_document",
        classification=document.classification,
        after_state=model_snapshot(document),
        event_type="billing.document.accessed",
        event_payload={"document_id": document.id},
    )
    return StreamingResponse(
        content=iter([data]),
        media_type=document.content_type,
        headers={"Content-Disposition": f"inline; filename={document.file_name}"},
    )
