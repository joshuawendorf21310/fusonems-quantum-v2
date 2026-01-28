from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
import os

from core.database import get_db
from core.security import require_roles
from models.patient_portal import (
    PatientPortalAccount,
    PatientBill,
    PatientPayment,
    PatientPaymentPlan,
    StripeCustomer,
)
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/patient-portal", tags=["Patient Billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class BillCreate(BaseModel):
    account_id: int
    bill_number: str
    transport_date: datetime
    service_type: str
    pickup_address: str = ""
    dropoff_address: str = ""
    amount_total: Decimal
    amount_insurance: Decimal = Decimal("0")
    amount_patient: Decimal
    amount_due: Decimal
    due_date: Optional[datetime] = None
    notes: str = ""
    metadata: dict = {}


class PaymentIntentCreate(BaseModel):
    bill_id: int
    amount: Decimal


class PaymentPlanCreate(BaseModel):
    bill_id: int
    installment_amount: Decimal
    frequency: str = "monthly"
    start_date: datetime
    auto_pay_enabled: bool = False


class ProfileUpdate(BaseModel):
    patient_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


@router.get("/bills")
def list_bills(
    request: Request,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    query = scoped_query(db, PatientBill, user.org_id, request.state.training_mode)
    if account_id:
        query = query.filter(PatientBill.account_id == account_id)
    bills = query.order_by(PatientBill.transport_date.desc()).all()
    return [model_snapshot(bill) for bill in bills]


@router.get("/bills/{bill_id}")
def get_bill(
    bill_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    bill = (
        scoped_query(db, PatientBill, user.org_id, request.state.training_mode)
        .filter(PatientBill.id == bill_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return model_snapshot(bill)


@router.post("/bills", status_code=status.HTTP_201_CREATED)
def create_bill(
    payload: BillCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder)),
):
    account = (
        scoped_query(db, PatientPortalAccount, user.org_id, request.state.training_mode)
        .filter(PatientPortalAccount.id == payload.account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    record = PatientBill(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_bill",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(record),
        event_type="patient_portal.bill.created",
        event_payload={"bill_id": record.id, "account_id": account.id},
    )
    return model_snapshot(record)


@router.get("/payments")
def list_payments(
    request: Request,
    account_id: Optional[int] = None,
    bill_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    query = scoped_query(db, PatientPayment, user.org_id, request.state.training_mode)
    if account_id:
        query = query.filter(PatientPayment.account_id == account_id)
    if bill_id:
        query = query.filter(PatientPayment.bill_id == bill_id)
    payments = query.order_by(PatientPayment.created_at.desc()).all()
    return [model_snapshot(payment) for payment in payments]


@router.post("/create-payment-intent", status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payload: PaymentIntentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    bill = (
        scoped_query(db, PatientBill, user.org_id, request.state.training_mode)
        .filter(PatientBill.id == payload.bill_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    account = (
        scoped_query(db, PatientPortalAccount, user.org_id, request.state.training_mode)
        .filter(PatientPortalAccount.id == bill.account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    stripe_customer = (
        scoped_query(db, StripeCustomer, user.org_id, request.state.training_mode)
        .filter(StripeCustomer.account_id == account.id)
        .first()
    )
    
    if not stripe_customer:
        customer = stripe.Customer.create(
            email=account.email,
            name=account.patient_name,
            metadata={"org_id": user.org_id, "account_id": account.id},
        )
        stripe_customer = StripeCustomer(
            org_id=user.org_id,
            account_id=account.id,
            stripe_customer_id=customer.id,
            email=account.email,
            name=account.patient_name,
        )
        apply_training_mode(stripe_customer, request)
        db.add(stripe_customer)
        db.commit()
        db.refresh(stripe_customer)
    
    amount_cents = int(float(payload.amount) * 100)
    
    payment_intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        customer=stripe_customer.stripe_customer_id,
        metadata={
            "org_id": user.org_id,
            "bill_id": bill.id,
            "account_id": account.id,
            "bill_number": bill.bill_number,
        },
        automatic_payment_methods={"enabled": True},
    )
    
    import uuid
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    
    payment_record = PatientPayment(
        org_id=user.org_id,
        account_id=account.id,
        bill_id=bill.id,
        payment_id=payment_id,
        stripe_payment_intent_id=payment_intent.id,
        amount=payload.amount,
        status="pending",
    )
    apply_training_mode(payment_record, request)
    db.add(payment_record)
    db.commit()
    db.refresh(payment_record)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_payment",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(payment_record),
        event_type="patient_portal.payment.initiated",
        event_payload={
            "payment_id": payment_record.id,
            "bill_id": bill.id,
            "amount": str(payload.amount),
        },
    )
    
    return {
        "client_secret": payment_intent.client_secret,
        "payment_id": payment_record.id,
        "payment_intent_id": payment_intent.id,
    }


@router.post("/payment-plans", status_code=status.HTTP_201_CREATED)
def create_payment_plan(
    payload: PaymentPlanCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    bill = (
        scoped_query(db, PatientBill, user.org_id, request.state.training_mode)
        .filter(PatientBill.id == payload.bill_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    import uuid
    plan_id = f"PLAN-{uuid.uuid4().hex[:12].upper()}"
    
    plan = PatientPaymentPlan(
        org_id=user.org_id,
        account_id=bill.account_id,
        bill_id=bill.id,
        plan_id=plan_id,
        total_amount=bill.amount_due,
        amount_remaining=bill.amount_due,
        installment_amount=payload.installment_amount,
        frequency=payload.frequency,
        start_date=payload.start_date,
        next_payment_date=payload.start_date,
        auto_pay_enabled=payload.auto_pay_enabled,
    )
    apply_training_mode(plan, request)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_payment_plan",
        classification="BILLING_SENSITIVE",
        after_state=model_snapshot(plan),
        event_type="patient_portal.payment_plan.created",
        event_payload={"plan_id": plan.id, "bill_id": bill.id},
    )
    return model_snapshot(plan)


@router.get("/payment-plans")
def list_payment_plans(
    request: Request,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    query = scoped_query(db, PatientPaymentPlan, user.org_id, request.state.training_mode)
    if account_id:
        query = query.filter(PatientPaymentPlan.account_id == account_id)
    plans = query.order_by(PatientPaymentPlan.created_at.desc()).all()
    return [model_snapshot(plan) for plan in plans]


@router.get("/profile/{account_id}")
def get_profile(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    account = (
        scoped_query(db, PatientPortalAccount, user.org_id, request.state.training_mode)
        .filter(PatientPortalAccount.id == account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return model_snapshot(account)


@router.put("/profile/{account_id}")
def update_profile(
    account_id: int,
    payload: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder, UserRole.patient)),
):
    account = (
        scoped_query(db, PatientPortalAccount, user.org_id, request.state.training_mode)
        .filter(PatientPortalAccount.id == account_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    before_state = model_snapshot(account)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="patient_portal_account",
        classification="PHI",
        before_state=before_state,
        after_state=model_snapshot(account),
        event_type="patient_portal.profile.updated",
        event_payload={"account_id": account.id},
    )
    return model_snapshot(account)
