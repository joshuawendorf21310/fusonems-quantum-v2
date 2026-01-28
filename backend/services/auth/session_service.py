"""Session management service for secure token revocation"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.auth_session import AuthSession


def create_session(
    db: Session,
    org_id: int,
    user_id: int,
    jwt_jti: str,
    expires_at: datetime,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuthSession:
    """Create a new authentication session"""
    session = AuthSession(
        org_id=org_id,
        user_id=user_id,
        jwt_jti=jwt_jti,
        expires_at=expires_at,
        csrf_secret=secrets.token_hex(16),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_active_session(db: Session, jwt_jti: str) -> Optional[AuthSession]:
    """Get an active session by JWT ID, returns None if revoked or expired"""
    session = db.query(AuthSession).filter(AuthSession.jwt_jti == jwt_jti).first()
    if not session:
        return None
    
    # Check if revoked
    if session.revoked_at is not None:
        return None
    
    # Check if expired
    if session.expires_at < datetime.utcnow():
        return None
    
    return session


def update_last_seen(db: Session, session_id: int) -> None:
    """Update the last_seen_at timestamp for a session"""
    session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    if session:
        session.last_seen_at = datetime.utcnow()
        db.commit()


def revoke_session(
    db: Session,
    session_id: Optional[int] = None,
    jwt_jti: Optional[str] = None,
    reason: str = "logout",
) -> bool:
    """Revoke a session by session_id or jwt_jti"""
    if session_id:
        session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    elif jwt_jti:
        session = db.query(AuthSession).filter(AuthSession.jwt_jti == jwt_jti).first()
    else:
        return False
    
    if not session:
        return False
    
    session.revoked_at = datetime.utcnow()
    session.revoked_reason = reason
    db.commit()
    return True


def revoke_all_sessions_for_user(
    db: Session,
    user_id: int,
    reason: str = "admin_action",
) -> int:
    """Revoke all active sessions for a user. Returns count of revoked sessions."""
    now = datetime.utcnow()
    sessions = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .all()
    )
    
    count = 0
    for session in sessions:
        session.revoked_at = now
        session.revoked_reason = reason
        count += 1
    
    if count > 0:
        db.commit()
    
    return count


def cleanup_expired_sessions(db: Session, older_than_days: int = 30) -> int:
    """Delete expired sessions older than specified days. Returns count of deleted sessions."""
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    sessions = (
        db.query(AuthSession)
        .filter(AuthSession.expires_at < cutoff)
        .all()
    )
    
    count = len(sessions)
    for session in sessions:
        db.delete(session)
    
    if count > 0:
        db.commit()
    
    return count
