from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.patient_portal import PatientPortalAccount, PatientPortalMessage
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/patient-portal", tags=["Patient Portal"])


class AccountCreate(BaseModel):
    patient_name: str
    email: str = ""
    status: str = "active"
    preferences: dict = {}


class MessageCreate(BaseModel):
    account_id: int
    sender: str = "patient"
    message: str
    payload: dict = {}


@router.get("/accounts")
def list_accounts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder)),
):
    accounts = (
        scoped_query(db, PatientPortalAccount, user.org_id, request.state.training_mode)
        .order_by(PatientPortalAccount.created_at.desc())
        .all()
    )
    return [model_snapshot(account) for account in accounts]


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder)),
):
    record = PatientPortalAccount(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_portal_account",
        classification="PHI",
        after_state=model_snapshot(record),
        event_type="patient_portal.account.created",
        event_payload={"account_id": record.id},
    )
    return model_snapshot(record)


@router.get("/messages")
def list_messages(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.founder)),
):
    messages = (
        scoped_query(db, PatientPortalMessage, user.org_id, request.state.training_mode)
        .order_by(PatientPortalMessage.created_at.desc())
        .all()
    )
    return [model_snapshot(message) for message in messages]


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(
    payload: MessageCreate,
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not found")
    record = PatientPortalMessage(org_id=user.org_id, **payload.dict())
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="patient_portal_message",
        classification="PHI",
        after_state=model_snapshot(record),
        event_type="patient_portal.message.created",
        event_payload={"message_id": record.id, "account_id": account.id},
    )
    return model_snapshot(record)
