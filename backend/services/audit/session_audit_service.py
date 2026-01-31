"""
Session Audit Service for FedRAMP AU-14 Compliance

FedRAMP Requirement AU-14: Session Audit
- Detailed session event capture
- User activity tracking during sessions
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.session_audit import SessionAuditEvent, SessionEventType
from models.auth_session import AuthSession
from models.user import User
from services.audit.comprehensive_audit_service import ComprehensiveAuditService


class SessionAuditService:
    """
    Service for session audit event capture (AU-14).
    """
    
    @staticmethod
    def log_session_event(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        event_type: SessionEventType,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        event_data: Optional[Dict] = None,
        outcome: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> SessionAuditEvent:
        """
        Log a session audit event.
        
        Args:
            db: Database session
            org_id: Organization ID
            user: User performing the action
            session: Active session
            event_type: Type of session event
            action: Action being performed
            resource_type: Type of resource (optional)
            resource_id: ID of resource (optional)
            request: HTTP request (optional, for context)
            event_data: Additional event data
            outcome: Outcome of action (success, failure, denied)
            duration_seconds: Duration in seconds (for activity events)
            
        Returns:
            Created SessionAuditEvent
        """
        # Extract request context
        ip_address = None
        user_agent = None
        request_method = None
        request_path = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            request_method = request.method
            request_path = str(request.url.path)
        
        # Create session audit event
        session_event = SessionAuditEvent(
            org_id=org_id,
            user_id=user.id,
            user_email=user.email,
            session_id=session.id,
            jwt_jti=session.jwt_jti,
            event_type=event_type.value,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            event_data=event_data,
            outcome=outcome,
            duration_seconds=duration_seconds,
            timestamp=datetime.now(timezone.utc),
        )
        
        db.add(session_event)
        
        try:
            db.commit()
            db.refresh(session_event)
            
            # Also log to comprehensive audit log for critical events
            if event_type in [
                SessionEventType.PRIVILEGE_USE,
                SessionEventType.CONFIGURATION_CHANGE,
                SessionEventType.SECURITY_EVENT,
            ]:
                ComprehensiveAuditService.log_security_event(
                    db=db,
                    org_id=org_id,
                    action=f"session_{action}",
                    resource_type=resource_type or "session",
                    outcome=outcome or "success",
                    user=user,
                    resource_id=str(session.id),
                    request=request,
                    metadata={
                        "session_event_id": str(session_event.id),
                        "session_jti": session.jwt_jti,
                    },
                )
            
            logger.debug(
                f"Session audit event logged: {event_type.value} - {action} "
                f"(session_id={session.id}, user={user.email})"
            )
            
            return session_event
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log session audit event: {e}", exc_info=True)
            raise
    
    @staticmethod
    def log_session_start(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        request: Optional[Request] = None,
    ) -> SessionAuditEvent:
        """Log session start event"""
        return SessionAuditService.log_session_event(
            db=db,
            org_id=org_id,
            user=user,
            session=session,
            event_type=SessionEventType.SESSION_START,
            action="session_started",
            request=request,
            outcome="success",
        )
    
    @staticmethod
    def log_session_end(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        request: Optional[Request] = None,
        duration_seconds: Optional[int] = None,
    ) -> SessionAuditEvent:
        """Log session end event"""
        return SessionAuditService.log_session_event(
            db=db,
            org_id=org_id,
            user=user,
            session=session,
            event_type=SessionEventType.SESSION_END,
            action="session_ended",
            request=request,
            outcome="success",
            duration_seconds=duration_seconds,
        )
    
    @staticmethod
    def log_session_revoked(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        reason: str,
        request: Optional[Request] = None,
    ) -> SessionAuditEvent:
        """Log session revocation event"""
        return SessionAuditService.log_session_event(
            db=db,
            org_id=org_id,
            user=user,
            session=session,
            event_type=SessionEventType.SESSION_REVOKED,
            action="session_revoked",
            request=request,
            event_data={"reason": reason},
            outcome="success",
        )
    
    @staticmethod
    def log_privilege_use(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        privilege: str,
        resource_type: str,
        resource_id: str,
        request: Optional[Request] = None,
        outcome: str = "success",
    ) -> SessionAuditEvent:
        """Log privilege use event"""
        return SessionAuditService.log_session_event(
            db=db,
            org_id=org_id,
            user=user,
            session=session,
            event_type=SessionEventType.PRIVILEGE_USE,
            action=f"privilege_use_{privilege}",
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            event_data={"privilege": privilege},
            outcome=outcome,
        )
    
    @staticmethod
    def log_data_access(
        db: Session,
        org_id: int,
        user: User,
        session: AuthSession,
        resource_type: str,
        resource_id: str,
        action: str,
        request: Optional[Request] = None,
        outcome: str = "success",
    ) -> SessionAuditEvent:
        """Log data access event"""
        return SessionAuditService.log_session_event(
            db=db,
            org_id=org_id,
            user=user,
            session=session,
            event_type=SessionEventType.DATA_ACCESS,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            outcome=outcome,
        )
    
    @staticmethod
    def get_session_events(
        db: Session,
        session_id: int,
        org_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 1000,
    ) -> List[SessionAuditEvent]:
        """Get all events for a session"""
        query = db.query(SessionAuditEvent).filter(
            SessionAuditEvent.session_id == session_id
        )
        
        if org_id:
            query = query.filter(SessionAuditEvent.org_id == org_id)
        if event_type:
            query = query.filter(SessionAuditEvent.event_type == event_type)
        
        return query.order_by(desc(SessionAuditEvent.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_user_session_activity(
        db: Session,
        user_id: int,
        org_id: int,
        hours: int = 24,
    ) -> List[SessionAuditEvent]:
        """Get user session activity for the last N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return db.query(SessionAuditEvent).filter(
            SessionAuditEvent.user_id == user_id,
            SessionAuditEvent.org_id == org_id,
            SessionAuditEvent.timestamp >= cutoff,
        ).order_by(desc(SessionAuditEvent.timestamp)).all()
