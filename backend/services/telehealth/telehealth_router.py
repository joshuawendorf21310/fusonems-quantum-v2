from datetime import datetime
from uuid import uuid4
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal, get_db, get_telehealth_db
from core.security import require_roles
from models.business_ops import BusinessOpsTask
from models.telehealth import TelehealthMessage, TelehealthParticipant, TelehealthSession
from models.user import UserRole

router = APIRouter(prefix="/api/telehealth", tags=["Telehealth"])


class SessionCreate(BaseModel):
    title: str
    host_name: str


class SessionResponse(BaseModel):
    session_uuid: str
    title: str
    host_name: str
    access_code: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None

    class Config:
        from_attributes = True


class ParticipantCreate(BaseModel):
    name: str
    role: str = "patient"


class MessageCreate(BaseModel):
    sender: str
    message: str


def _log_alert(db: Session, session_uuid: str, message: str) -> None:
    alert = TelehealthMessage(session_uuid=session_uuid, sender="system", message=message)
    db.add(alert)
    db.commit()


def _create_integration_task(session_uuid: str, title: str, integration: str) -> None:
    try:
        db = SessionLocal()
        task = BusinessOpsTask(
            title=title,
            owner="CareFusion Telemed",
            priority="Normal",
            task_metadata={"session_uuid": session_uuid, "integration": integration},
        )
        db.add(task)
        db.commit()
    except Exception:
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_telehealth_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = TelehealthSession(
        session_uuid=str(uuid4()),
        title=payload.title,
        host_name=payload.host_name,
        access_code=str(secrets.randbelow(900000) + 100000),
        session_secret=secrets.token_hex(16),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    _log_alert(db, session.session_uuid, "Session created")
    _create_integration_task(session.session_uuid, "Telehealth session created", "carefusion")
    _create_integration_task(session.session_uuid, "Office Ally sync queued", "office-ally")
    return session


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_telehealth_db)):
    return db.query(TelehealthSession).order_by(TelehealthSession.created_at.desc()).all()


@router.get("/sessions/{session_uuid}", response_model=SessionResponse)
def get_session(session_uuid: str, db: Session = Depends(get_telehealth_db)):
    session = db.query(TelehealthSession).filter(TelehealthSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("/sessions/{session_uuid}/participants", status_code=status.HTTP_201_CREATED)
def add_participant(
    session_uuid: str,
    payload: ParticipantCreate,
    db: Session = Depends(get_telehealth_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = db.query(TelehealthSession).filter(TelehealthSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    participant = TelehealthParticipant(
        session_uuid=session_uuid, name=payload.name, role=payload.role
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@router.post("/sessions/{session_uuid}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    session_uuid: str,
    payload: MessageCreate,
    db: Session = Depends(get_telehealth_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = db.query(TelehealthSession).filter(TelehealthSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    message = TelehealthMessage(
        session_uuid=session_uuid, sender=payload.sender, message=payload.message
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/sessions/{session_uuid}/messages")
def list_messages(session_uuid: str, db: Session = Depends(get_telehealth_db)):
    return (
        db.query(TelehealthMessage)
        .filter(TelehealthMessage.session_uuid == session_uuid)
        .order_by(TelehealthMessage.created_at.asc())
        .all()
    )


@router.post("/sessions/{session_uuid}/start")
def start_session(
    session_uuid: str,
    db: Session = Depends(get_telehealth_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = db.query(TelehealthSession).filter(TelehealthSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.status = "Live"
    session.started_at = datetime.utcnow()
    db.commit()
    _log_alert(db, session_uuid, "Session started")
    return {"status": "started", "session_uuid": session_uuid}


@router.post("/sessions/{session_uuid}/end")
def end_session(
    session_uuid: str,
    db: Session = Depends(get_telehealth_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = db.query(TelehealthSession).filter(TelehealthSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.status = "Ended"
    session.ended_at = datetime.utcnow()
    db.commit()
    _log_alert(db, session_uuid, "Session ended")
    _create_integration_task(session_uuid, "Telehealth session closed", "carefusion")
    _create_integration_task(session_uuid, "Office Ally sync queued", "office-ally")
    return {"status": "ended", "session_uuid": session_uuid}


@router.get("/sessions/{session_uuid}/webrtc")
def get_webrtc_config(session_uuid: str):
    return {
        "session_uuid": session_uuid,
        "provider": "webrtc",
        "room_id": session_uuid,
        "access_code": "internal",
        "features": {
            "screen_share": True,
            "chat": True,
            "recording": True,
            "multi_party": True,
        },
    }
