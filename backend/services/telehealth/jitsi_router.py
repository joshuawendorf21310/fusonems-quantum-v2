from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_telehealth_db
from core.security import require_roles
from models.telehealth import TelehealthAppointment, TelehealthSession
from models.user import User, UserRole
from services.telehealth.jitsi_service import get_jitsi_service
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(prefix="/api/carefusion/video", tags=["CareFusion Video"])


class VideoRoomCreate(BaseModel):
    appointment_id: str
    session_title: str


class VideoRoomResponse(BaseModel):
    room_name: str
    jwt_token: str
    jitsi_config: dict
    session_uuid: str


@router.post("/create-room", response_model=VideoRoomResponse, status_code=status.HTTP_201_CREATED)
def create_video_room(
    payload: VideoRoomCreate,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    """
    Create a secure Jitsi video room for a telehealth appointment.
    
    - Generates unique room name
    - Creates JWT token with appropriate permissions
    - Returns Jitsi configuration for frontend
    """
    # Verify appointment exists
    appointment = (
        scoped_query(db, TelehealthAppointment, user.org_id, request.state.training_mode)
        .filter(TelehealthAppointment.appointment_id == payload.appointment_id)
        .first()
    )
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Determine if user is moderator (providers are moderators)
    is_moderator = user.role in [UserRole.provider, UserRole.admin]
    
    # Get Jitsi service
    jitsi = get_jitsi_service()
    
    # Generate unique room name
    room_name = jitsi.generate_room_name(
        appointment_id=payload.appointment_id,
        org_id=user.org_id
    )
    
    # Generate JWT token
    token = jitsi.generate_token(
        room_name=room_name,
        user_name=user.name or user.email,
        user_email=user.email,
        user_id=str(user.id),
        is_moderator=is_moderator,
        expires_in_hours=24,
    )
    
    # Create Jitsi config
    jitsi_config = jitsi.create_meeting_config(
        room_name=room_name,
        token=token,
        user_name=user.name or user.email,
        is_moderator=is_moderator,
    )
    
    # Create or update telehealth session
    import uuid
    session_uuid = str(uuid.uuid4())
    
    session = TelehealthSession(
        org_id=user.org_id,
        session_uuid=session_uuid,
        title=payload.session_title,
        host_name=user.name or user.email,
        access_code=room_name,  # Store Jitsi room name
        session_secret=token[:32],  # Store token hash
        status="Scheduled",
        modality="video",
        recording_enabled=is_moderator,
        consent_required=True,
    )
    
    apply_training_mode(session, request)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Link session to appointment
    appointment.session_uuid = session_uuid
    db.commit()
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="video_room",
        classification="PHI",
        after_state=model_snapshot(session),
        event_type="carefusion.video.room_created",
        event_payload={
            "session_uuid": session_uuid,
            "appointment_id": payload.appointment_id,
            "room_name": room_name,
        },
    )
    
    return VideoRoomResponse(
        room_name=room_name,
        jwt_token=token,
        jitsi_config=jitsi_config,
        session_uuid=session_uuid,
    )


@router.get("/room/{session_uuid}", response_model=VideoRoomResponse)
def join_video_room(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider, UserRole.patient)),
):
    """
    Join an existing video room.
    
    - Retrieves session details
    - Generates new JWT token for user
    - Returns Jitsi configuration
    """
    # Get session
    session = (
        scoped_query(db, TelehealthSession, user.org_id, request.state.training_mode)
        .filter(TelehealthSession.session_uuid == session_uuid)
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    # Determine if user is moderator
    is_moderator = user.role in [UserRole.provider, UserRole.admin]
    
    # Get Jitsi service
    jitsi = get_jitsi_service()
    
    # Room name is stored in access_code
    room_name = session.access_code
    
    # Generate JWT token for this user
    token = jitsi.generate_token(
        room_name=room_name,
        user_name=user.name or user.email,
        user_email=user.email,
        user_id=str(user.id),
        is_moderator=is_moderator,
        expires_in_hours=24,
    )
    
    # Create Jitsi config
    jitsi_config = jitsi.create_meeting_config(
        room_name=room_name,
        token=token,
        user_name=user.name or user.email,
        is_moderator=is_moderator,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="read",
        resource="video_room",
        classification="PHI",
        after_state={"session_uuid": session_uuid, "user_id": user.id},
        event_type="carefusion.video.room_joined",
        event_payload={
            "session_uuid": session_uuid,
            "room_name": room_name,
        },
    )
    
    return VideoRoomResponse(
        room_name=room_name,
        jwt_token=token,
        jitsi_config=jitsi_config,
        session_uuid=session_uuid,
    )


@router.post("/room/{session_uuid}/start")
def start_video_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """
    Start a video session (moderator only).
    Updates session status to Live.
    """
    session = (
        scoped_query(db, TelehealthSession, user.org_id, request.state.training_mode)
        .filter(TelehealthSession.session_uuid == session_uuid)
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    from datetime import datetime, timezone
    
    before = model_snapshot(session)
    session.status = "Live"
    session.started_at = datetime.now(timezone.utc)
    db.commit()
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="video_session",
        classification="PHI",
        before_state=before,
        after_state=model_snapshot(session),
        event_type="carefusion.video.session_started",
        event_payload={"session_uuid": session_uuid},
    )
    
    return {"status": "started", "session_uuid": session_uuid}


@router.post("/room/{session_uuid}/end")
def end_video_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_telehealth_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.provider)),
):
    """
    End a video session (moderator only).
    Updates session status to Ended.
    """
    session = (
        scoped_query(db, TelehealthSession, user.org_id, request.state.training_mode)
        .filter(TelehealthSession.session_uuid == session_uuid)
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    from datetime import datetime, timezone
    
    before = model_snapshot(session)
    session.status = "Ended"
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="video_session",
        classification="PHI",
        before_state=before,
        after_state=model_snapshot(session),
        event_type="carefusion.video.session_ended",
        event_payload={"session_uuid": session_uuid},
    )
    
    return {"status": "ended", "session_uuid": session_uuid}
