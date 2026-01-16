from datetime import datetime
from uuid import uuid4
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal, get_db, get_telehealth_db
from core.guards import require_module
from core.security import require_roles
from models.business_ops import BusinessOpsTask
from models.consent import ConsentProvenance
from models.telehealth import TelehealthMessage, TelehealthParticipant, TelehealthSession
from models.user import User, UserRole
from utils.tenancy import get_scoped_record, scoped_query
from utils.legal import enforce_legal_hold
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/telehealth",
    tags=["Telehealth"],
    dependencies=[Depends(require_module("TELEHEALTH"))],
)


class SessionCreate(BaseModel):
    title: str
    host_name: str
    consent_captured: bool = True
    consent_context: str = "telehealth_intake"
    policy_hash: str = ""
    modality: str = "video"
    recording_enabled: bool = True
    consent_required: bool = True


class SessionResponse(BaseModel):
    session_uuid: str
    title: str
    host_name: str
    access_code: str
    status: str
    modality: str
    recording_enabled: bool
    consent_required: bool
    consent_captured_at: datetime | None
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


def _log_alert(db: Session, session_uuid: str, message: str, org_id: int) -> None:
    alert = TelehealthMessage(
        session_uuid=session_uuid, sender="system", message=message, org_id=org_id
    )
    db.add(alert)
    db.commit()


def _create_integration_task(session_uuid: str, title: str, integration: str, org_id: int) -> None:
    try:
        db = SessionLocal()
        task = BusinessOpsTask(
            title=title,
            owner="CareFusion Telemed",
            priority="Normal",
            task_metadata={"session_uuid": session_uuid, "integration": integration},
            org_id=org_id,
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
    request: Request,
    db: Session = Depends(get_telehealth_db),
    primary_db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = TelehealthSession(
        org_id=user.org_id,
        session_uuid=str(uuid4()),
        title=payload.title,
        host_name=payload.host_name,
        access_code=str(secrets.randbelow(900000) + 100000),
        session_secret=secrets.token_hex(16),
        modality=payload.modality,
        recording_enabled=payload.recording_enabled,
        consent_required=payload.consent_required,
    )
    apply_training_mode(session, request)
    db.add(session)
    db.commit()
    db.refresh(session)
    _log_alert(db, session.session_uuid, "Session created", user.org_id)
    _create_integration_task(
        session.session_uuid, "Telehealth session created", "carefusion", user.org_id
    )
    _create_integration_task(
        session.session_uuid, "Office Ally sync queued", "office-ally", user.org_id
    )
    if payload.consent_captured:
        consent = ConsentProvenance(
            org_id=user.org_id,
            subject_type="telehealth_session",
            subject_id=session.session_uuid,
            policy_hash=payload.policy_hash,
            context=payload.consent_context,
            metadata_json={"title": session.title, "host_name": session.host_name},
            captured_by=user.email,
            device_id=request.headers.get("x-device-id", "") if request else "",
        )
        apply_training_mode(consent, request)
        primary_db.add(consent)
        primary_db.commit()
        session.consent_captured_at = datetime.utcnow()
        db.commit()
        audit_and_event(
            db=primary_db,
            request=request,
            user=user,
            action="create",
            resource="consent_provenance",
            classification=consent.classification,
            after_state=model_snapshot(consent),
            event_type="telehealth.consent.created",
            event_payload={"consent_id": consent.id},
        )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_session",
        classification=session.classification,
        after_state=model_snapshot(session),
        event_type="telehealth.session.created",
        event_payload={"session_uuid": session.session_uuid},
    )
    return session


@router.post("/sessions/{session_uuid}/consent")
def capture_consent(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    primary_db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    consent = ConsentProvenance(
        org_id=user.org_id,
        subject_type="telehealth_session",
        subject_id=session.session_uuid,
        policy_hash="telehealth-standard",
        context="telehealth_consent",
        metadata_json={"title": session.title, "host_name": session.host_name},
        captured_by=user.email,
        device_id=request.headers.get("x-device-id", "") if request else "",
    )
    apply_training_mode(consent, request)
    primary_db.add(consent)
    primary_db.commit()
    session.consent_captured_at = datetime.utcnow()
    db.commit()
    audit_and_event(
        db=primary_db,
        request=request,
        user=user,
        action="create",
        resource="consent_provenance",
        classification=consent.classification,
        after_state=model_snapshot(consent),
        event_type="telehealth.consent.created",
        event_payload={"consent_id": consent.id},
    )
    return {"status": "ok", "session_uuid": session_uuid}


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(
        db, TelehealthSession, user.org_id, request.state.training_mode
    ).order_by(TelehealthSession.created_at.desc()).all()


@router.get("/sessions/{session_uuid}", response_model=SessionResponse)
def get_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles()),
):
    return get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )


@router.post("/sessions/{session_uuid}/participants", status_code=status.HTTP_201_CREATED)
def add_participant(
    session_uuid: str,
    payload: ParticipantCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    participant = TelehealthParticipant(
        session_uuid=session_uuid, name=payload.name, role=payload.role, org_id=session.org_id
    )
    apply_training_mode(participant, request)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_participant",
        classification=participant.classification,
        after_state=model_snapshot(participant),
        event_type="telehealth.participant.added",
        event_payload={"participant_id": participant.id},
    )
    return participant


@router.post("/sessions/{session_uuid}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    session_uuid: str,
    payload: MessageCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    message = TelehealthMessage(
        session_uuid=session_uuid,
        sender=payload.sender,
        message=payload.message,
        org_id=session.org_id,
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="telehealth_message",
        classification=message.classification,
        after_state=model_snapshot(message),
        event_type="telehealth.message.created",
        event_payload={"message_id": message.id},
    )
    return message


@router.get("/sessions/{session_uuid}/messages")
def list_messages(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles()),
):
    return (
        scoped_query(db, TelehealthMessage, user.org_id, request.state.training_mode)
        .filter(TelehealthMessage.session_uuid == session_uuid)
        .order_by(TelehealthMessage.created_at.asc())
        .all()
    )


@router.post("/sessions/{session_uuid}/start")
def start_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    if session.consent_required and not session.consent_captured_at:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Consent required")
    enforce_legal_hold(db, user.org_id, "telehealth_session", session.session_uuid, "update")
    before = model_snapshot(session)
    session.status = "Live"
    session.started_at = datetime.utcnow()
    db.commit()
    _log_alert(db, session_uuid, "Session started", session.org_id)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="telehealth_session",
        classification=session.classification,
        before_state=before,
        after_state=model_snapshot(session),
        event_type="telehealth.session.started",
        event_payload={"session_uuid": session.session_uuid, "status": session.status},
    )
    return {"status": "started", "session_uuid": session_uuid}


@router.post("/sessions/{session_uuid}/end")
def end_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    enforce_legal_hold(db, user.org_id, "telehealth_session", session.session_uuid, "update")
    before = model_snapshot(session)
    session.status = "Ended"
    session.ended_at = datetime.utcnow()
    db.commit()
    _log_alert(db, session_uuid, "Session ended", session.org_id)
    _create_integration_task(
        session_uuid, "Telehealth session closed", "carefusion", session.org_id
    )
    _create_integration_task(
        session_uuid, "Office Ally sync queued", "office-ally", session.org_id
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="telehealth_session",
        classification=session.classification,
        before_state=before,
        after_state=model_snapshot(session),
        event_type="telehealth.session.ended",
        event_payload={"session_uuid": session.session_uuid, "status": session.status},
    )
    return {"status": "ended", "session_uuid": session_uuid}


@router.get("/sessions/{session_uuid}/webrtc")
def get_webrtc_config(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles()),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    token = secrets.token_hex(16)
    return {
        "session_uuid": session_uuid,
        "provider": "webrtc",
        "room_id": session_uuid,
        "access_code": "internal",
        "token": token,
        "ice_servers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
        ],
        "features": {
            "screen_share": True,
            "chat": True,
            "recording": session.recording_enabled,
            "multi_party": True,
        },
        "status": session.status,
    }


@router.get("/sessions/{session_uuid}/secure-token")
def get_secure_token(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles()),
):
    session = get_scoped_record(
        db,
        request,
        TelehealthSession,
        session_uuid,
        user,
        id_field="session_uuid",
        resource_label="telehealth",
    )
    return {
        "session_uuid": session_uuid,
        "token": secrets.token_hex(16),
        "encryption_state": session.encryption_state,
        "modality": session.modality,
    }
