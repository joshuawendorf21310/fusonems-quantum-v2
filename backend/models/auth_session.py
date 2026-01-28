from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class AuthSession(Base):
    """Server-side session store for JWT token revocation and tracking"""
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    jwt_jti = Column(String, unique=True, nullable=False, index=True)  # JWT ID claim
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_reason = Column(String, nullable=True)  # e.g., "logout", "password_reset", "admin_ban"
    csrf_secret = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
