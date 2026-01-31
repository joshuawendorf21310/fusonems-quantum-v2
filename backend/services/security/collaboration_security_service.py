"""
Collaborative Computing Security Service for FedRAMP SC-15 compliance.

This module provides:
- Screen sharing controls and monitoring
- Video conferencing security (Jitsi integration)
- Participant validation and authorization
- Session security monitoring
- Access control for collaborative sessions

FedRAMP SC-15: Control collaborative computing devices and applications.
"""

import logging
from typing import Optional, Dict, List, Any, Set
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Session, relationship

from core.database import Base
from services.telehealth.jitsi_service import JitsiService

logger = logging.getLogger(__name__)


class SessionPermission(Enum):
    """Session permissions."""
    SCREEN_SHARE = "screen_share"
    RECORD = "record"
    MODERATE = "moderate"
    CHAT = "chat"
    PARTICIPANT_CONTROL = "participant_control"


class SessionStatus(Enum):
    """Session status."""
    CREATED = "created"
    ACTIVE = "active"
    ENDED = "ended"
    TERMINATED = "terminated"


class CollaborationSession(Base):
    """Database model for collaboration sessions."""
    __tablename__ = "collaboration_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    session_type = Column(String(50), nullable=False)  # "video", "screen_share", "document"
    room_name = Column(String(255), nullable=False, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default=SessionStatus.CREATED.value, index=True)
    
    # Security settings
    require_authentication = Column(Boolean, nullable=False, default=True)
    require_moderator_approval = Column(Boolean, nullable=False, default=True)
    allow_screen_share = Column(Boolean, nullable=False, default=True)
    allow_recording = Column(Boolean, nullable=False, default=False)
    max_participants = Column(Integer, nullable=False, default=10)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = relationship("CollaborationParticipant", back_populates="session", cascade="all, delete-orphan")
    events = relationship("CollaborationEvent", back_populates="session", cascade="all, delete-orphan")


class CollaborationParticipant(Base):
    """Database model for collaboration session participants."""
    __tablename__ = "collaboration_participants"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    participant_id = Column(String(64), nullable=False, index=True)  # Jitsi participant ID
    
    # Permissions
    is_moderator = Column(Boolean, nullable=False, default=False)
    can_screen_share = Column(Boolean, nullable=False, default=False)
    can_record = Column(Boolean, nullable=False, default=False)
    can_moderate = Column(Boolean, nullable=False, default=False)
    
    # Status
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_id = Column(String(64), nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("CollaborationSession", back_populates="participants")
    events = relationship("CollaborationEvent", back_populates="participant")


class CollaborationEvent(Base):
    """Database model for collaboration session events."""
    __tablename__ = "collaboration_events"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    participant_id = Column(Integer, ForeignKey("collaboration_participants.id"), nullable=True)
    
    event_type = Column(String(50), nullable=False, index=True)  # "join", "leave", "screen_share_start", etc.
    event_data = Column(JSON, nullable=True)
    
    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("CollaborationSession", back_populates="events")
    participant = relationship("CollaborationParticipant", back_populates="events")


class CollaborationSecurityService:
    """
    Service for managing collaborative computing security.
    
    Features:
    - Screen sharing controls
    - Video conferencing security (Jitsi)
    - Participant validation
    - Session monitoring
    """
    
    def __init__(self, db: Session, jitsi_service: Optional[JitsiService] = None):
        """
        Initialize collaboration security service.
        
        Args:
            db: Database session
            jitsi_service: Optional Jitsi service instance
        """
        self.db = db
        self._jitsi_service = jitsi_service or JitsiService()
    
    def create_session(
        self,
        session_type: str,
        room_name: str,
        org_id: int,
        created_by: int,
        require_authentication: bool = True,
        require_moderator_approval: bool = True,
        allow_screen_share: bool = True,
        allow_recording: bool = False,
        max_participants: int = 10,
        metadata: Optional[Dict] = None
    ) -> CollaborationSession:
        """
        Create a new collaboration session.
        
        Args:
            session_type: Type of session ("video", "screen_share", "document")
            room_name: Room identifier (e.g., Jitsi room name)
            org_id: Organization ID
            created_by: User ID of creator
            require_authentication: Require user authentication
            require_moderator_approval: Require moderator approval for participants
            allow_screen_share: Allow screen sharing
            allow_recording: Allow recording
            max_participants: Maximum number of participants
            metadata: Optional metadata
            
        Returns:
            CollaborationSession object
        """
        session = CollaborationSession(
            session_id=self._generate_session_id(),
            session_type=session_type,
            room_name=room_name,
            org_id=org_id,
            created_by=created_by,
            require_authentication=require_authentication,
            require_moderator_approval=require_moderator_approval,
            allow_screen_share=allow_screen_share,
            allow_recording=allow_recording,
            max_participants=max_participants,
            metadata=metadata or {},
            status=SessionStatus.CREATED.value
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Log session creation
        self._log_event(
            session_id=session.id,
            participant_id=None,
            event_type="session_created",
            event_data={"session_type": session_type, "room_name": room_name}
        )
        
        logger.info(f"Created collaboration session: {session.session_id}")
        return session
    
    def add_participant(
        self,
        session_id: int,
        user_id: int,
        participant_id: str,
        is_moderator: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> CollaborationParticipant:
        """
        Add participant to collaboration session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            participant_id: Participant identifier (e.g., Jitsi participant ID)
            is_moderator: Whether participant is a moderator
            ip_address: Participant IP address
            user_agent: Participant user agent
            device_id: Device identifier
            
        Returns:
            CollaborationParticipant object
            
        Raises:
            ValueError: If session not found or max participants reached
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Check max participants
        active_count = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.is_active == True
        ).count()
        
        if active_count >= session.max_participants:
            raise ValueError(f"Maximum participants ({session.max_participants}) reached")
        
        # Check if user is already a participant
        existing = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
            CollaborationParticipant.is_active == True
        ).first()
        
        if existing:
            return existing
        
        # Set permissions based on moderator status and session settings
        participant = CollaborationParticipant(
            session_id=session_id,
            user_id=user_id,
            participant_id=participant_id,
            is_moderator=is_moderator,
            can_screen_share=session.allow_screen_share and (is_moderator or not session.require_moderator_approval),
            can_record=session.allow_recording and is_moderator,
            can_moderate=is_moderator,
            joined_at=datetime.utcnow(),
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id
        )
        
        self.db.add(participant)
        
        # Update session status if first participant
        if session.status == SessionStatus.CREATED.value:
            session.status = SessionStatus.ACTIVE.value
            session.started_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(participant)
        
        # Log participant join
        self._log_event(
            session_id=session_id,
            participant_id=participant.id,
            event_type="participant_joined",
            event_data={"user_id": user_id, "is_moderator": is_moderator},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Added participant {user_id} to session {session_id}")
        return participant
    
    def remove_participant(
        self,
        session_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> None:
        """
        Remove participant from session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            reason: Optional reason for removal
        """
        participant = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
            CollaborationParticipant.is_active == True
        ).first()
        
        if participant:
            participant.is_active = False
            participant.left_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log participant leave
            self._log_event(
                session_id=session_id,
                participant_id=participant.id,
                event_type="participant_left",
                event_data={"user_id": user_id, "reason": reason}
            )
            
            logger.info(f"Removed participant {user_id} from session {session_id}")
    
    def validate_screen_share_permission(
        self,
        session_id: int,
        user_id: int
    ) -> bool:
        """
        Validate if user can start screen sharing.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            True if user can screen share
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()
        
        if not session or not session.allow_screen_share:
            return False
        
        participant = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
            CollaborationParticipant.is_active == True
        ).first()
        
        if not participant:
            return False
        
        return participant.can_screen_share
    
    def record_screen_share_event(
        self,
        session_id: int,
        user_id: int,
        action: str,  # "start", "stop"
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record screen sharing event.
        
        Args:
            session_id: Session ID
            user_id: User ID
            action: Action ("start" or "stop")
            metadata: Optional metadata
        """
        participant = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
            CollaborationParticipant.is_active == True
        ).first()
        
        if participant:
            self._log_event(
                session_id=session_id,
                participant_id=participant.id,
                event_type=f"screen_share_{action}",
                event_data=metadata or {}
            )
    
    def validate_recording_permission(
        self,
        session_id: int,
        user_id: int
    ) -> bool:
        """
        Validate if user can record session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            True if user can record
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()
        
        if not session or not session.allow_recording:
            return False
        
        participant = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id,
            CollaborationParticipant.user_id == user_id,
            CollaborationParticipant.is_active == True
        ).first()
        
        if not participant:
            return False
        
        return participant.can_record
    
    def end_session(
        self,
        session_id: int,
        ended_by: int,
        reason: Optional[str] = None
    ) -> None:
        """
        End collaboration session.
        
        Args:
            session_id: Session ID
            ended_by: User ID who ended the session
            reason: Optional reason for ending
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()
        
        if session and session.status == SessionStatus.ACTIVE.value:
            session.status = SessionStatus.ENDED.value
            session.ended_at = datetime.utcnow()
            
            # Deactivate all participants
            self.db.query(CollaborationParticipant).filter(
                CollaborationParticipant.session_id == session_id,
                CollaborationParticipant.is_active == True
            ).update({"is_active": False, "left_at": datetime.utcnow()})
            
            self.db.commit()
            
            # Log session end
            self._log_event(
                session_id=session_id,
                participant_id=None,
                event_type="session_ended",
                event_data={"ended_by": ended_by, "reason": reason}
            )
            
            logger.info(f"Ended collaboration session: {session_id}")
    
    def get_session_participants(
        self,
        session_id: int,
        active_only: bool = True
    ) -> List[CollaborationParticipant]:
        """
        Get session participants.
        
        Args:
            session_id: Session ID
            active_only: Only return active participants
            
        Returns:
            List of participants
        """
        query = self.db.query(CollaborationParticipant).filter(
            CollaborationParticipant.session_id == session_id
        )
        
        if active_only:
            query = query.filter(CollaborationParticipant.is_active == True)
        
        return query.all()
    
    def get_session_statistics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with statistics
        """
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.id == session_id
        ).first()
        
        if not session:
            return {}
        
        participants = self.get_session_participants(session_id, active_only=False)
        active_participants = [p for p in participants if p.is_active]
        
        events = self.db.query(CollaborationEvent).filter(
            CollaborationEvent.session_id == session_id
        ).all()
        
        screen_share_events = [e for e in events if "screen_share" in e.event_type]
        
        return {
            "session_id": session.session_id,
            "session_type": session.session_type,
            "status": session.status,
            "total_participants": len(participants),
            "active_participants": len(active_participants),
            "moderators": len([p for p in active_participants if p.is_moderator]),
            "screen_share_events": len(screen_share_events),
            "total_events": len(events),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_seconds": (
                (session.ended_at - session.started_at).total_seconds()
                if session.started_at and session.ended_at
                else None
            )
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _log_event(
        self,
        session_id: int,
        participant_id: Optional[int],
        event_type: str,
        event_data: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log collaboration event."""
        event = CollaborationEvent(
            session_id=session_id,
            participant_id=participant_id,
            event_type=event_type,
            event_data=event_data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(event)
        self.db.commit()
