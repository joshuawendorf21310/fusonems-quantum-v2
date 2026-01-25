import io
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.guards import require_module
from core.security import hash_password, require_roles
from models.communications import (
    CommsBroadcast,
    CommsCallEvent,
    CommsCallLog,
    CommsMessage,
    CommsPhoneNumber,
    CommsRecording,
    CommsRingGroup,
    CommsRoutingPolicy,
    CommsTask,
    CommsThread,
    CommsTranscript,
    CommsVoicemail,
)
from models.communications_batch5 import (
    CommsDeliveryAttempt,
    CommsEvent,
    CommsProvider,
    CommsTemplate,
)
from models.quantum_documents import RetentionPolicy
from models.module_registry import ModuleRegistry
from models.organization import Organization
from models.user import User, UserRole
from utils.legal import get_active_hold
from utils.storage import get_storage_backend
from utils.tenancy import scoped_query
from utils.decision import DecisionBuilder, finalize_decision_packet, hash_payload
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/comms",
    tags=["Communications"],
    dependencies=[Depends(require_module("COMMS"))],
)
webhook_router = APIRouter(prefix="/api/comms/webhooks", tags=["Communications"])

TELNYX_EVENT_MAP = {
    "call.initiated": ("INITIATED", "comms.call.initiated"),
    "call.answered": ("ANSWERED", "comms.call.answered"),
    "call.bridged": ("BRIDGED", "comms.call.bridged"),
    "call.hangup": ("ENDED", "comms.call.hangup"),
    "call.recording.saved": ("RECORDED", "comms.call.recording.saved"),
    "call.playback.ended": ("PLAYBACK_COMPLETE", "comms.call.playback.ended"),
    "call.dtmf.received": ("DTMF", "comms.call.dtmf.received"),
}


def _redact_text(value: str) -> str:
    if not value:
        return ""
    redacted = []
    for char in value:
        if char.isdigit():
            redacted.append("*")
        else:
            redacted.append(char)
    return "".join(redacted)[:160]


def _record_event(
    db: Session,
    request: Request,
    user: User,
    thread: CommsThread,
    message: CommsMessage,
    event_type: str,
    payload: dict,
    status: str = "queued",
) -> CommsEvent:
    event = CommsEvent(
        org_id=user.org_id,
        thread_id=thread.id,
        message_id=message.id,
        event_type=event_type,
        status=status,
        payload=payload,
    )
    apply_training_mode(event, request)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _record_attempt(db: Session, event: CommsEvent, provider: str, status: str, payload: dict, error: str = "") -> None:
    attempt = CommsDeliveryAttempt(
        org_id=event.org_id,
        event_id=event.id,
        provider=provider,
        status=status,
        response_payload=payload,
        error=error,
    )
    db.add(attempt)
    db.commit()


def _send_telnyx(channel: str, recipient: str, body: str, media_url: str = "") -> str:
    if not settings.TELNYX_API_KEY:
        raise HTTPException(status_code=412, detail="Telnyx API key not configured")
    try:
        import telnyx
    except ImportError as exc:
        raise HTTPException(status_code=412, detail="Telnyx SDK not installed") from exc
    telnyx.api_key = settings.TELNYX_API_KEY
    if channel == "sms":
        response = telnyx.Message.create(
            from_=settings.TELNYX_NUMBER,
            to=recipient,
            text=body,
            messaging_profile_id=settings.TELNYX_MESSAGING_PROFILE_ID or None,
        )
        return response.id
    if channel == "fax":
        if not media_url:
            raise HTTPException(status_code=422, detail="Fax requires media_url")
        response = telnyx.Fax.create(
            connection_id=settings.TELNYX_CONNECTION_ID,
            to=recipient,
            from_=settings.TELNYX_NUMBER,
            media_url=media_url,
        )
        return response.id
    if channel == "voice":
        response = telnyx.Call.create(
            connection_id=settings.TELNYX_CONNECTION_ID,
            to=recipient,
            from_=settings.TELNYX_NUMBER,
        )
        return response.id
    raise HTTPException(status_code=422, detail="Unsupported channel")


def _parse_occurred_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _verify_telnyx_signature(raw_body: bytes, request: Request) -> None:
    if not settings.TELNYX_REQUIRE_SIGNATURE:
        return
    signature = request.headers.get("telnyx-signature-ed25519")
    timestamp = request.headers.get("telnyx-timestamp")
    if not signature or not timestamp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telnyx signature")
    if not settings.TELNYX_PUBLIC_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telnyx public key")
    try:
        from nacl.encoding import Base64Encoder
        from nacl.signing import VerifyKey

        verify_key = VerifyKey(settings.TELNYX_PUBLIC_KEY, encoder=Base64Encoder)
        signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
        verify_key.verify(signed_payload, Base64Encoder.decode(signature))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Telnyx signature: {exc}") from exc


@router.get("/health")
def comms_health():
    configured = bool(settings.TELNYX_API_KEY and settings.TELNYX_NUMBER)
    response = {
        "configured": configured,
        "telnyx_number": settings.TELNYX_NUMBER or None,
        "probe": "skipped",
    }
    if not configured:
        response["status"] = "missing_credentials"
        return response
    try:
        import telnyx

        telnyx.api_key = settings.TELNYX_API_KEY
        balance = telnyx.Balance.retrieve()
        response["status"] = "ok"
        response["probe"] = "telnyx_balance"
        response["balance"] = getattr(balance, "available_credit", None)
    except Exception as exc:  # noqa: BLE001 - surface status for ops
        response["status"] = "error"
        response["probe"] = "telnyx_balance"
        response["error"] = str(exc)
    return response


def _get_system_user(db: Session, org_id: int) -> User:
    user = (
        db.query(User)
        .filter(User.org_id == org_id, User.email == "system@fusonems.local")
        .first()
    )
    if user:
        return user
    user = User(
        org_id=org_id,
        email="system@fusonems.local",
        full_name="System Integration",
        hashed_password=hash_password("system"),
        role=UserRole.admin.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _resolve_org(db: Session, payload: dict) -> Organization | None:
    org_id = payload.get("org_id")
    if not org_id:
        metadata = payload.get("metadata") or {}
        org_id = metadata.get("org_id")
    if org_id:
        return db.query(Organization).filter(Organization.id == org_id).first()
    return db.query(Organization).order_by(Organization.id.asc()).first()


def _module_enabled(db: Session, org_id: int) -> bool:
    module = (
        db.query(ModuleRegistry)
        .filter(ModuleRegistry.org_id == org_id, ModuleRegistry.module_key == "COMMS")
        .first()
    )
    return bool(module and module.enabled and not module.kill_switch)


async def _handle_telnyx_event(body: dict, request: Request, db: Session) -> dict:
    data = body.get("data") or {}
    payload = data.get("payload") or body.get("payload") or {}
    event_type = data.get("event_type") or body.get("event_type") or "unknown"
    call_state, canonical_event = TELNYX_EVENT_MAP.get(event_type, ("UNKNOWN", "comms.call.unknown"))

    org = _resolve_org(db, payload)
    if not org:
        return {"status": "no_org"}
    if not _module_enabled(db, org.id):
        return {"status": "module_disabled"}

    caller = payload.get("from") or payload.get("caller") or payload.get("from_number") or ""
    recipient = payload.get("to") or payload.get("recipient") or payload.get("to_number") or ""
    duration = payload.get("duration") or payload.get("duration_seconds") or 0
    recording_url = payload.get("recording_url") or ""
    disposition = payload.get("hangup_cause") or event_type
    external_call_id = (
        payload.get("call_control_id")
        or payload.get("call_leg_id")
        or payload.get("call_session_id")
        or ""
    )
    dtmf_digits = payload.get("digits") or payload.get("dtmf") or ""
    provider_event_id = data.get("id") or payload.get("event_id") or ""
    occurred_at = _parse_occurred_at(data.get("occurred_at") or payload.get("occurred_at"))

    log = None
    if external_call_id:
        log = (
            db.query(CommsCallLog)
            .filter(
                CommsCallLog.org_id == org.id,
                CommsCallLog.external_call_id == external_call_id,
            )
            .first()
        )
    created = False
    if not log:
        log = CommsCallLog(
            org_id=org.id,
            caller=caller,
            recipient=recipient,
            direction=payload.get("direction", "inbound"),
            duration_seconds=duration or 0,
            recording_url=recording_url,
            disposition=disposition,
            call_state=call_state,
            external_call_id=external_call_id,
            last_event=event_type,
            dtmf_digits=dtmf_digits,
            payload=body,
        )
        apply_training_mode(log, request)
        db.add(log)
        created = True
    else:
        log.duration_seconds = duration or log.duration_seconds
        log.recording_url = recording_url or log.recording_url
        log.disposition = disposition or log.disposition
        log.call_state = call_state
        log.last_event = event_type
        if dtmf_digits:
            log.dtmf_digits = f"{log.dtmf_digits}{dtmf_digits}"
        log.payload = body
    db.commit()
    db.refresh(log)

    system_user = _get_system_user(db, org.id)

    existing_event = None
    if provider_event_id:
        existing_event = (
            db.query(CommsCallEvent)
            .filter(
                CommsCallEvent.org_id == org.id,
                CommsCallEvent.provider_event_id == provider_event_id,
            )
            .first()
        )
    if not existing_event:
        existing_event = (
            db.query(CommsCallEvent)
            .filter(
                CommsCallEvent.org_id == org.id,
                CommsCallEvent.external_call_id == external_call_id,
                CommsCallEvent.event_type == event_type,
                CommsCallEvent.occurred_at == occurred_at,
            )
            .first()
        )

    if not existing_event:
        call_event = CommsCallEvent(
            org_id=org.id,
            call_id=log.id,
            external_call_id=external_call_id,
            event_type=event_type,
            provider_event_id=provider_event_id,
            occurred_at=occurred_at,
            payload=body,
        )
        apply_training_mode(call_event, request)
        db.add(call_event)
        db.commit()

    if event_type == "call.answered" and occurred_at:
        log.answered_at = occurred_at
    if event_type == "call.hangup" and occurred_at:
        log.ended_at = occurred_at
    db.commit()

    if event_type in {"call.recording.saved", "recording.available"} and recording_url:
        policy_key = "comms_billing" if log.classification == "billing" else "comms_ops"
        policy = (
            db.query(RetentionPolicy)
            .filter(RetentionPolicy.org_id == org.id, RetentionPolicy.applies_to == policy_key)
            .first()
        )
        recording = CommsRecording(
            org_id=org.id,
            call_id=log.id,
            provider_recording_id=payload.get("recording_id", ""),
            recording_url=recording_url,
            retention_policy_id=policy.id if policy else None,
        )
        apply_training_mode(recording, request)
        db.add(recording)
        db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=system_user,
        action="create" if created else "update",
        resource="comms_call",
        classification="PHI",
        after_state=model_snapshot(log),
        event_type=canonical_event,
        event_payload={
            "call_id": log.id,
            "event_type": event_type,
            "call_state": call_state,
            "external_call_id": external_call_id,
        },
    )
    return {"status": "ok"}


@webhook_router.post("/telnyx")
async def telnyx_inbound_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    _verify_telnyx_signature(raw_body, request)
    body = json.loads(raw_body.decode("utf-8") or "{}")
    return await _handle_telnyx_event(body, request, db)


@webhook_router.post("/telnyx/test")
async def telnyx_test_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    return await _handle_telnyx_event(body, request, db)


class ThreadCreate(BaseModel):
    channel: str = "sms"
    subject: str = ""
    priority: str = "Normal"
    status: str = "open"
    linked_resource: str = ""
    participants: list[str] = []


class MessageCreate(BaseModel):
    thread_id: int
    sender: str
    body: str
    media_url: str = ""
    tags: list[str] = []


class CallLogCreate(BaseModel):
    caller: str
    recipient: str
    direction: str = "outbound"
    duration_seconds: int = 0
    recording_url: str = ""
    disposition: str = "unknown"
    thread_id: Optional[int] = None


class BroadcastCreate(BaseModel):
    title: str
    message: str
    target: str = "all"
    status: str = "draft"
    expires_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    thread_id: Optional[int] = None
    title: str
    owner: str = ""
    status: str = "open"
    due_at: Optional[datetime] = None


class TranscriptSegment(BaseModel):
    start_time: float
    end_time: float
    speaker: str = "unknown"
    text: str
    confidence: float = 0.0


class TranscriptCreate(BaseModel):
    transcript_text: str
    segments: list[TranscriptSegment] = []
    confidence: float = 0.0
    method_used: str = "local"


class VoicePlanRequest(BaseModel):
    message: str
    urgency: str = "informational"
    ambient_noise: float = 0.0
    allow_speaker: bool = True


class PhoneNumberCreate(BaseModel):
    e164: str
    label: str = ""
    purpose: str = "ops"
    routing_policy_id: Optional[int] = None


class RoutingPolicyCreate(BaseModel):
    name: str
    mode: str = "ring_group"
    rules: dict = {}


class RingGroupCreate(BaseModel):
    name: str
    members: list[int] = []
    strategy: str = "simultaneous"


class CallLinkCreate(BaseModel):
    linked_object_type: str
    linked_object_id: str
    classification: str = "ops"


@router.get("/threads")
def list_threads(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    threads = (
        scoped_query(db, CommsThread, user.org_id, request.state.training_mode)
        .order_by(CommsThread.created_at.desc())
        .all()
    )
    return [model_snapshot(thread) for thread in threads]


@router.post("/threads", status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: ThreadCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    thread = CommsThread(org_id=user.org_id, **payload.dict())
    apply_training_mode(thread, request)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_thread",
        classification="PHI",
        after_state=model_snapshot(thread),
        event_type="comms.thread.created",
        event_payload={"thread_id": thread.id},
    )
    return model_snapshot(thread)


@router.get("/threads/{thread_id}/messages")
def list_messages(
    thread_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    messages = (
        scoped_query(db, CommsMessage, user.org_id, request.state.training_mode)
        .filter(CommsMessage.thread_id == thread_id)
        .order_by(CommsMessage.created_at.asc())
        .all()
    )
    return [model_snapshot(message) for message in messages]


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(
    payload: MessageCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    thread = (
        scoped_query(db, CommsThread, user.org_id, request.state.training_mode)
        .filter(CommsThread.id == payload.thread_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Thread not found")
    message = CommsMessage(org_id=user.org_id, **payload.dict())
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_message",
        classification="PHI",
        after_state=model_snapshot(message),
        event_type="comms.message.created",
        event_payload={"message_id": message.id, "thread_id": thread.id},
    )
    return model_snapshot(message)


@router.get("/calls")
def list_calls(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    calls = (
        scoped_query(db, CommsCallLog, user.org_id, request.state.training_mode)
        .order_by(CommsCallLog.created_at.desc())
        .all()
    )
    return [model_snapshot(call) for call in calls]


@router.get("/calls/{call_id}")
def get_call(
    call_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = (
        scoped_query(db, CommsCallLog, user.org_id, request.state.training_mode)
        .filter(CommsCallLog.id == call_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return model_snapshot(call)


@router.get("/calls/{external_call_id}/timeline")
def call_timeline(
    external_call_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return (
        scoped_query(db, CommsCallEvent, user.org_id, request.state.training_mode)
        .filter(CommsCallEvent.external_call_id == external_call_id)
        .order_by(CommsCallEvent.occurred_at.asc())
        .all()
    )


@router.post("/calls", status_code=status.HTTP_201_CREATED)
def create_call(
    payload: CallLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    log = CommsCallLog(org_id=user.org_id, **payload.dict())
    apply_training_mode(log, request)
    db.add(log)
    db.commit()
    db.refresh(log)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_call",
        classification="PHI",
        after_state=model_snapshot(log),
        event_type="comms.call.created",
        event_payload={"call_id": log.id},
    )
    return model_snapshot(log)


@router.post("/calls/outbound", status_code=status.HTTP_201_CREATED)
def initiate_outbound_call(
    payload: CallLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = CommsCallLog(org_id=user.org_id, **payload.dict())
    call.call_state = "INITIATED"
    apply_training_mode(call, request)
    db.add(call)
    db.commit()
    db.refresh(call)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_call",
        classification="PHI",
        after_state=model_snapshot(call),
        event_type="comms.call.initiated",
        event_payload={"call_id": call.id},
    )
    return model_snapshot(call)


@router.post("/calls/{call_id}/link")
def link_call(
    call_id: int,
    payload: CallLinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    call = (
        scoped_query(db, CommsCallLog, user.org_id, request.state.training_mode)
        .filter(CommsCallLog.id == call_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    before = model_snapshot(call)
    call.linked_object_type = payload.linked_object_type
    call.linked_object_id = payload.linked_object_id
    call.classification = payload.classification
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="comms_call",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(call),
        event_type="comms.call.linked",
        event_payload={"call_id": call.id},
    )
    return model_snapshot(call)


@router.get("/calls/{call_id}/recordings")
def list_call_recordings(
    call_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.billing)),
):
    recordings = (
        scoped_query(db, CommsRecording, user.org_id, request.state.training_mode)
        .filter(CommsRecording.call_id == call_id)
        .order_by(CommsRecording.created_at.desc())
        .all()
    )
    return [model_snapshot(recording) for recording in recordings]


@router.post("/calls/{call_id}/transcript", status_code=status.HTTP_201_CREATED)
def create_transcript(
    call_id: int,
    payload: TranscriptCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.billing)),
):
    call = (
        scoped_query(db, CommsCallLog, user.org_id, request.state.training_mode)
        .filter(CommsCallLog.id == call_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    builder = DecisionBuilder(component="comms_transcript", component_version="v1")
    hold = get_active_hold(db, user.org_id, "comms_call", str(call.id))
    if hold:
        builder.add_reason(
            "COMMS.LEGAL_HOLD.BLOCK_TRANSCRIPT.v1",
            "Legal hold blocks transcript modification.",
            severity="High",
            decision="BLOCK",
        )
        decision = finalize_decision_packet(
            db=db,
            request=request,
            user=user,
            builder=builder,
            input_payload={"call_id": call.id},
            classification="PHI",
            action="comms_transcript",
            resource="comms_call",
            reason_code="SMART_POLICY",
        )
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    evidence_hash = hash_payload(
        {
            "transcript_text": payload.transcript_text,
            "segments": [segment.dict() for segment in payload.segments],
            "confidence": payload.confidence,
        }
    )
    evidence_ref = builder.add_evidence(
        "transcript",
        f"call:{call.id}",
        {"evidence_hash": evidence_hash},
    )
    if payload.confidence < 0.75:
        builder.add_reason(
            "COMMS.TRANSCRIPT.CONFIDENCE.WARN.v1",
            "Transcript confidence is below threshold.",
            severity="Medium",
            decision="REQUIRE_CONFIRMATION",
            evidence_refs=[evidence_ref],
        )
    if not builder.reasons:
        builder.add_reason(
            "COMMS.TRANSCRIPT.ALLOW.v1",
            "Transcript accepted.",
            severity="Low",
            decision="ALLOW",
            evidence_refs=[evidence_ref],
        )
    policy_key = "comms_billing" if call.classification == "billing" else "comms_ops"
    policy = (
        db.query(RetentionPolicy)
        .filter(RetentionPolicy.org_id == user.org_id, RetentionPolicy.applies_to == policy_key)
        .first()
    )
    transcript = CommsTranscript(
        org_id=user.org_id,
        call_id=call.id,
        classification=call.classification,
        transcript_text=payload.transcript_text,
        segments=[segment.dict() for segment in payload.segments],
        confidence=int(payload.confidence * 100),
        evidence_hash=evidence_hash,
        method_used=payload.method_used,
        retention_policy_id=policy.id if policy else None,
    )
    apply_training_mode(transcript, request)
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload={"call_id": call.id, "evidence_hash": evidence_hash},
        classification="PHI",
        action="comms_transcript",
        resource="comms_call",
        reason_code="SMART_POLICY",
    )
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_transcript",
        classification="PHI",
        after_state=model_snapshot(transcript),
        event_type="comms.transcript.created",
        event_payload={"call_id": call.id, "transcript_id": transcript.id},
    )
    return {"transcript": model_snapshot(transcript), "decision": decision}


@router.get("/recordings/{recording_id}/download")
def download_recording(
    recording_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.billing)),
):
    recording = (
        scoped_query(db, CommsRecording, user.org_id, request.state.training_mode)
        .filter(CommsRecording.id == recording_id)
        .first()
    )
    if not recording:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")
    hold = get_active_hold(db, user.org_id, "comms_recording", str(recording.id))
    if hold:
        builder = DecisionBuilder(component="comms_recording", component_version="v1")
        builder.add_reason(
            "COMMS.LEGAL_HOLD.BLOCK_RECORDING.v1",
            "Legal hold blocks recording access.",
            severity="High",
            decision="BLOCK",
        )
        decision = finalize_decision_packet(
            db=db,
            request=request,
            user=user,
            builder=builder,
            input_payload={"recording_id": recording.id},
            classification="LEGAL_HOLD",
            action="comms_recording_download",
            resource="comms_recording",
            reason_code="SMART_POLICY",
        )
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="blocked",
            resource="comms_recording",
            classification="LEGAL_HOLD",
            after_state={"recording_id": recording.id, "reason": "LEGAL_HOLD_ACTIVE"},
            event_type="comms.recording.blocked",
            event_payload={"recording_id": recording.id},
        )
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    if recording.storage_key:
        payload = get_storage_backend().read_bytes(recording.storage_key)
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="download",
            resource="comms_recording",
            classification="OPS",
            after_state={"recording_id": recording.id},
            event_type="comms.recording.downloaded",
            event_payload={"recording_id": recording.id},
        )
        return StreamingResponse(io.BytesIO(payload), media_type="audio/mpeg")
    if recording.recording_url:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="download",
            resource="comms_recording",
            classification="OPS",
            after_state={"recording_id": recording.id},
            event_type="comms.recording.downloaded",
            event_payload={"recording_id": recording.id},
        )
        return {"recording_url": recording.recording_url}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recording available")


@router.post("/voice/plan")
def voice_plan(
    payload: VoicePlanRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    builder = DecisionBuilder(component="comms_voice_plan", component_version="v1")
    evidence_ref = builder.add_evidence(
        "voice_request",
        "comms_voice",
        {
            "urgency": payload.urgency,
            "ambient_noise": payload.ambient_noise,
            "allow_speaker": payload.allow_speaker,
        },
    )
    if not payload.allow_speaker:
        builder.add_reason(
            "VOICE.SPEAKER.DISABLED.v1",
            "Device speaker output is disabled.",
            severity="Medium",
            decision="REQUIRE_CONFIRMATION",
            evidence_refs=[evidence_ref],
        )
    if payload.ambient_noise >= 0.7:
        builder.add_reason(
            "VOICE.NOISE.BLOCK.v1",
            "Ambient noise too high for safe speech output.",
            severity="High",
            decision="BLOCK",
            evidence_refs=[evidence_ref],
        )
    if not builder.reasons:
        builder.add_reason(
            "VOICE.PLAN.ALLOW.v1",
            "Voice output approved.",
            severity="Low",
            decision="ALLOW",
            evidence_refs=[evidence_ref],
        )
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload=payload.dict(),
        classification="OPS",
        action="voice_plan",
        resource="comms_voice",
        reason_code="SMART_POLICY",
    )
    return {
        "decision": decision,
        "speech_plan": {
            "engine": "local",
            "urgency": payload.urgency,
            "message": payload.message,
        },
    }


@router.get("/phone-numbers")
def list_phone_numbers(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, CommsPhoneNumber, user.org_id, request.state.training_mode).order_by(
        CommsPhoneNumber.created_at.desc()
    )


@router.post("/phone-numbers", status_code=status.HTTP_201_CREATED)
def create_phone_number(
    payload: PhoneNumberCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    phone = CommsPhoneNumber(org_id=user.org_id, **payload.dict())
    apply_training_mode(phone, request)
    db.add(phone)
    db.commit()
    db.refresh(phone)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_phone_number",
        classification="NON_PHI",
        after_state=model_snapshot(phone),
        event_type="comms.phone_number.created",
        event_payload={"phone_id": phone.id},
    )
    return model_snapshot(phone)


@router.get("/routing-policies")
def list_routing_policies(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, CommsRoutingPolicy, user.org_id, request.state.training_mode).order_by(
        CommsRoutingPolicy.created_at.desc()
    )


@router.post("/routing-policies", status_code=status.HTTP_201_CREATED)
def create_routing_policy(
    payload: RoutingPolicyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    policy = CommsRoutingPolicy(org_id=user.org_id, **payload.dict())
    apply_training_mode(policy, request)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_routing_policy",
        classification="NON_PHI",
        after_state=model_snapshot(policy),
        event_type="comms.routing_policy.created",
        event_payload={"policy_id": policy.id},
    )
    return model_snapshot(policy)


@router.get("/ring-groups")
def list_ring_groups(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, CommsRingGroup, user.org_id, request.state.training_mode).order_by(
        CommsRingGroup.created_at.desc()
    )


@router.post("/ring-groups", status_code=status.HTTP_201_CREATED)
def create_ring_group(
    payload: RingGroupCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    group = CommsRingGroup(org_id=user.org_id, **payload.dict())
    apply_training_mode(group, request)
    db.add(group)
    db.commit()
    db.refresh(group)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_ring_group",
        classification="NON_PHI",
        after_state=model_snapshot(group),
        event_type="comms.ring_group.created",
        event_payload={"group_id": group.id},
    )
    return model_snapshot(group)

@router.get("/broadcasts")
def list_broadcasts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    return scoped_query(db, CommsBroadcast, user.org_id, request.state.training_mode).order_by(
        CommsBroadcast.created_at.desc()
    )


@router.post("/broadcasts", status_code=status.HTTP_201_CREATED)
def create_broadcast(
    payload: BroadcastCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    broadcast = CommsBroadcast(org_id=user.org_id, **payload.dict())
    apply_training_mode(broadcast, request)
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_broadcast",
        classification="NON_PHI",
        after_state=model_snapshot(broadcast),
        event_type="comms.broadcast.created",
        event_payload={"broadcast_id": broadcast.id},
    )
    return model_snapshot(broadcast)


@router.get("/tasks")
def list_tasks(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return scoped_query(db, CommsTask, user.org_id, request.state.training_mode).order_by(
        CommsTask.created_at.desc()
    )


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    task = CommsTask(org_id=user.org_id, **payload.dict())
    apply_training_mode(task, request)
    db.add(task)
    db.commit()
    db.refresh(task)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_task",
        classification="OPS",
        after_state=model_snapshot(task),
        event_type="comms.task.created",
        event_payload={"task_id": task.id},
    )
    return model_snapshot(task)


class ThreadCreate(BaseModel):
    channel: str = "email"
    subject: str = ""
    priority: str = "Normal"
    linked_resource: str = ""
    participants: list = []


class SendEmail(BaseModel):
    thread_id: int | None = None
    subject: str
    recipients: list[str]
    body_plain: str = ""
    body_html: str = ""
    metadata: dict = {}


class SendTelnyx(BaseModel):
    thread_id: int | None = None
    recipient: str
    body: str = ""
    media_url: str = ""
    metadata: dict = {}


@router.post("/thread/create", status_code=status.HTTP_201_CREATED)
def create_thread_alias(
    payload: ThreadCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    thread = CommsThread(org_id=user.org_id, **payload.dict())
    apply_training_mode(thread, request)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="comms_thread",
        classification="NON_PHI",
        after_state=model_snapshot(thread),
        event_type="comms.thread.created",
        event_payload={"thread_id": thread.id},
    )
    return model_snapshot(thread)


@router.get("/thread/{thread_id}")
def get_thread_detail(
    thread_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    thread = (
        scoped_query(db, CommsThread, user.org_id, request.state.training_mode)
        .filter(CommsThread.id == thread_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    messages = (
        scoped_query(db, CommsMessage, user.org_id, request.state.training_mode)
        .filter(CommsMessage.thread_id == thread.id)
        .order_by(CommsMessage.created_at.asc())
        .all()
    )
    return {
        "thread": model_snapshot(thread),
        "messages": [model_snapshot(message) for message in messages],
    }


@router.post("/send/email", status_code=status.HTTP_201_CREATED)
def send_email(
    payload: SendEmail,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    if not payload.recipients:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Recipients required")
    thread = None
    if payload.thread_id:
        thread = (
            scoped_query(db, CommsThread, user.org_id, request.state.training_mode)
            .filter(CommsThread.id == payload.thread_id)
            .first()
        )
    if not thread:
        thread = CommsThread(org_id=user.org_id, channel="email", subject=payload.subject)
        apply_training_mode(thread, request)
        db.add(thread)
        db.commit()
        db.refresh(thread)
    message = CommsMessage(
        org_id=user.org_id,
        thread_id=thread.id,
        sender=user.email,
        body=payload.body_plain or payload.body_html,
        delivery_status="queued",
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    event = _record_event(
        db,
        request,
        user,
        thread,
        message,
        "email.send",
        {"subject": payload.subject, "preview": _redact_text(message.body)},
    )
    try:
        from services.email.email_transport_service import send_outbound

        result = send_outbound(
            db=db,
            request=request,
            user=user,
            payload={
                "subject": payload.subject,
                "recipients": payload.recipients,
                "body_plain": payload.body_plain,
                "body_html": payload.body_html,
                "metadata": payload.metadata,
            },
        )
        event.status = "sent"
        db.commit()
        _record_attempt(db, event, "postmark", "sent", result)
    except HTTPException as exc:
        event.status = "failed"
        event.error = str(exc.detail)
        db.commit()
        _record_attempt(db, event, "postmark", "failed", {}, str(exc.detail))
        raise
    return {"thread": model_snapshot(thread), "message": model_snapshot(message)}


@router.post("/send/sms", status_code=status.HTTP_201_CREATED)
def send_sms(
    payload: SendTelnyx,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    thread = None
    if payload.thread_id:
        thread = (
            scoped_query(db, CommsThread, user.org_id, request.state.training_mode)
            .filter(CommsThread.id == payload.thread_id)
            .first()
        )
    if not thread:
        thread = CommsThread(org_id=user.org_id, channel="sms", subject="SMS")
        apply_training_mode(thread, request)
        db.add(thread)
        db.commit()
        db.refresh(thread)
    message = CommsMessage(
        org_id=user.org_id,
        thread_id=thread.id,
        sender=settings.TELNYX_NUMBER or user.email,
        body=payload.body,
        delivery_status="queued",
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    event = _record_event(
        db,
        request,
        user,
        thread,
        message,
        "sms.send",
        {"recipient": payload.recipient, "preview": _redact_text(payload.body)},
    )
    try:
        provider_id = _send_telnyx("sms", payload.recipient, payload.body)
        event.status = "sent"
        db.commit()
        _record_attempt(db, event, "telnyx", "sent", {"provider_id": provider_id})
    except HTTPException as exc:
        event.status = "failed"
        event.error = str(exc.detail)
        db.commit()
        _record_attempt(db, event, "telnyx", "failed", {}, str(exc.detail))
        raise
    return {"thread": model_snapshot(thread), "message": model_snapshot(message)}


@router.post("/send/fax", status_code=status.HTTP_201_CREATED)
def send_fax(
    payload: SendTelnyx,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    if not payload.media_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fax media_url required")
    thread = CommsThread(org_id=user.org_id, channel="fax", subject="Fax")
    apply_training_mode(thread, request)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    message = CommsMessage(
        org_id=user.org_id,
        thread_id=thread.id,
        sender=settings.TELNYX_NUMBER or user.email,
        body=payload.body or "fax",
        media_url=payload.media_url,
        delivery_status="queued",
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    event = _record_event(
        db,
        request,
        user,
        thread,
        message,
        "fax.send",
        {"recipient": payload.recipient, "preview": _redact_text(payload.body)},
    )
    try:
        provider_id = _send_telnyx("fax", payload.recipient, payload.body, payload.media_url)
        event.status = "sent"
        db.commit()
        _record_attempt(db, event, "telnyx", "sent", {"provider_id": provider_id})
    except HTTPException as exc:
        event.status = "failed"
        event.error = str(exc.detail)
        db.commit()
        _record_attempt(db, event, "telnyx", "failed", {}, str(exc.detail))
        raise
    return {"thread": model_snapshot(thread), "message": model_snapshot(message)}


@router.post("/send/voice", status_code=status.HTTP_201_CREATED)
def send_voice(
    payload: SendTelnyx,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    thread = CommsThread(org_id=user.org_id, channel="voice", subject="Voice")
    apply_training_mode(thread, request)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    message = CommsMessage(
        org_id=user.org_id,
        thread_id=thread.id,
        sender=settings.TELNYX_NUMBER or user.email,
        body=payload.body or "voice",
        delivery_status="queued",
    )
    apply_training_mode(message, request)
    db.add(message)
    db.commit()
    db.refresh(message)
    event = _record_event(
        db,
        request,
        user,
        thread,
        message,
        "voice.send",
        {"recipient": payload.recipient, "preview": _redact_text(payload.body)},
    )
    try:
        provider_id = _send_telnyx("voice", payload.recipient, payload.body)
        event.status = "sent"
        db.commit()
        _record_attempt(db, event, "telnyx", "sent", {"provider_id": provider_id})
    except HTTPException as exc:
        event.status = "failed"
        event.error = str(exc.detail)
        db.commit()
        _record_attempt(db, event, "telnyx", "failed", {}, str(exc.detail))
        raise
    return {"thread": model_snapshot(thread), "message": model_snapshot(message)}


@router.post("/retry/{event_id}")
def retry_event(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    event = (
        scoped_query(db, CommsEvent, user.org_id, request.state.training_mode)
        .filter(CommsEvent.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    event.status = "retry_queued"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="comms_event",
        classification="OPS",
        after_state=model_snapshot(event),
        event_type="comms.event.retry",
        event_payload={"event_id": event.id},
    )
    return {"status": "queued"}


@router.get("/queue")
def comms_queue(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.billing, UserRole.compliance, UserRole.founder)),
):
    events = (
        scoped_query(db, CommsEvent, user.org_id, request.state.training_mode)
        .order_by(CommsEvent.created_at.desc())
        .all()
    )
    attempts = (
        scoped_query(db, CommsDeliveryAttempt, user.org_id, request.state.training_mode)
        .order_by(CommsDeliveryAttempt.created_at.desc())
        .all()
    )
    return {
        "events": [model_snapshot(event) for event in events],
        "attempts": [model_snapshot(attempt) for attempt in attempts],
    }
