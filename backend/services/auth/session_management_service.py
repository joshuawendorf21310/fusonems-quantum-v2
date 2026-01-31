"""Session management service for FedRAMP AC-11/AC-12 compliance"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Request

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.logger import logger
from core.config import settings
from models.auth_session import AuthSession
from models.user import User
from utils.audit import record_audit


class SessionManagementService:
    """Service for managing user sessions per FedRAMP AC-11/AC-12 requirements"""

    # FedRAMP AC-11/AC-12 requirements
    INACTIVITY_TIMEOUT_MINUTES = 15  # 15 minutes of inactivity
    MAX_SESSION_LIFETIME_HOURS = 12  # Maximum 12 hours session lifetime
    MAX_CONCURRENT_SESSIONS = 5  # Maximum concurrent sessions per user

    @staticmethod
    def check_session_timeout(session: AuthSession) -> tuple[bool, Optional[str]]:
        """
        Check if session has timed out due to inactivity or exceeded maximum lifetime.
        Returns (is_valid, reason_if_invalid)
        """
        now = datetime.now(timezone.utc)

        # Check if session is revoked
        if session.revoked_at is not None:
            return False, "Session revoked"

        # Check if session has expired
        if session.expires_at < now:
            return False, "Session expired"

        # Check inactivity timeout (FedRAMP AC-11)
        if session.last_seen_at:
            inactivity_duration = now - session.last_seen_at
            if inactivity_duration > timedelta(minutes=SessionManagementService.INACTIVITY_TIMEOUT_MINUTES):
                return False, f"Inactivity timeout ({SessionManagementService.INACTIVITY_TIMEOUT_MINUTES} minutes)"

        # Check maximum session lifetime (FedRAMP AC-12)
        session_age = now - session.created_at
        if session_age > timedelta(hours=SessionManagementService.MAX_SESSION_LIFETIME_HOURS):
            return False, f"Maximum session lifetime exceeded ({SessionManagementService.MAX_SESSION_LIFETIME_HOURS} hours)"

        return True, None

    @staticmethod
    def update_session_activity(
        db: Session,
        session: AuthSession,
        request: Optional[Request] = None,
    ) -> None:
        """Update session last_seen_at timestamp"""
        session.last_seen_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def enforce_concurrent_session_limit(
        db: Session,
        user_id: int,
        new_session_jti: str,
        request: Optional[Request] = None,
    ) -> List[AuthSession]:
        """
        Enforce maximum concurrent sessions per user (FedRAMP AC-12).
        Returns list of sessions that were terminated.
        """
        now = datetime.now(timezone.utc)
        
        # Get all active sessions for user (excluding the new one being created)
        active_sessions = (
            db.query(AuthSession)
            .filter(
                AuthSession.user_id == user_id,
                AuthSession.jwt_jti != new_session_jti,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .order_by(AuthSession.last_seen_at.desc())
            .all()
        )

        terminated_sessions = []

        # If we exceed the limit, revoke oldest sessions
        if len(active_sessions) >= SessionManagementService.MAX_CONCURRENT_SESSIONS:
            sessions_to_revoke = active_sessions[SessionManagementService.MAX_CONCURRENT_SESSIONS - 1:]
            
            for session in sessions_to_revoke:
                session.revoked_at = now
                session.revoked_reason = "concurrent_session_limit"
                terminated_sessions.append(session)
                
                logger.info(
                    f"Terminated session due to concurrent limit: "
                    f"user_id={user_id}, session_id={session.id}, jti={session.jwt_jti}"
                )

                # Audit session termination
                if request:
                    try:
                        user = db.query(User).filter(User.id == user_id).first()
                        if user:
                            record_audit(
                                db=db,
                                request=request,
                                user=user,
                                action="session_terminated",
                                resource="auth_session",
                                outcome="Blocked",
                                classification="NON_PHI",
                                reason_code="CONCURRENT_SESSION_LIMIT",
                                after_state={
                                    "session_id": session.id,
                                    "jti": session.jwt_jti,
                                    "reason": "concurrent_session_limit",
                                },
                            )
                    except Exception as e:
                        logger.error(f"Failed to record audit for session termination: {e}", exc_info=True)

            if terminated_sessions:
                db.commit()

        return terminated_sessions

    @staticmethod
    def terminate_session(
        db: Session,
        session_id: Optional[int] = None,
        jwt_jti: Optional[str] = None,
        user_id: Optional[int] = None,
        reason: str = "admin_termination",
        admin_user: Optional[User] = None,
        request: Optional[Request] = None,
    ) -> bool:
        """
        Terminate a specific session.
        Returns True if session was terminated, False if not found.
        """
        session = None
        
        if session_id:
            session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
        elif jwt_jti:
            session = db.query(AuthSession).filter(AuthSession.jwt_jti == jwt_jti).first()
        
        if not session:
            return False

        # Verify user_id matches if provided
        if user_id and session.user_id != user_id:
            return False

        # Check if already revoked
        if session.revoked_at is not None:
            return False

        now = datetime.now(timezone.utc)
        session.revoked_at = now
        session.revoked_reason = reason
        db.commit()

        # Audit session termination
        if request:
            try:
                session_user = db.query(User).filter(User.id == session.user_id).first()
                if session_user:
                    record_audit(
                        db=db,
                        request=request,
                        user=admin_user or session_user,
                        action="session_terminated",
                        resource="auth_session",
                        outcome="Allowed",
                        classification="NON_PHI",
                        reason_code="SESSION_TERMINATION",
                        after_state={
                            "session_id": session.id,
                            "jti": session.jwt_jti,
                            "terminated_user_id": session.user_id,
                            "reason": reason,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for session termination: {e}", exc_info=True)

        logger.info(
            f"Session terminated: session_id={session.id}, user_id={session.user_id}, "
            f"reason={reason}, admin={admin_user.email if admin_user else 'self'}"
        )
        return True

    @staticmethod
    def terminate_all_user_sessions(
        db: Session,
        user_id: int,
        reason: str = "admin_termination",
        admin_user: Optional[User] = None,
        request: Optional[Request] = None,
    ) -> int:
        """
        Terminate all active sessions for a user.
        Returns count of terminated sessions.
        """
        now = datetime.now(timezone.utc)
        active_sessions = (
            db.query(AuthSession)
            .filter(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .all()
        )

        count = 0
        for session in active_sessions:
            session.revoked_at = now
            session.revoked_reason = reason
            count += 1

        if count > 0:
            db.commit()

            # Audit bulk termination
            if request:
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        record_audit(
                            db=db,
                            request=request,
                            user=admin_user or user,
                            action="all_sessions_terminated",
                            resource="auth_session",
                            outcome="Allowed",
                            classification="NON_PHI",
                            reason_code="BULK_SESSION_TERMINATION",
                            after_state={
                                "terminated_user_id": user_id,
                                "sessions_terminated": count,
                                "reason": reason,
                            },
                        )
                except Exception as e:
                    logger.error(f"Failed to record audit for bulk session termination: {e}", exc_info=True)

            logger.info(
                f"Terminated {count} sessions for user_id={user_id}, "
                f"reason={reason}, admin={admin_user.email if admin_user else 'self'}"
            )

        return count

    @staticmethod
    def get_user_active_sessions(
        db: Session,
        user_id: int,
    ) -> List[AuthSession]:
        """Get all active sessions for a user"""
        now = datetime.now(timezone.utc)
        return (
            db.query(AuthSession)
            .filter(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .order_by(AuthSession.last_seen_at.desc())
            .all()
        )

    @staticmethod
    def cleanup_expired_sessions(db: Session, older_than_days: int = 30) -> int:
        """
        Clean up expired and revoked sessions older than specified days.
        Returns count of cleaned up sessions.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        
        expired_sessions = (
            db.query(AuthSession)
            .filter(
                or_(
                    AuthSession.expires_at < cutoff,
                    and_(
                        AuthSession.revoked_at.isnot(None),
                        AuthSession.revoked_at < cutoff,
                    ),
                )
            )
            .all()
        )

        count = len(expired_sessions)
        for session in expired_sessions:
            db.delete(session)

        if count > 0:
            db.commit()
            logger.info(f"Cleaned up {count} expired sessions older than {older_than_days} days")

        return count

    @staticmethod
    def get_session_info(session: AuthSession) -> dict:
        """Get session information for API responses"""
        now = datetime.now(timezone.utc)
        is_valid, reason = SessionManagementService.check_session_timeout(session)
        
        return {
            "session_id": session.id,
            "jti": session.jwt_jti,
            "created_at": session.created_at.isoformat(),
            "last_seen_at": session.last_seen_at.isoformat() if session.last_seen_at else None,
            "expires_at": session.expires_at.isoformat(),
            "is_revoked": session.revoked_at is not None,
            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
            "revoked_reason": session.revoked_reason,
            "is_valid": is_valid,
            "invalid_reason": reason,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "session_age_minutes": (now - session.created_at).total_seconds() / 60,
            "inactivity_minutes": (
                (now - session.last_seen_at).total_seconds() / 60
                if session.last_seen_at else None
            ),
        }
