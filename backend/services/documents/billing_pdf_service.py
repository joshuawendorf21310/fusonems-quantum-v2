from __future__ import annotations

import io
from datetime import datetime
from sqlalchemy.orm import Session

from models.billing_accounts import BillingInvoice, BillingPayment
from models.billing_batch5 import BillingDocument, BillingInvoiceItem
from utils.storage import build_storage_key, get_storage_backend


def _render_header(pdf, title: str) -> None:
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, 750, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, 735, datetime.utcnow().isoformat())


def generate_invoice_pdf(db: Session, invoice: BillingInvoice) -> BillingDocument:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("reportlab must be installed for PDF generation") from exc
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _render_header(pdf, f"Invoice {invoice.invoice_number}")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(72, 700, f"Invoice ID: {invoice.id}")
    pdf.drawString(72, 685, f"Status: {invoice.status}")
    pdf.drawString(72, 670, f"Amount Due: ${invoice.amount_due / 100:.2f}")

    items = (
        db.query(BillingInvoiceItem)
        .filter(BillingInvoiceItem.invoice_id == invoice.id)
        .order_by(BillingInvoiceItem.created_at.asc())
        .all()
    )
    y = 640
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(72, y, "Line Items")
    y -= 15
    pdf.setFont("Helvetica", 10)
    for item in items:
        line = f"{item.description} ({item.code}) x{item.quantity} - ${item.amount / 100:.2f}"
        pdf.drawString(72, y, line)
        y -= 12
        if y < 72:
            pdf.showPage()
            y = 720
            pdf.setFont("Helvetica", 10)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    data = buffer.read()
    storage = get_storage_backend()
    file_name = f"invoice-{invoice.invoice_number}.pdf"
    key = build_storage_key(invoice.org_id, f"billing/{invoice.id}/{file_name}")
    storage.write_bytes(key, data, content_type="application/pdf")
    document = BillingDocument(
        org_id=invoice.org_id,
        invoice_id=invoice.id,
        doc_type="invoice",
        storage_key=key,
        file_name=file_name,
        content_type="application/pdf",
        checksum=str(len(data)),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def generate_receipt_pdf(db: Session, invoice: BillingInvoice, payment: BillingPayment) -> BillingDocument:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("reportlab must be installed for PDF generation") from exc
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _render_header(pdf, f"Receipt {invoice.invoice_number}")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(72, 700, f"Payment ID: {payment.id}")
    pdf.drawString(72, 685, f"Amount Paid: ${payment.amount / 100:.2f}")
    pdf.drawString(72, 670, f"Paid At: {payment.received_at.isoformat() if payment.received_at else ''}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    data = buffer.read()
    storage = get_storage_backend()
    file_name = f"receipt-{payment.id}.pdf"
    key = build_storage_key(invoice.org_id, f"billing/{invoice.id}/receipts/{file_name}")
    storage.write_bytes(key, data, content_type="application/pdf")
    document = BillingDocument(
        org_id=invoice.org_id,
        invoice_id=invoice.id,
        payment_id=payment.id,
        doc_type="receipt",
        storage_key=key,
        file_name=file_name,
        content_type="application/pdf",
        checksum=str(len(data)),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
