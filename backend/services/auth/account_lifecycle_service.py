"""
Account Lifecycle Management Service
Implements FedRAMP AC-2(2) and AC-2(3) requirements for automated account management.

Features:
- Automatic account deactivation after 90 days of inactivity
- Notification system (30, 15, 7 days before deactivation)
- Automated account removal for terminated employees
- Periodic access reviews
- Account activity tracking
- Re-activation workflow
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.user import User, AccountStatus
from services.email.email_transport_service import send_notification_email
from core.logger import logger
from core.config import settings


class AccountLifecycleService:
    """Service for managing user account lifecycle per FedRAMP requirements"""
    
    # Configuration constants
    INACTIVITY_THRESHOLD_DAYS = 90
    NOTIFICATION_DAYS = [30, 15, 7]  # Days before deactivation to notify
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_activity(self, user_id: int) -> None:
        """
        Update last_activity_at timestamp for a user.
        Called on login, API access, or any authenticated activity.
        
        Args:
            user_id: User ID to update
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_activity_at = datetime.utcnow()
                # Reactivate inactive accounts on activity
                if user.account_status == AccountStatus.INACTIVE.value:
                    user.account_status = AccountStatus.ACTIVE.value
                    user.deactivation_scheduled_at = None
                    user.deactivation_reason = None
                    logger.info(
                        f"Account {user_id} ({user.email}) reactivated due to activity",
                        extra={
                            "user_id": user_id,
                            "email": user.email,
                            "org_id": user.org_id,
                            "event_type": "account.reactivated",
                        }
                    )
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update activity for user {user_id}: {e}", exc_info=True)
            self.db.rollback()
    
    def check_inactive_accounts(self) -> Dict[str, Any]:
        """
        Check for accounts that should be notified or deactivated.
        Returns summary of actions taken.
        
        Returns:
            Dict with counts of accounts processed
        """
        now = datetime.utcnow()
        threshold_date = now - timedelta(days=self.INACTIVITY_THRESHOLD_DAYS)
        
        results = {
            "notifications_sent": 0,
            "accounts_disabled": 0,
            "errors": 0,
        }
        
        try:
            # Find active accounts with no recent activity
            inactive_accounts = self.db.query(User).filter(
                and_(
                    User.account_status == AccountStatus.ACTIVE.value,
                    or_(
                        User.last_activity_at < threshold_date,
                        and_(
                            User.last_activity_at.is_(None),
                            User.created_at < threshold_date
                        )
                    )
                )
            ).all()
            
            for user in inactive_accounts:
                try:
                    # Determine days until deactivation
                    last_activity = user.last_activity_at or user.created_at
                    days_inactive = (now - last_activity).days
                    days_until_deactivation = self.INACTIVITY_THRESHOLD_DAYS - days_inactive
                    
                    # Check if we should send notification
                    if days_until_deactivation in self.NOTIFICATION_DAYS:
                        self._send_deactivation_warning(user, days_until_deactivation)
                        results["notifications_sent"] += 1
                    
                    # Disable if threshold reached
                    if days_inactive >= self.INACTIVITY_THRESHOLD_DAYS:
                        self._disable_account(
                            user,
                            reason="inactivity",
                            details=f"Account inactive for {days_inactive} days"
                        )
                        results["accounts_disabled"] += 1
                    
                except Exception as e:
                    logger.error(
                        f"Error processing inactive account {user.id}: {e}",
                        exc_info=True,
                        extra={"user_id": user.id, "email": user.email}
                    )
                    results["errors"] += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error checking inactive accounts: {e}", exc_info=True)
            self.db.rollback()
            results["errors"] += 1
        
        return results
    
    def _send_deactivation_warning(self, user: User, days_until: int) -> None:
        """
        Send email notification warning about upcoming deactivation.
        
        Args:
            user: User to notify
            days_until: Days until deactivation
        """
        try:
            subject = f"Account Deactivation Warning - {days_until} Days Remaining"
            html_body = f"""
            <html>
            <body>
                <h2>Account Deactivation Warning</h2>
                <p>Dear {user.full_name or user.email},</p>
                <p>Your account has been inactive for an extended period. If no activity is detected within 
                <strong>{days_until} days</strong>, your account will be automatically deactivated per our 
                security policy (FedRAMP AC-2(2), AC-2(3)).</p>
                <p>To prevent deactivation, simply log in to your account or use any system feature.</p>
                <p>If you have any questions, please contact your system administrator.</p>
                <hr>
                <p><small>This is an automated message from the account lifecycle management system.</small></p>
            </body>
            </html>
            """
            
            send_notification_email(
                to=user.email,
                subject=subject,
                html_body=html_body,
                reply_to=getattr(settings, "SUPPORT_EMAIL", None)
            )
            
            logger.info(
                f"Deactivation warning sent to {user.email} ({days_until} days remaining)",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "org_id": user.org_id,
                    "days_until": days_until,
                    "event_type": "account.deactivation_warning",
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to send deactivation warning to {user.email}: {e}",
                exc_info=True,
                extra={"user_id": user.id, "email": user.email}
            )
    
    def _disable_account(
        self,
        user: User,
        reason: str,
        details: Optional[str] = None
    ) -> None:
        """
        Disable an account and log the action.
        
        Args:
            user: User to disable
            reason: Reason for deactivation (inactivity, termination, etc.)
            details: Additional details
        """
        try:
            user.account_status = AccountStatus.DISABLED.value
            user.deactivation_reason = reason
            user.deactivation_scheduled_at = None  # Clear any scheduled deactivation
            
            # Revoke all active sessions
            from services.auth.session_service import revoke_all_sessions_for_user
            revoke_all_sessions_for_user(self.db, user.id, reason="account_disabled")
            
            logger.warning(
                f"Account disabled: {user.email} - Reason: {reason}",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "org_id": user.org_id,
                    "reason": reason,
                    "details": details,
                    "event_type": "account.disabled",
                }
            )
            
            # Send notification email
            try:
                subject = "Account Deactivated - Inactivity"
                html_body = f"""
                <html>
                <body>
                    <h2>Account Deactivated</h2>
                    <p>Dear {user.full_name or user.email},</p>
                    <p>Your account has been automatically deactivated due to inactivity 
                    (no activity for {self.INACTIVITY_THRESHOLD_DAYS} days).</p>
                    <p>To reactivate your account, please contact your system administrator.</p>
                    <hr>
                    <p><small>This is an automated message from the account lifecycle management system.</small></p>
                </body>
                </html>
                """
                
                send_notification_email(
                    to=user.email,
                    subject=subject,
                    html_body=html_body,
                    reply_to=getattr(settings, "SUPPORT_EMAIL", None)
                )
            except Exception as e:
                logger.error(f"Failed to send deactivation email to {user.email}: {e}")
            
        except Exception as e:
            logger.error(
                f"Failed to disable account {user.id}: {e}",
                exc_info=True,
                extra={"user_id": user.id, "email": user.email}
            )
            raise
    
    def terminate_employee(self, user_id: int, reason: str, terminated_by: int) -> None:
        """
        Terminate an employee account immediately.
        Used when an employee leaves the organization.
        
        Args:
            user_id: User ID to terminate
            reason: Reason for termination
            terminated_by: User ID of admin performing termination
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user.account_status = AccountStatus.TERMINATED.value
            user.deactivation_reason = f"Termination: {reason}"
            user.deactivation_scheduled_at = datetime.utcnow()
            
            # Revoke all active sessions immediately
            from services.auth.session_service import revoke_all_sessions_for_user
            revoke_all_sessions_for_user(self.db, user.id, reason="employee_termination")
            
            logger.warning(
                f"Employee account terminated: {user.email}",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "org_id": user.org_id,
                    "reason": reason,
                    "terminated_by": terminated_by,
                    "event_type": "account.terminated",
                }
            )
            
            self.db.commit()
            
        except Exception as e:
            logger.error(
                f"Failed to terminate account {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "terminated_by": terminated_by}
            )
            self.db.rollback()
            raise
    
    def reactivate_account(
        self,
        user_id: int,
        reactivated_by: int,
        reason: Optional[str] = None
    ) -> None:
        """
        Reactivate a disabled or inactive account.
        
        Args:
            user_id: User ID to reactivate
            reactivated_by: User ID of admin performing reactivation
            reason: Reason for reactivation
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if user.account_status == AccountStatus.ACTIVE.value:
                logger.info(f"Account {user_id} already active, skipping reactivation")
                return
            
            user.account_status = AccountStatus.ACTIVE.value
            user.deactivation_reason = None
            user.deactivation_scheduled_at = None
            user.last_activity_at = datetime.utcnow()
            
            logger.info(
                f"Account reactivated: {user.email}",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "org_id": user.org_id,
                    "reason": reason,
                    "reactivated_by": reactivated_by,
                    "event_type": "account.reactivated",
                }
            )
            
            self.db.commit()
            
        except Exception as e:
            logger.error(
                f"Failed to reactivate account {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "reactivated_by": reactivated_by}
            )
            self.db.rollback()
            raise
    
    def generate_access_review_report(self, org_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a compliance report for access reviews.
        FedRAMP AC-2(3) requires periodic access reviews.
        
        Args:
            org_id: Optional organization ID to filter by
            
        Returns:
            Dict with report data
        """
        try:
            query = self.db.query(User)
            if org_id:
                query = query.filter(User.org_id == org_id)
            
            all_users = query.all()
            
            now = datetime.utcnow()
            threshold_date = now - timedelta(days=self.INACTIVITY_THRESHOLD_DAYS)
            
            report = {
                "generated_at": now.isoformat(),
                "total_accounts": len(all_users),
                "active": 0,
                "inactive": 0,
                "disabled": 0,
                "terminated": 0,
                "accounts_requiring_review": [],
            }
            
            for user in all_users:
                status = user.account_status
                if status == AccountStatus.ACTIVE.value:
                    report["active"] += 1
                    # Check if approaching inactivity threshold
                    last_activity = user.last_activity_at or user.created_at
                    days_inactive = (now - last_activity).days
                    if days_inactive >= (self.INACTIVITY_THRESHOLD_DAYS - 30):
                        report["accounts_requiring_review"].append({
                            "user_id": user.id,
                            "email": user.email,
                            "full_name": user.full_name,
                            "days_inactive": days_inactive,
                            "last_activity": last_activity.isoformat() if last_activity else None,
                        })
                elif status == AccountStatus.INACTIVE.value:
                    report["inactive"] += 1
                elif status == AccountStatus.DISABLED.value:
                    report["disabled"] += 1
                elif status == AccountStatus.TERMINATED.value:
                    report["terminated"] += 1
            
            logger.info(
                f"Access review report generated",
                extra={
                    "org_id": org_id,
                    "total_accounts": report["total_accounts"],
                    "event_type": "compliance.access_review_report",
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate access review report: {e}", exc_info=True)
            raise
    
    def get_account_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed account status information.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with account status details
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            now = datetime.utcnow()
            last_activity = user.last_activity_at or user.created_at
            days_inactive = (now - last_activity).days if last_activity else None
            
            return {
                "user_id": user.id,
                "email": user.email,
                "account_status": user.account_status,
                "last_activity_at": user.last_activity_at.isoformat() if user.last_activity_at else None,
                "days_inactive": days_inactive,
                "deactivation_reason": user.deactivation_reason,
                "deactivation_scheduled_at": user.deactivation_scheduled_at.isoformat() if user.deactivation_scheduled_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get account status for {user_id}: {e}", exc_info=True)
            raise
