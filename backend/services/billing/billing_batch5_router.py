import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.billing_accounts import BillingInvoice, BillingPayment
from models.billing_batch5 import (
    BillingAppeal,
    BillingClaim,
    BillingClaimEvent,
    BillingContact,
    BillingDenial,
    BillingDocument,
    BillingFacility,
    BillingInvoiceEvent,
    BillingInvoiceItem,
    BillingPatientAccount,
    BillingPaymentEvent,
    BillingPortalToken,
)
from models.user import User, UserRole
from utils.storage import get_storage_backend
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot


router = APIRouter(prefix="/api/billing", tags=["Billing Batch5"])


class InvoiceItemCreate(BaseModel):
    description: str
    code: str = ""
    quantity: int = Field(ge=1, default=1)
    unit_price: int = Field(ge=0, default=0)
    metadata: dict = {}


class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: str
    currency: str = "usd"
    due_date: datetime | None = None
    metadata: dict = {}
    items: list[InvoiceItemCreate]


class InvoiceUpdate(BaseModel):
    due_date: datetime | None = None
    metadata: dict | None = None
    status: str | None = None


class ClaimCreate(BaseModel):
    invoice_id: str
    payer: str
    payload: dict = {}


class ClaimStatusUpdate(BaseModel):
    status: str
    payload: dict = {}


class DenialCreate(BaseModel):
    claim_id: str
    reason: str
    payload: dict = {}


class AppealCreate(BaseModel):
    denial_id: str
    payload: dict = {}


class FacilityCreate(BaseModel):
    name: str
    npi: str = ""
    address: str = ""
    metadata: dict = {}


class ContactCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    role: str = ""
    metadata: dict = {}


class PatientAccountCreate(BaseModel):
    patient_name: str
    email: str = ""
    phone: str = ""
    metadata: dict = {}


class PortalTokenCreate(BaseModel):
    patient_account_id: str
    invoice_id: str
    expires_in_hours: int = Field(ge=1, le=168, default=72)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _invoice_with_org(db: Session, org_id: int, invoice_id: str) -> BillingInvoice | None:
    return (
        db.query(BillingInvoice)
        .filter(BillingInvoice.org_id == str(org_id), BillingInvoice.id == invoice_id)
        .first()
    )


@router.get("/invoices")
def list_invoices(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    invoices = (
        scoped_query(db, BillingInvoice, user.org_id, request.state.training_mode)
        .order_by(BillingInvoice.created_at.desc())
        .all()
    )
    return [model_snapshot(invoice) for invoice in invoices]


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    org_id = str(user.org_id)
    subtotal = sum(item.quantity * item.unit_price for item in payload.items)
    invoice = BillingInvoice(
        org_id=org_id,
        invoice_number=payload.invoice_number,
        customer_id=payload.customer_id,
        currency=payload.currency,
        subtotal=subtotal,
        tax=0,
        total=subtotal,
        amount_due=subtotal,
        due_date=payload.due_date,
        meta_data=payload.metadata,
        status="DRAFT",
    )
    apply_training_mode(invoice, request)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    for item in payload.items:
        line_amount = item.quantity * item.unit_price
        line = BillingInvoiceItem(
            org_id=org_id,
            invoice_id=invoice.id,
            description=item.description,
            code=item.code,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=line_amount,
            meta_data=item.metadata,
        )
        apply_training_mode(line, request)
        db.add(line)

    event = BillingInvoiceEvent(
        org_id=org_id,
        invoice_id=invoice.id,
        event_type="created",
        from_status="",
        to_status=invoice.status,
        payload={"invoice_number": invoice.invoice_number},
    )
    apply_training_mode(event, request)
    db.add(event)
    db.commit()

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_invoice",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(invoice),
        event_type="billing.invoice.created",
        event_payload={"invoice_id": invoice.id},
    )
    return model_snapshot(invoice)


@router.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    invoice = _invoice_with_org(db, user.org_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    items = (
        scoped_query(db, BillingInvoiceItem, user.org_id, request.state.training_mode)
        .filter(BillingInvoiceItem.invoice_id == invoice.id)
        .all()
    )
    return {"invoice": model_snapshot(invoice), "items": [model_snapshot(item) for item in items]}


@router.put("/invoices/{invoice_id}")
def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    invoice = _invoice_with_org(db, user.org_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status not in {"DRAFT", "OPEN"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice immutable")
    before = model_snapshot(invoice)
    if payload.due_date is not None:
        invoice.due_date = payload.due_date
    if payload.metadata is not None:
        invoice.meta_data = payload.metadata
    if payload.status and payload.status != invoice.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use finalize endpoint")
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="billing_invoice",
        classification="BILLING_SENSITIVE",
        before_state=before,
        after_state=model_snapshot(invoice),
        event_type="billing.invoice.updated",
        event_payload={"invoice_id": invoice.id},
    )
    return model_snapshot(invoice)


@router.post("/invoices/{invoice_id}/finalize")
def finalize_invoice(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    invoice = _invoice_with_org(db, user.org_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status == "FINALIZED":
        return {"status": "already_finalized"}
    before_status = invoice.status
    invoice.status = "FINALIZED"
    event = BillingInvoiceEvent(
        org_id=str(user.org_id),
        invoice_id=invoice.id,
        event_type="finalized",
        from_status=before_status,
        to_status=invoice.status,
        payload={"actor": user.email},
    )
    apply_training_mode(event, request)
    db.add(event)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="billing_invoice",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(invoice),
        event_type="billing.invoice.finalized",
        event_payload={"invoice_id": invoice.id},
    )
    return {"status": "finalized", "invoice": model_snapshot(invoice)}


@router.get("/claims")
def list_claims(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    claims = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .order_by(BillingClaim.created_at.desc())
        .all()
    )
    return [model_snapshot(claim) for claim in claims]


@router.post("/claims", status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    org_id = str(user.org_id)
    invoice = _invoice_with_org(db, user.org_id, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    claim = BillingClaim(
        org_id=org_id,
        invoice_id=invoice.id,
        payer=payload.payer,
        status="draft",
        payload=payload.payload,
    )
    apply_training_mode(claim, request)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    event = BillingClaimEvent(
        org_id=org_id,
        claim_id=claim.id,
        event_type="created",
        from_status="",
        to_status=claim.status,
        payload={"invoice_id": invoice.id},
    )
    apply_training_mode(event, request)
    db.add(event)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_claim",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(claim),
        event_type="billing.claim.created",
        event_payload={"claim_id": claim.id},
    )
    return model_snapshot(claim)


@router.post("/claims/{claim_id}/status")
def update_claim_status(
    claim_id: str,
    payload: ClaimStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    claim = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .filter(BillingClaim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    before_status = claim.status
    claim.status = payload.status
    if payload.status == "submitted":
        claim.submitted_at = datetime.utcnow()
    event = BillingClaimEvent(
        org_id=str(user.org_id),
        claim_id=claim.id,
        event_type="status_update",
        from_status=before_status,
        to_status=payload.status,
        payload=payload.payload,
    )
    apply_training_mode(event, request)
    db.add(event)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="billing_claim",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(claim),
        event_type="billing.claim.status_updated",
        event_payload={"claim_id": claim.id},
    )
    return {"status": "updated", "claim": model_snapshot(claim)}


@router.post("/denials", status_code=status.HTTP_201_CREATED)
def create_denial(
    payload: DenialCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    claim = (
        scoped_query(db, BillingClaim, user.org_id, request.state.training_mode)
        .filter(BillingClaim.id == payload.claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    denial = BillingDenial(
        org_id=str(user.org_id),
        claim_id=claim.id,
        reason=payload.reason,
        status="open",
        payload=payload.payload,
    )
    apply_training_mode(denial, request)
    db.add(denial)
    db.commit()
    db.refresh(denial)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_denial",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(denial),
        event_type="billing.denial.created",
        event_payload={"denial_id": denial.id},
    )
    return model_snapshot(denial)


@router.get("/denials")
def list_denials(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    denials = (
        scoped_query(db, BillingDenial, user.org_id, request.state.training_mode)
        .order_by(BillingDenial.created_at.desc())
        .all()
    )
    return [model_snapshot(denial) for denial in denials]


@router.post("/appeals", status_code=status.HTTP_201_CREATED)
def create_appeal(
    payload: AppealCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    denial = (
        scoped_query(db, BillingDenial, user.org_id, request.state.training_mode)
        .filter(BillingDenial.id == payload.denial_id)
        .first()
    )
    if not denial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denial not found")
    appeal = BillingAppeal(
        org_id=str(user.org_id),
        denial_id=denial.id,
        status="draft",
        payload=payload.payload,
    )
    apply_training_mode(appeal, request)
    db.add(appeal)
    db.commit()
    db.refresh(appeal)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_appeal",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(appeal),
        event_type="billing.appeal.created",
        event_payload={"appeal_id": appeal.id},
    )
    return model_snapshot(appeal)


@router.get("/appeals")
def list_appeals(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    appeals = (
        scoped_query(db, BillingAppeal, user.org_id, request.state.training_mode)
        .order_by(BillingAppeal.created_at.desc())
        .all()
    )
    return [model_snapshot(appeal) for appeal in appeals]


@router.get("/patient/accounts")
def list_patient_accounts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    accounts = (
        scoped_query(db, BillingPatientAccount, user.org_id, request.state.training_mode)
        .order_by(BillingPatientAccount.created_at.desc())
        .all()
    )
    return [model_snapshot(account) for account in accounts]


@router.get("/facilities")
def list_facilities(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    facilities = (
        scoped_query(db, BillingFacility, user.org_id, request.state.training_mode)
        .order_by(BillingFacility.created_at.desc())
        .all()
    )
    return [model_snapshot(facility) for facility in facilities]


@router.post("/facilities", status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    facility = BillingFacility(
        org_id=str(user.org_id),
        name=payload.name,
        npi=payload.npi,
        address=payload.address,
        meta_data=payload.metadata,
    )
    apply_training_mode(facility, request)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_facility",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(facility),
        event_type="billing.facility.created",
        event_payload={"facility_id": facility.id},
    )
    return model_snapshot(facility)


@router.get("/facilities/{facility_id}/contacts")
def list_contacts(
    facility_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    contacts = (
        scoped_query(db, BillingContact, user.org_id, request.state.training_mode)
        .filter(BillingContact.facility_id == facility_id)
        .all()
    )
    return [model_snapshot(contact) for contact in contacts]


@router.post("/facilities/{facility_id}/contacts", status_code=status.HTTP_201_CREATED)
def create_contact(
    facility_id: str,
    payload: ContactCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    facility = (
        scoped_query(db, BillingFacility, user.org_id, request.state.training_mode)
        .filter(BillingFacility.id == facility_id)
        .first()
    )
    if not facility:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    contact = BillingContact(
        org_id=str(user.org_id),
        facility_id=facility.id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        meta_data=payload.metadata,
    )
    apply_training_mode(contact, request)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_contact",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(contact),
        event_type="billing.contact.created",
        event_payload={"contact_id": contact.id},
    )
    return model_snapshot(contact)


@router.post("/patient/accounts", status_code=status.HTTP_201_CREATED)
def create_patient_account(
    payload: PatientAccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    account = BillingPatientAccount(
        org_id=str(user.org_id),
        patient_name=payload.patient_name,
        email=payload.email,
        phone=payload.phone,
        meta_data=payload.metadata,
    )
    apply_training_mode(account, request)
    db.add(account)
    db.commit()
    db.refresh(account)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_patient_account",
        classification="PHI",
        after_state=model_snapshot(account),
        event_type="billing.patient_account.created",
        event_payload={"account_id": account.id},
    )
    return model_snapshot(account)


@router.post("/patient/portal-token", status_code=status.HTTP_201_CREATED)
def create_portal_token(
    payload: PortalTokenCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    account = (
        scoped_query(db, BillingPatientAccount, user.org_id, request.state.training_mode)
        .filter(BillingPatientAccount.id == payload.patient_account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient account not found")
    invoice = _invoice_with_org(db, user.org_id, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.utcnow() + timedelta(hours=payload.expires_in_hours)
    portal = BillingPortalToken(
        org_id=str(user.org_id),
        patient_account_id=account.id,
        invoice_id=invoice.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(portal)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_portal_token",
        classification="PHI",
        after_state=model_snapshot(portal),
        event_type="billing.portal_token.created",
        event_payload={"portal_id": portal.id, "invoice_id": invoice.id},
    )
    return {"token": token, "expires_at": expires_at.isoformat()}


@router.get("/patient/{account_id}")
def patient_portal_view(
    account_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    account = (
        scoped_query(db, BillingPatientAccount, user.org_id, request.state.training_mode)
        .filter(BillingPatientAccount.id == account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    invoices = (
        scoped_query(db, BillingInvoice, user.org_id, request.state.training_mode)
        .filter(BillingInvoice.customer_id == account.id)
        .order_by(BillingInvoice.created_at.desc())
        .all()
    )
    payments = (
        scoped_query(db, BillingPayment, user.org_id, request.state.training_mode)
        .filter(BillingPayment.invoice_id.in_([invoice.id for invoice in invoices]))
        .all()
    )
    documents = (
        scoped_query(db, BillingDocument, user.org_id, request.state.training_mode)
        .filter(BillingDocument.invoice_id.in_([invoice.id for invoice in invoices]))
        .all()
    )
    return {
        "account": model_snapshot(account),
        "invoices": [model_snapshot(invoice) for invoice in invoices],
        "payments": [model_snapshot(payment) for payment in payments],
        "documents": [model_snapshot(doc) for doc in documents],
    }


@router.get("/documents/{document_id}")
def get_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.billing, UserRole.admin, UserRole.founder)),
):
    doc = (
        scoped_query(db, BillingDocument, user.org_id, request.state.training_mode)
        .filter(BillingDocument.id == document_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    storage = get_storage_backend()
    data = storage.read_bytes(doc.storage_key)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="billing_document",
        classification=doc.classification,
        after_state=model_snapshot(doc),
        event_type="billing.document.accessed",
        event_payload={"document_id": doc.id},
    )
    return StreamingResponse(
        content=iter([data]),
        media_type=doc.content_type,
        headers={"Content-Disposition": f"inline; filename={doc.file_name or doc.id}.pdf"},
    )


@router.get("/portal/{token}")
def portal_invoice_view(
    token: str,
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(token)
    portal = db.query(BillingPortalToken).filter(BillingPortalToken.token_hash == token_hash).first()
    if not portal or portal.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token invalid or expired")
    invoice = _invoice_with_org(db, portal.org_id, portal.invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    items = (
        scoped_query(db, BillingInvoiceItem, portal.org_id, None)
        .filter(BillingInvoiceItem.invoice_id == invoice.id)
        .all()
    )
    payments = (
        scoped_query(db, BillingPayment, portal.org_id, None)
        .filter(BillingPayment.invoice_id == invoice.id)
        .all()
    )
    documents = (
        scoped_query(db, BillingDocument, portal.org_id, None)
        .filter(BillingDocument.invoice_id == invoice.id)
        .all()
    )
    return {
        "invoice": model_snapshot(invoice),
        "items": [model_snapshot(item) for item in items],
        "payments": [model_snapshot(payment) for payment in payments],
        "documents": [model_snapshot(doc) for doc in documents],
        "expires_at": portal.expires_at.isoformat(),
    }


@router.get("/portal/{token}/documents/{document_id}")
def portal_document_download(
    token: str,
    document_id: str,
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(token)
    portal = db.query(BillingPortalToken).filter(BillingPortalToken.token_hash == token_hash).first()
    if not portal or portal.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token invalid or expired")
    doc = (
        db.query(BillingDocument)
        .filter(
            BillingDocument.id == document_id,
            BillingDocument.invoice_id == portal.invoice_id,
            BillingDocument.org_id == portal.org_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    storage = get_storage_backend()
    data = storage.read_bytes(doc.storage_key)
    return StreamingResponse(
        content=iter([data]),
        media_type=doc.content_type,
        headers={"Content-Disposition": f"inline; filename={doc.file_name or doc.id}.pdf"},
    )


def record_payment_event(
    db: Session,
    event_id: str,
    event_type: str,
    payload: dict,
    org_id: int | None,
) -> BillingPaymentEvent:
    payment_event = BillingPaymentEvent(
        org_id=str(org_id) if org_id else None,
        provider="stripe",
        provider_event_id=event_id,
        event_type=event_type,
        status="received",
        payload=payload,
    )
    db.add(payment_event)
    db.commit()
    db.refresh(payment_event)
    return payment_event
