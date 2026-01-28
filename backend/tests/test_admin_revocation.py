"""Test script for admin session revocation functionality"""
from core.database import SessionLocal
from models.user import User
from models.auth_session import AuthSession


def test_admin_revoke_endpoint(client):
    """Integration test for admin session revocation endpoint"""
    from jose import jwt
    from core.config import settings
    
    # Create admin user
    admin_register = {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "adminpass",
        "role": "admin",
        "organization_name": "AdminOrg",
    }
    response = client.post("/api/auth/register", json=admin_register)
    assert response.status_code == 201
    admin_token = response.json()["access_token"]
    
    # Create regular user
    user_register = {
        "email": "regular@example.com",
        "full_name": "Regular User",
        "password": "userpass",
        "role": "dispatcher",
        "organization_name": "AdminOrg",
    }
    response = client.post("/api/auth/register", json=user_register)
    assert response.status_code == 201
    
    # Get user ID
    db = SessionLocal()
    user = db.query(User).filter(User.email == "regular@example.com").first()
    user_id = user.id
    
    # User logs in multiple times (creates multiple sessions)
    user_login = {"email": "regular@example.com", "password": "userpass"}
    tokens = []
    for i in range(3):
        response = client.post("/api/auth/login", json=user_login)
        assert response.status_code == 200
        tokens.append(response.json()["access_token"])
    
    # Verify user has 4 active sessions (1 from register + 3 from login)
    active_sessions = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None)
        )
        .count()
    )
    assert active_sessions == 4
    
    # Admin revokes all user sessions
    revoke_payload = {
        "user_id": user_id,
        "reason": "security_audit"
    }
    response = client.post(
        "/api/auth/admin/revoke-user-sessions",
        json=revoke_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["revoked_count"] == 4
    
    # Verify all sessions are revoked
    active_sessions = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None)
        )
        .count()
    )
    assert active_sessions == 0
    
    # Verify user tokens no longer work
    for token in tokens:
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
    
    # Verify revoked sessions have correct reason
    revoked_sessions = (
        db.query(AuthSession)
        .filter(AuthSession.user_id == user_id)
        .all()
    )
    for session in revoked_sessions:
        assert session.revoked_at is not None
        assert session.revoked_reason == "security_audit"
    
    db.close()
    
    print("✅ Admin revocation endpoint test passed!")


def test_non_admin_cannot_revoke(client):
    """Test that non-admin users cannot revoke sessions"""
    # Create two regular users in same org
    user1_register = {
        "email": "user1@example.com",
        "full_name": "User One",
        "password": "pass1",
        "role": "dispatcher",
        "organization_name": "TestOrg",
    }
    response = client.post("/api/auth/register", json=user1_register)
    assert response.status_code == 201
    user1_token = response.json()["access_token"]
    
    user2_register = {
        "email": "user2@example.com",
        "full_name": "User Two",
        "password": "pass2",
        "role": "dispatcher",
        "organization_name": "TestOrg",
    }
    response = client.post("/api/auth/register", json=user2_register)
    assert response.status_code == 201
    
    # Get user2 ID
    db = SessionLocal()
    user2 = db.query(User).filter(User.email == "user2@example.com").first()
    user2_id = user2.id
    db.close()
    
    # User1 (non-admin) tries to revoke user2's sessions
    revoke_payload = {
        "user_id": user2_id,
        "reason": "test"
    }
    response = client.post(
        "/api/auth/admin/revoke-user-sessions",
        json=revoke_payload,
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 403  # Forbidden
    
    print("✅ Non-admin revocation prevention test passed!")


if __name__ == "__main__":
    from tests.conftest import create_test_client, drop_test_db
    
    print("Running admin revocation tests...")
    client = create_test_client()
    
    try:
        test_admin_revoke_endpoint(client)
        drop_test_db()
        
        client = create_test_client()
        test_non_admin_cannot_revoke(client)
        
        print("\n✅ All admin revocation tests passed!")
    finally:
        drop_test_db()
