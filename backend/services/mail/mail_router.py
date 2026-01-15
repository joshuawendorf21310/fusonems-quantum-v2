from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import require_roles
from models.mail import Message
from models.user import UserRole


router = APIRouter(prefix="/api/mail", tags=["Mail"])


class MessageCreate(BaseModel):
    channel: str
    recipient: str
    subject: str | None = None
    body: str


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    if payload.channel.lower() in {"sms", "fax"} and not settings.TELNYX_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Telnyx API key not configured",
        )
    message = Message(**payload.dict())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/messages")
def list_messages(db: Session = Depends(get_db)):
    return db.query(Message).order_by(Message.created_at.desc()).all()
