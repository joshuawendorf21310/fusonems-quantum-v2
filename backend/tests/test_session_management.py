"""Tests for session management functionality"""
import uuid
from datetime import datetime, timedelta

from models.auth_session import AuthSession
from models.user import User
from services.auth.session_service import (
    create_session,
    get_active_session,
    revoke_session,
    revoke_all_sessions_for_user,
    update_last_seen,
    cleanup_expired_sessions,
)


def test_create_and_get_session(client):
    """Test creating and retrieving an active session"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    # Create a user and org first
    register_payload = {
        "email": "session_test@example.com",
        "full_name": "Session Test",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "SessionTestOrg",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    user_data = response.json()["user"]
    
    # Get the user from DB
    user = db.query(User).filter(User.email == "session_test@example.com").first()
    assert user is not None
    
    # Create a session
    jti = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    session = create_session(
        db=db,
        org_id=user.org_id,
        user_id=user.id,
        jwt_jti=jti,
        expires_at=expires_at,
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    
    assert session.id is not None
    assert session.jwt_jti == jti
    assert session.user_id == user.id
    assert session.revoked_at is None
    
    # Retrieve the active session
    active_session = get_active_session(db=db, jwt_jti=jti)
    assert active_session is not None
    assert active_session.id == session.id
    
    db.close()


def test_revoke_session(client):
    """Test revoking a session"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    # Create a user
    register_payload = {
        "email": "revoke_test@example.com",
        "full_name": "Revoke Test",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "RevokeTestOrg",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    
    user = db.query(User).filter(User.email == "revoke_test@example.com").first()
    
    # Create a session
    jti = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    session = create_session(
        db=db,
        org_id=user.org_id,
        user_id=user.id,
        jwt_jti=jti,
        expires_at=expires_at,
    )
    
    # Verify session is active
    active_session = get_active_session(db=db, jwt_jti=jti)
    assert active_session is not None
    
    # Revoke the session
    result = revoke_session(db=db, jwt_jti=jti, reason="logout")
    assert result is True
    
    # Verify session is no longer active
    active_session = get_active_session(db=db, jwt_jti=jti)
    assert active_session is None
    
    # Verify revoked fields are set
    revoked_session = db.query(AuthSession).filter(AuthSession.jwt_jti == jti).first()
    assert revoked_session.revoked_at is not None
    assert revoked_session.revoked_reason == "logout"
    
    db.close()


def test_revoke_all_user_sessions(client):
    """Test revoking all sessions for a user"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    # Create a user
    register_payload = {
        "email": "multi_session@example.com",
        "full_name": "Multi Session",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "MultiSessionOrg",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    
    user = db.query(User).filter(User.email == "multi_session@example.com").first()
    
    # Create multiple additional sessions (register already created one)
    jti1 = str(uuid.uuid4())
    jti2 = str(uuid.uuid4())
    jti3 = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    session1 = create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti1, expires_at=expires_at)
    session2 = create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti2, expires_at=expires_at)
    session3 = create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti3, expires_at=expires_at)
    
    # Verify all sessions are active
    assert get_active_session(db=db, jwt_jti=jti1) is not None
    assert get_active_session(db=db, jwt_jti=jti2) is not None
    assert get_active_session(db=db, jwt_jti=jti3) is not None
    
    # Revoke all sessions for user (should be 4 total: 1 from register + 3 we created)
    count = revoke_all_sessions_for_user(db=db, user_id=user.id, reason="password_reset")
    assert count == 4
    
    # Verify all sessions are revoked
    assert get_active_session(db=db, jwt_jti=jti1) is None
    assert get_active_session(db=db, jwt_jti=jti2) is None
    assert get_active_session(db=db, jwt_jti=jti3) is None
    
    db.close()


def test_login_creates_session(client):
    """Test that login creates a session with JWT containing jti"""
    from jose import jwt
    from core.config import settings
    from core.database import SessionLocal
    
    # Register a user
    register_payload = {
        "email": "login_session@example.com",
        "full_name": "Login Session",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "LoginSessionOrg",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    
    # Login
    login_payload = {
        "email": "login_session@example.com",
        "password": "password123",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    # Decode JWT and verify jti is present
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert "jti" in payload
    assert "sub" in payload
    assert "org" in payload
    
    # Verify session exists in database
    db = SessionLocal()
    session = db.query(AuthSession).filter(AuthSession.jwt_jti == payload["jti"]).first()
    assert session is not None
    assert session.revoked_at is None
    db.close()


def test_logout_revokes_session(client):
    """Test that logout revokes the session"""
    from jose import jwt
    from core.config import settings
    from core.database import SessionLocal
    
    # Register and login
    register_payload = {
        "email": "logout_session@example.com",
        "full_name": "Logout Session",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "LogoutSessionOrg",
    }
    client.post("/api/auth/register", json=register_payload)
    
    login_payload = {
        "email": "logout_session@example.com",
        "password": "password123",
    }
    response = client.post("/api/auth/login", json=login_payload)
    token = response.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    
    # Verify session is active
    db = SessionLocal()
    session = db.query(AuthSession).filter(AuthSession.jwt_jti == jti).first()
    assert session is not None
    assert session.revoked_at is None
    
    # Logout
    response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Verify session is revoked
    db = SessionLocal()
    session = db.query(AuthSession).filter(AuthSession.jwt_jti == jti).first()
    assert session.revoked_at is not None
    assert session.revoked_reason == "logout"
    db.close()


def test_revoked_session_fails_auth(client):
    """Test that a revoked session fails authentication"""
    from jose import jwt
    from core.config import settings
    from core.database import SessionLocal
    
    # Register and login
    register_payload = {
        "email": "revoked_auth@example.com",
        "full_name": "Revoked Auth",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "RevokedAuthOrg",
    }
    client.post("/api/auth/register", json=register_payload)
    
    login_payload = {
        "email": "revoked_auth@example.com",
        "password": "password123",
    }
    response = client.post("/api/auth/login", json=login_payload)
    token = response.json()["access_token"]
    
    # Verify we can access /me endpoint with valid token
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Revoke the session manually
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    
    db = SessionLocal()
    revoke_session(db=db, jwt_jti=jti, reason="test_revocation")
    db.close()
    
    # Try to access /me endpoint with revoked token
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower()


def test_expired_session_fails_auth(client):
    """Test that an expired session fails authentication"""
    from jose import jwt
    from core.config import settings
    from core.database import SessionLocal
    
    # Register and login
    register_payload = {
        "email": "expired_auth@example.com",
        "full_name": "Expired Auth",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "ExpiredAuthOrg",
    }
    client.post("/api/auth/register", json=register_payload)
    
    login_payload = {
        "email": "expired_auth@example.com",
        "password": "password123",
    }
    response = client.post("/api/auth/login", json=login_payload)
    token = response.json()["access_token"]
    
    # Manually expire the session
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    
    db = SessionLocal()
    session = db.query(AuthSession).filter(AuthSession.jwt_jti == jti).first()
    session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Set to past
    db.commit()
    db.close()
    
    # Try to access /me endpoint with expired session
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_cleanup_expired_sessions(client):
    """Test cleanup of expired sessions"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    # Create a user
    register_payload = {
        "email": "cleanup_test@example.com",
        "full_name": "Cleanup Test",
        "password": "password123",
        "role": "dispatcher",
        "organization_name": "CleanupTestOrg",
    }
    response = client.post("/api/auth/register", json=register_payload)
    user = db.query(User).filter(User.email == "cleanup_test@example.com").first()
    
    # Create sessions with different expiry dates
    jti1 = str(uuid.uuid4())
    jti2 = str(uuid.uuid4())
    jti3 = str(uuid.uuid4())
    
    # Old expired session (35 days ago)
    old_expired = datetime.utcnow() - timedelta(days=35)
    create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti1, expires_at=old_expired)
    
    # Recent expired session (5 days ago)
    recent_expired = datetime.utcnow() - timedelta(days=5)
    create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti2, expires_at=recent_expired)
    
    # Active session
    active_expires = datetime.utcnow() + timedelta(hours=1)
    create_session(db=db, org_id=user.org_id, user_id=user.id, jwt_jti=jti3, expires_at=active_expires)
    
    # Cleanup sessions older than 30 days
    count = cleanup_expired_sessions(db=db, older_than_days=30)
    assert count == 1
    
    # Verify only old session was deleted
    assert db.query(AuthSession).filter(AuthSession.jwt_jti == jti1).first() is None
    assert db.query(AuthSession).filter(AuthSession.jwt_jti == jti2).first() is not None
    assert db.query(AuthSession).filter(AuthSession.jwt_jti == jti3).first() is not None
    
    db.close()
