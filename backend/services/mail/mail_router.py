from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.mail import Message
from models.user import User, UserRole
from utils.logger import logger
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from utils.tenancy import scoped_query


router = APIRouter(
    prefix="/api/mail",
    tags=["Mail"],
    dependencies=[Depends(require_module("COMMS"))],
)


class MessageCreate(BaseModel):
    channel: str
    recipient: str
    subject: str | None = None
    body: str
    media_url: str | None = None


def _send_telnyx_message(payload: MessageCreate) -> str:
    try:
        import telnyx
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Telnyx SDK not installed",
        ) from exc

    telnyx.api_key = settings.TELNYX_API_KEY
    channel = payload.channel.lower()

    if channel == "sms":
        response = telnyx.Message.create(
            from_=settings.TELNYX_NUMBER,
            to=payload.recipient,
            text=payload.body,
            messaging_profile_id=settings.TELNYX_MESSAGING_PROFILE_ID or None,
        )
        return response.id
    if channel in {"voice", "call"}:
        response = telnyx.Call.create(
            connection_id=settings.TELNYX_CONNECTION_ID,
            to=payload.recipient,
            from_=settings.TELNYX_NUMBER,
        )
        return response.id
    if channel == "fax":
        if not payload.media_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fax requires media_url",
            )
        response = telnyx.Fax.create(
            connection_id=settings.TELNYX_CONNECTION_ID,
            to=payload.recipient,
            from_=settings.TELNYX_NUMBER,
            media_url=payload.media_url,
        )
        return response.id

    return "unsupported"


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(
    payload: MessageCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    if payload.channel.lower() in {"sms", "fax", "voice", "call"} and not settings.TELNYX_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Telnyx API key not configured",
        )
    message = Message(**payload.model_dump(exclude={"media_url"}), org_id=user.org_id)
    apply_training_mode(message, request)
    if payload.channel.lower() in {"sms", "fax", "voice", "call"}:
        try:
            telnyx_id = _send_telnyx_message(payload)
            message.status = f"Sent:{telnyx_id}"
        except HTTPException:
            message.status = "Failed"
            raise
        except Exception as exc:
            logger.warning("Telnyx send failed: %s", exc)
            message.status = "Failed"
    db.add(message)
    db.commit()
    db.refresh(message)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="mail_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="mail.message.created",
        event_payload={"message_id": message.id},
    )
    return message


@router.get("/messages")
def list_messages(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(db, Message, user.org_id, request.state.training_mode).order_by(
        Message.created_at.desc()
    ).all()
