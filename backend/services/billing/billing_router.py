from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.guards import require_module
from core.security import require_roles, require_mfa
from models.billing import BillingRecord
from models.billing_accounts import BillingInvoice, BillingInvoiceLine
from models.billing_exports import (
    AppealPacket,
    ClaimStatusInquiry,
    ClaimSubmission,
    ClearinghouseAck,
    EligibilityCheck,
    PatientStatement,
    PaymentPosting,
    RemittanceAdvice,
)
from models.business_ops import BusinessOpsTask
from models.user import User, UserRole
from utils.legal import enforce_legal_hold
from utils.decision import DecisionBuilder, finalize_decision_packet
from utils.events import event_bus
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import get_scoped_record, scoped_query


router = APIRouter(
    prefix="/api/billing",
    tags=["Billing"],
    dependencies=[Depends(require_module("BILLING"))],
)


class BillingCreate(BaseModel):
    patient_name: str
    invoice_number: str
    payer: str
    amount_due: float
    status: str = "Open"
    claim_payload: dict = {}


class BillingResponse(BillingCreate):
    id: int

    class Config:
        from_attributes = True


class InternalInvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: str
    status: str = "DRAFT"
    currency: str = "usd"
    subtotal: int = 0
    tax: int = 0
    total: int = 0
    amount_due: int = 0
    metadata: dict = {}
    lines: list[dict] = []


class InternalInvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    status: str
    currency: str
    total: int
    amount_due: int
    meta_data: dict

    class Config:
        from_attributes = True


class BusinessOpsCreate(BaseModel):
    title: str
    owner: str
    priority: str = "Normal"
    metadata: dict = {}


class ClaimSubmissionCreate(BaseModel):
    invoice_number: str
    clearinghouse: str = "OfficeAlly"
    edi_version: str = "005010X222A1"
    payload: dict = {}


class RemittanceCreate(BaseModel):
    payer: str
    claim_reference: str = ""
    payload: dict = {}


class AckCreate(BaseModel):
    ack_type: str = "999"
    reference: str = ""
    payload: dict = {}


class EligibilityCreate(BaseModel):
    patient_name: str
    payer: str = ""
    payload: dict = {}


class ClaimStatusCreate(BaseModel):
    claim_reference: str = ""
    payload: dict = {}


class StatementCreate(BaseModel):
    patient_name: str
    balance_due: str = "0"
    payload: dict = {}


class PaymentCreate(BaseModel):
    source: str = "manual"
    amount: str = "0"
    payload: dict = {}


class AppealCreate(BaseModel):
    claim_reference: str = ""
    payload: dict = {}


class BillingReadinessRequest(BaseModel):
    invoice_number: str


@router.post("/readiness")
def billing_readiness(
    payload: BillingReadinessRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    record = (
        db.query(BillingRecord)
        .filter(BillingRecord.org_id == user.org_id, BillingRecord.invoice_number == payload.invoice_number)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    builder = DecisionBuilder(component="billing_readiness", component_version="v1")
    evidence_ref = builder.add_evidence(
        "billing_record",
        f"invoice:{record.invoice_number}",
        {"invoice_id": record.id},
    )
    required_fields = ["patient_name", "invoice_number", "payer", "amount_due"]
    missing_fields = [field for field in required_fields if not getattr(record, field)]
    claim_payload = record.claim_payload or {}
    claim_required = ["diagnosis_codes", "procedure_codes", "service_date", "transport_miles"]
    missing_claim = [field for field in claim_required if not claim_payload.get(field)]
    if missing_fields:
        builder.add_reason(
            "BILL.CMS.REQUIRED_FIELDS.v1",
            "Required billing fields are missing.",
            severity="High",
            decision="BLOCK",
            evidence_refs=[evidence_ref],
        )
    if missing_claim:
        builder.add_reason(
            "BILL.CMS.CLAIM_PAYLOAD.MINIMUM.v1",
            "Claim payload is missing required CMS fields.",
            severity="High",
            decision="BLOCK",
            evidence_refs=[evidence_ref],
        )
    if not builder.reasons:
        builder.add_reason(
            "BILL.CMS.READINESS_SCORE.v1",
            "Invoice meets readiness requirements.",
            severity="Low",
            decision="ALLOW",
            evidence_refs=[evidence_ref],
        )
    total_checks = len(required_fields) + len(claim_required)
    readiness_score = round(1 - (len(missing_fields) + len(missing_claim)) / max(total_checks, 1), 2)
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload={"invoice_number": payload.invoice_number, "claim_fields": claim_payload},
        classification=record.classification,
        action="billing_readiness",
        resource="billing_record",
        reason_code="SMART_POLICY",
    )
    event_bus.publish(
        db=db,
        org_id=user.org_id,
        event_type="billing.readiness.checked",
        payload={
            "invoice_number": record.invoice_number,
            "missing_fields": missing_fields,
            "missing_claim_fields": missing_claim,
            "readiness_score": readiness_score,
        },
        actor_id=user.id,
        actor_role=user.role,
        device_id=request.headers.get("x-device-id", ""),
        server_time=getattr(request.state, "server_time", None),
        drift_seconds=getattr(request.state, "drift_seconds", 0),
        drifted=getattr(request.state, "drifted", False),
        training_mode=getattr(request.state, "training_mode", False),
    )
    return {
        "invoice_number": record.invoice_number,
        "readiness_score": readiness_score,
        "missing_fields": missing_fields,
        "missing_claim_fields": missing_claim,
        "decision": decision,
    }


@router.post("/invoices", response_model=BillingResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: BillingCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    enforce_legal_hold(db, user.org_id, "billing_record", payload.invoice_number, "create")
    record = BillingRecord(**payload.model_dump(), org_id=user.org_id)
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_record",
        classification=record.classification,
        after_state=model_snapshot(record),
        event_type="billing.invoice.created",
        event_payload={"invoice_id": record.id, "invoice_number": record.invoice_number},
    )
    return record


@router.get("/invoices", response_model=list[BillingResponse])
def list_invoices(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, BillingRecord, user.org_id, request.state.training_mode).order_by(
        BillingRecord.created_at.desc()
    ).all()


@router.get("/internal-invoices", response_model=list[InternalInvoiceResponse])
def list_internal_invoices(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    invoices = scoped_query(db, BillingInvoice, user.org_id, request.state.training_mode).order_by(
        BillingInvoice.created_at.desc()
    ).all()
    return [model_snapshot(invoice) for invoice in invoices]


@router.post("/internal-invoices", response_model=InternalInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_internal_invoice(
    payload: InternalInvoiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    invoice = BillingInvoice(
        org_id=user.org_id,
        invoice_number=payload.invoice_number,
        customer_id=payload.customer_id,
        status=payload.status,
        currency=payload.currency,
        subtotal=payload.subtotal,
        tax=payload.tax,
        total=payload.total,
        amount_due=payload.amount_due,
        meta_data=payload.metadata,
    )
    apply_training_mode(invoice, request)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    for line in payload.lines:
        db.add(
            BillingInvoiceLine(
                org_id=user.org_id,
                invoice_id=invoice.id,
                description=line.get("description", ""),
                code=line.get("code", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line.get("amount", 0),
                meta_data=line.get("metadata", {}),
            )
        )
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="billing_invoice",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(invoice),
        event_type="billing.internal_invoice.created",
        event_payload={"invoice_id": invoice.id},
    )
    return model_snapshot(invoice)


@router.get("/internal-invoices/{invoice_id}/lines")
def list_internal_invoice_lines(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing)),
):
    lines = (
        scoped_query(db, BillingInvoiceLine, user.org_id, request.state.training_mode)
        .filter(BillingInvoiceLine.invoice_id == invoice_id)
        .order_by(BillingInvoiceLine.created_at.desc())
        .all()
    )
    return [model_snapshot(line) for line in lines]


@router.post("/claims/837p", status_code=status.HTTP_201_CREATED)
def submit_837p(
    payload: ClaimSubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
    _: User = Depends(require_mfa),
):
    submission = ClaimSubmission(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(submission, request)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="claim_submission",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(submission),
        event_type="billing.claim.submitted",
        event_payload={"submission_id": submission.id, "invoice_number": submission.invoice_number},
    )
    return model_snapshot(submission)


@router.get("/claims/837p")
def list_837p(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    submissions = (
        scoped_query(db, ClaimSubmission, user.org_id, request.state.training_mode)
        .order_by(ClaimSubmission.created_at.desc())
        .all()
    )
    return [model_snapshot(submission) for submission in submissions]


@router.get("/claims/{invoice_number}/hcfa-1500")
def get_hcfa(invoice_number: str):
    return {
        "status": "ok",
        "form": "HCFA-1500",
        "invoice_number": invoice_number,
        "fields": {"payer": "CMS", "cpt": ["A0427"], "modifiers": ["QL"]},
    }


@router.post("/remittance/835", status_code=status.HTTP_201_CREATED)
def import_835(
    payload: RemittanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
    _: User = Depends(require_mfa),
):
    record = RemittanceAdvice(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="remittance_advice",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.remittance.imported",
        event_payload={"remittance_id": record.id},
    )
    return record


@router.get("/remittance/835")
def list_835(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    remittances = (
        scoped_query(db, RemittanceAdvice, user.org_id, request.state.training_mode)
        .order_by(RemittanceAdvice.created_at.desc())
        .all()
    )
    return [model_snapshot(remittance) for remittance in remittances]


@router.post("/acks", status_code=status.HTTP_201_CREATED)
def import_ack(
    payload: AckCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    ack = ClearinghouseAck(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(ack, request)
    db.add(ack)
    db.commit()
    db.refresh(ack)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="clearinghouse_ack",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(ack),
        event_type="billing.ack.imported",
        event_payload={"ack_id": ack.id},
    )
    return ack


@router.get("/acks")
def list_acks(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, ClearinghouseAck, user.org_id, request.state.training_mode).order_by(
        ClearinghouseAck.created_at.desc()
    )


@router.post("/eligibility/270", status_code=status.HTTP_201_CREATED)
def check_eligibility(
    payload: EligibilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = EligibilityCheck(org_id=user.org_id, **payload.model_dump(), status="checked")
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="eligibility_check",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.eligibility.checked",
        event_payload={"eligibility_id": record.id},
    )
    return record


@router.get("/eligibility/270")
def list_eligibility(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, EligibilityCheck, user.org_id, request.state.training_mode).order_by(
        EligibilityCheck.created_at.desc()
    )


@router.post("/claim-status/276", status_code=status.HTTP_201_CREATED)
def claim_status(
    payload: ClaimStatusCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = ClaimStatusInquiry(org_id=user.org_id, **payload.model_dump(), status="received")
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="claim_status_inquiry",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.claim_status.created",
        event_payload={"claim_status_id": record.id},
    )
    return record


@router.get("/claim-status/276")
def list_claim_status(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, ClaimStatusInquiry, user.org_id, request.state.training_mode).order_by(
        ClaimStatusInquiry.created_at.desc()
    )


@router.post("/statements", status_code=status.HTTP_201_CREATED)
def create_statement(
    payload: StatementCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = PatientStatement(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_statement",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.statement.created",
        event_payload={"statement_id": record.id},
    )
    return record


@router.get("/statements")
def list_statements(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, PatientStatement, user.org_id, request.state.training_mode).order_by(
        PatientStatement.created_at.desc()
    )


@router.post("/payments", status_code=status.HTTP_201_CREATED)
def post_payment(
    payload: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = PaymentPosting(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="payment_posting",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.payment.posted",
        event_payload={"payment_id": record.id},
    )
    return record


@router.get("/payments")
def list_payments(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, PaymentPosting, user.org_id, request.state.training_mode).order_by(
        PaymentPosting.created_at.desc()
    )


@router.post("/appeals", status_code=status.HTTP_201_CREATED)
def create_appeal(
    payload: AppealCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    record = AppealPacket(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="appeal_packet",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="billing.appeal.created",
        event_payload={"appeal_id": record.id},
    )
    return record


@router.get("/appeals")
def list_appeals(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, AppealPacket, user.org_id, request.state.training_mode).order_by(
        AppealPacket.created_at.desc()
    )


@router.post("/office-ally/submit")
def submit_claims(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    if request.state.training_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TRAINING_MODE_EXPORT_BLOCKED",
        )
    enforce_legal_hold(db, user.org_id, "billing_export", "office-ally", "export")
    if not settings.OFFICEALLY_FTP_HOST:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Office Ally FTP not configured",
        )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="export",
        resource="billing_office_ally",
        classification="BILLING_SENSITIVE",
        event_type="billing.office_ally.submitted",
        event_payload={"provider": "Office Ally"},
    )
    return {"status": "queued", "provider": "Office Ally"}


@router.post("/business-ops/tasks", status_code=status.HTTP_201_CREATED)
def create_business_task(
    payload: BusinessOpsCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    task = BusinessOpsTask(
        **payload.model_dump(exclude={"metadata"}),
        task_metadata=payload.metadata,
        org_id=user.org_id,
    )
    apply_training_mode(task, request)
    db.add(task)
    db.commit()
    db.refresh(task)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="business_ops_task",
        classification=task.classification,
        after_state=model_snapshot(task),
        event_type="billing.business_ops_task.created",
        event_payload={"task_id": task.id},
    )
    return task
