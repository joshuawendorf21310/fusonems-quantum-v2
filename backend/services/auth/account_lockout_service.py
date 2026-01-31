"""Account lockout service for FedRAMP AC-7 compliance"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Request

from sqlalchemy.orm import Session

from core.logger import logger
from models.account_lockout import AccountLockout, AccountLockoutAudit
from models.user import User
from utils.audit import record_audit


class AccountLockoutService:
    """Service for managing account lockouts per FedRAMP AC-7 requirements"""

    # FedRAMP AC-7 requirements
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    @staticmethod
    def record_failed_attempt(
        db: Session,
        user: User,
        request: Optional[Request] = None,
    ) -> bool:
        """
        Record a failed login attempt and lock account if threshold reached.
        Returns True if account was locked, False otherwise.
        """
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user.id).first()
        
        if not lockout:
            lockout = AccountLockout(user_id=user.id, failed_attempts=0)
            db.add(lockout)
            db.flush()

        # Check if account is already locked
        if lockout.is_locked():
            logger.warning(f"Login attempt on locked account: user_id={user.id}, email={user.email}")
            AccountLockoutService._audit_lockout_event(
                db=db,
                user=user,
                action="failed_attempt_locked",
                reason="Attempt on locked account",
                request=request,
            )
            return True

        # Increment failed attempts
        was_locked = lockout.increment_failed_attempts(
            max_attempts=AccountLockoutService.MAX_FAILED_ATTEMPTS,
            lockout_duration_minutes=AccountLockoutService.LOCKOUT_DURATION_MINUTES,
        )

        db.commit()
        db.refresh(lockout)

        # Audit failed attempt
        AccountLockoutService._audit_lockout_event(
            db=db,
            user=user,
            action="failed_attempt",
            reason=f"Failed attempt {lockout.failed_attempts}/{AccountLockoutService.MAX_FAILED_ATTEMPTS}",
            request=request,
        )

        # If account was just locked, audit the lockout
        if was_locked:
            logger.warning(
                f"Account locked due to failed attempts: user_id={user.id}, "
                f"email={user.email}, locked_until={lockout.locked_until}"
            )
            AccountLockoutService._audit_lockout_event(
                db=db,
                user=user,
                action="lockout",
                reason=f"Exceeded {AccountLockoutService.MAX_FAILED_ATTEMPTS} failed attempts",
                request=request,
            )
            
            # Also log to forensic audit
            if request:
                try:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="account_lockout",
                        resource="user",
                        outcome="Blocked",
                        classification="NON_PHI",
                        reason_code="ACCOUNT_LOCKED",
                        after_state={
                            "failed_attempts": lockout.failed_attempts,
                            "locked_until": lockout.locked_until.isoformat() if lockout.locked_until else None,
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to record forensic audit for lockout: {e}", exc_info=True)

        return was_locked

    @staticmethod
    def record_successful_login(
        db: Session,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Reset failed attempts on successful login"""
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user.id).first()
        
        if lockout and lockout.failed_attempts > 0:
            lockout.reset_failed_attempts()
            db.commit()
            
            AccountLockoutService._audit_lockout_event(
                db=db,
                user=user,
                action="reset",
                reason="Successful login",
                request=request,
            )

    @staticmethod
    def is_account_locked(db: Session, user_id: int) -> bool:
        """Check if account is currently locked"""
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
        if not lockout:
            return False
        return lockout.is_locked()

    @staticmethod
    def get_lockout_info(db: Session, user_id: int) -> Optional[dict]:
        """Get lockout information for an account"""
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
        if not lockout:
            return None
        
        return {
            "is_locked": lockout.is_locked(),
            "failed_attempts": lockout.failed_attempts,
            "locked_until": lockout.locked_until.isoformat() if lockout.locked_until else None,
            "locked_at": lockout.locked_at.isoformat() if lockout.locked_at else None,
            "last_failed_attempt_at": lockout.last_failed_attempt_at.isoformat() if lockout.last_failed_attempt_at else None,
        }

    @staticmethod
    def unlock_account(
        db: Session,
        user_id: int,
        admin_user: User,
        reason: str = "admin_unlock",
        request: Optional[Request] = None,
    ) -> bool:
        """
        Unlock an account (admin action).
        Returns True if account was unlocked, False if not found or not locked.
        """
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
        
        if not lockout:
            return False
        
        if not lockout.is_locked():
            return False

        lockout.unlock(reason=reason, admin_user_id=admin_user.id)
        db.commit()
        db.refresh(lockout)

        # Audit unlock action
        AccountLockoutService._audit_lockout_event(
            db=db,
            user=lockout.user,
            action="unlock",
            reason=f"{reason} by admin {admin_user.email}",
            admin_user_id=admin_user.id,
            request=request,
        )

        # Also log to forensic audit
        if request:
            try:
                record_audit(
                    db=db,
                    request=request,
                    user=admin_user,
                    action="account_unlock",
                    resource="user",
                    outcome="Allowed",
                    classification="NON_PHI",
                    reason_code="ADMIN_UNLOCK",
                    after_state={
                        "unlocked_user_id": user_id,
                        "reason": reason,
                    },
                )
            except Exception as e:
                logger.error(f"Failed to record forensic audit for unlock: {e}", exc_info=True)

        logger.info(f"Account unlocked by admin: user_id={user_id}, admin={admin_user.email}")
        return True

    @staticmethod
    def cleanup_expired_lockouts(db: Session) -> int:
        """
        Clean up expired lockouts (accounts that have passed lockout duration).
        Returns count of cleaned up lockouts.
        """
        now = datetime.now(timezone.utc)
        expired_lockouts = (
            db.query(AccountLockout)
            .filter(
                AccountLockout.locked_until.isnot(None),
                AccountLockout.locked_until < now,
            )
            .all()
        )

        count = 0
        for lockout in expired_lockouts:
            lockout.unlock(reason="timeout")
            count += 1

        if count > 0:
            db.commit()
            logger.info(f"Cleaned up {count} expired lockouts")

        return count

    @staticmethod
    def _audit_lockout_event(
        db: Session,
        user: User,
        action: str,
        reason: Optional[str] = None,
        admin_user_id: Optional[int] = None,
        request: Optional[Request] = None,
    ) -> None:
        """Record lockout event in audit log"""
        try:
            ip_address = None
            user_agent = None
            if request and request.client:
                ip_address = request.client.host
            if request:
                user_agent = request.headers.get("user-agent")

            audit_entry = AccountLockoutAudit(
                user_id=user.id,
                action=action,
                reason=reason,
                admin_user_id=admin_user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to record lockout audit event: {e}", exc_info=True)
            db.rollback()
