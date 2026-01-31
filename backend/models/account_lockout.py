"""Account lockout model for FedRAMP AC-7 compliance"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.orm import relationship

from core.database import Base


class AccountLockout(Base):
    """Tracks account lockout state and failed login attempts for FedRAMP AC-7 compliance"""
    __tablename__ = "account_lockouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True, index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    unlock_reason = Column(String, nullable=True)  # e.g., "admin_unlock", "timeout", "successful_login"
    last_failed_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="lockout")

    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def increment_failed_attempts(self, max_attempts: int = 5, lockout_duration_minutes: int = 30) -> bool:
        """
        Increment failed attempts and lock account if threshold reached.
        Returns True if account was locked, False otherwise.
        """
        self.failed_attempts += 1
        self.last_failed_attempt_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        if self.failed_attempts >= max_attempts:
            self.locked_at = datetime.now(timezone.utc)
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_duration_minutes)
            return True
        return False

    def reset_failed_attempts(self) -> None:
        """Reset failed attempts on successful login"""
        self.failed_attempts = 0
        self.locked_until = None
        self.locked_at = None
        self.unlock_reason = "successful_login"
        self.updated_at = datetime.now(timezone.utc)

    def unlock(self, reason: str = "admin_unlock", admin_user_id: int = None) -> None:
        """Unlock account manually (admin action)"""
        self.locked_until = None
        self.locked_at = None
        self.failed_attempts = 0
        self.unlock_reason = reason
        self.updated_at = datetime.now(timezone.utc)


class AccountLockoutAudit(Base):
    """Audit log for account lockout events (FedRAMP requirement)"""
    __tablename__ = "account_lockout_audits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # e.g., "lockout", "unlock", "failed_attempt", "reset"
    reason = Column(String, nullable=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who unlocked
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="lockout_audits")
    admin_user = relationship("User", foreign_keys=[admin_user_id])
