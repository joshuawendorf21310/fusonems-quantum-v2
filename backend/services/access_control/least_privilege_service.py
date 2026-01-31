"""
AC-6: Least Privilege Service

Implements privilege review automation, excessive permission detection, and
privilege escalation tracking for FedRAMP AC-6 compliance.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.access_control import (
    PrivilegeAssignment,
    PrivilegeEscalation,
    PrivilegeReviewStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from models.user import User
from utils.logger import logger


class LeastPrivilegeService:
    """Service for managing least privilege assignments and reviews"""
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def request_privilege(
        self,
        user_id: int,
        privilege_name: str,
        privilege_type: str,
        justification: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        business_need: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        review_frequency_days: int = 90,
    ) -> PrivilegeAssignment:
        """
        Request a privilege assignment for a user.
        
        Args:
            user_id: User requesting the privilege
            privilege_name: Name of the privilege
            privilege_type: Type of privilege (role, permission, capability)
            justification: Justification for the privilege
            resource_type: Type of resource (optional)
            resource_id: Resource ID (optional)
            business_need: Business need description (optional)
            expires_at: Expiration date (optional)
            review_frequency_days: Days between reviews
        
        Returns:
            Created PrivilegeAssignment
        """
        assignment = PrivilegeAssignment(
            org_id=self.org_id,
            user_id=user_id,
            privilege_name=privilege_name,
            privilege_type=privilege_type,
            resource_type=resource_type,
            resource_id=resource_id,
            justification=justification,
            business_need=business_need,
            requested_by=self.user_id or user_id,
            status=PrivilegeReviewStatus.PENDING.value,
            expires_at=expires_at,
            review_frequency_days=review_frequency_days,
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log
        self._audit_log(
            action="request_privilege",
            resource_type="privilege_assignment",
            resource_id=str(assignment.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "user_id": user_id,
                "privilege_name": privilege_name,
                "privilege_type": privilege_type,
            }
        )
        
        logger.info(f"Privilege requested: {privilege_name} for user {user_id}")
        return assignment
    
    def approve_privilege(
        self,
        assignment_id: int,
        approved_by: int,
        expires_at: Optional[datetime] = None,
    ) -> PrivilegeAssignment:
        """
        Approve a privilege assignment.
        
        Args:
            assignment_id: Privilege assignment ID
            approved_by: User approving the privilege
            expires_at: Optional expiration date
        
        Returns:
            Updated PrivilegeAssignment
        """
        assignment = self.db.query(PrivilegeAssignment).filter(
            and_(
                PrivilegeAssignment.id == assignment_id,
                PrivilegeAssignment.org_id == self.org_id,
            )
        ).first()
        
        if not assignment:
            raise ValueError(f"Privilege assignment {assignment_id} not found")
        
        assignment.status = PrivilegeReviewStatus.APPROVED.value
        assignment.approved_by = approved_by
        assignment.granted_at = datetime.now(timezone.utc)
        if expires_at:
            assignment.expires_at = expires_at
        
        # Set next review date
        assignment.next_review_due = datetime.now(timezone.utc) + timedelta(
            days=assignment.review_frequency_days
        )
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log
        self._audit_log(
            action="approve_privilege",
            resource_type="privilege_assignment",
            resource_id=str(assignment_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "approved_by": approved_by,
                "privilege_name": assignment.privilege_name,
            }
        )
        
        return assignment
    
    def revoke_privilege(
        self,
        assignment_id: int,
        revoked_by: int,
        revocation_reason: str,
    ) -> PrivilegeAssignment:
        """
        Revoke a privilege assignment.
        
        Args:
            assignment_id: Privilege assignment ID
            revoked_by: User revoking the privilege
            revocation_reason: Reason for revocation
        
        Returns:
            Updated PrivilegeAssignment
        """
        assignment = self.db.query(PrivilegeAssignment).filter(
            and_(
                PrivilegeAssignment.id == assignment_id,
                PrivilegeAssignment.org_id == self.org_id,
            )
        ).first()
        
        if not assignment:
            raise ValueError(f"Privilege assignment {assignment_id} not found")
        
        assignment.status = PrivilegeReviewStatus.REVOKED.value
        assignment.revoked_by = revoked_by
        assignment.revoked_at = datetime.now(timezone.utc)
        assignment.revocation_reason = revocation_reason
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log
        self._audit_log(
            action="revoke_privilege",
            resource_type="privilege_assignment",
            resource_id=str(assignment_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "revoked_by": revoked_by,
                "revocation_reason": revocation_reason,
            }
        )
        
        return assignment
    
    def request_escalation(
        self,
        user_id: int,
        escalated_privilege: str,
        reason: str,
        duration_hours: int = 4,
        task_description: Optional[str] = None,
        privilege_id: Optional[int] = None,
    ) -> PrivilegeEscalation:
        """
        Request temporary privilege escalation.
        
        Args:
            user_id: User requesting escalation
            escalated_privilege: Privilege to escalate
            reason: Reason for escalation
            duration_hours: Duration in hours
            task_description: Description of task
            privilege_id: Related privilege assignment ID
        
        Returns:
            Created PrivilegeEscalation
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        escalation = PrivilegeEscalation(
            org_id=self.org_id,
            user_id=user_id,
            privilege_id=privilege_id,
            escalated_privilege=escalated_privilege,
            reason=reason,
            task_description=task_description,
            requested_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
        )
        
        self.db.add(escalation)
        self.db.commit()
        self.db.refresh(escalation)
        
        # Audit log
        self._audit_log(
            action="request_privilege_escalation",
            resource_type="privilege_escalation",
            resource_id=str(escalation.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "user_id": user_id,
                "escalated_privilege": escalated_privilege,
                "expires_at": expires_at.isoformat(),
            }
        )
        
        logger.info(f"Privilege escalation requested: {escalated_privilege} for user {user_id}")
        return escalation
    
    def approve_escalation(
        self,
        escalation_id: int,
        approved_by: int,
    ) -> PrivilegeEscalation:
        """Approve a privilege escalation"""
        escalation = self.db.query(PrivilegeEscalation).filter(
            and_(
                PrivilegeEscalation.id == escalation_id,
                PrivilegeEscalation.org_id == self.org_id,
            )
        ).first()
        
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.approved_by = approved_by
        escalation.approved_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(escalation)
        
        # Audit log
        self._audit_log(
            action="approve_privilege_escalation",
            resource_type="privilege_escalation",
            resource_id=str(escalation_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"approved_by": approved_by}
        )
        
        return escalation
    
    def revoke_escalation(
        self,
        escalation_id: int,
        revoked_by: int,
    ) -> PrivilegeEscalation:
        """Revoke a privilege escalation"""
        escalation = self.db.query(PrivilegeEscalation).filter(
            and_(
                PrivilegeEscalation.id == escalation_id,
                PrivilegeEscalation.org_id == self.org_id,
            )
        ).first()
        
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.is_active = False
        escalation.revoked_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(escalation)
        
        # Audit log
        self._audit_log(
            action="revoke_privilege_escalation",
            resource_type="privilege_escalation",
            resource_id=str(escalation_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"revoked_by": revoked_by}
        )
        
        return escalation
    
    def detect_excessive_privileges(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Detect users with excessive privileges.
        
        Returns list of users with potential excessive privileges.
        """
        query = self.db.query(
            PrivilegeAssignment.user_id,
            User.email,
            func.count(PrivilegeAssignment.id).label('privilege_count')
        ).join(
            User, PrivilegeAssignment.user_id == User.id
        ).filter(
            and_(
                PrivilegeAssignment.org_id == self.org_id,
                PrivilegeAssignment.status == PrivilegeReviewStatus.APPROVED.value,
                or_(
                    PrivilegeAssignment.expires_at.is_(None),
                    PrivilegeAssignment.expires_at > datetime.now(timezone.utc),
                ),
            )
        )
        
        if user_id:
            query = query.filter(PrivilegeAssignment.user_id == user_id)
        
        results = query.group_by(
            PrivilegeAssignment.user_id,
            User.email
        ).having(
            func.count(PrivilegeAssignment.id) > 10  # Threshold: more than 10 privileges
        ).all()
        
        excessive = []
        for user_id, email, count in results:
            excessive.append({
                "user_id": user_id,
                "email": email,
                "privilege_count": count,
                "reason": "exceeds_threshold",
            })
        
        return excessive
    
    def get_pending_reviews(self) -> List[PrivilegeAssignment]:
        """Get privileges pending review"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(PrivilegeAssignment).filter(
            and_(
                PrivilegeAssignment.org_id == self.org_id,
                PrivilegeAssignment.status == PrivilegeReviewStatus.APPROVED.value,
                or_(
                    PrivilegeAssignment.next_review_due <= now,
                    PrivilegeAssignment.next_review_due.is_(None),
                ),
            )
        ).all()
    
    def review_privilege(
        self,
        assignment_id: int,
        reviewed_by: int,
        keep_privilege: bool,
        review_notes: Optional[str] = None,
    ) -> PrivilegeAssignment:
        """
        Review a privilege assignment.
        
        Args:
            assignment_id: Privilege assignment ID
            reviewed_by: User performing the review
            keep_privilege: Whether to keep the privilege
            review_notes: Review notes
        
        Returns:
            Updated PrivilegeAssignment
        """
        assignment = self.db.query(PrivilegeAssignment).filter(
            and_(
                PrivilegeAssignment.id == assignment_id,
                PrivilegeAssignment.org_id == self.org_id,
            )
        ).first()
        
        if not assignment:
            raise ValueError(f"Privilege assignment {assignment_id} not found")
        
        assignment.last_reviewed_at = datetime.now(timezone.utc)
        assignment.next_review_due = datetime.now(timezone.utc) + timedelta(
            days=assignment.review_frequency_days
        )
        
        if not keep_privilege:
            assignment.status = PrivilegeReviewStatus.REVOKED.value
            assignment.revoked_at = datetime.now(timezone.utc)
            assignment.revoked_by = reviewed_by
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Audit log
        self._audit_log(
            action="review_privilege",
            resource_type="privilege_assignment",
            resource_id=str(assignment_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "reviewed_by": reviewed_by,
                "keep_privilege": keep_privilege,
                "review_notes": review_notes,
            }
        )
        
        return assignment
    
    def get_user_privileges(self, user_id: int) -> List[PrivilegeAssignment]:
        """Get all active privileges for a user"""
        return self.db.query(PrivilegeAssignment).filter(
            and_(
                PrivilegeAssignment.org_id == self.org_id,
                PrivilegeAssignment.user_id == user_id,
                PrivilegeAssignment.status == PrivilegeReviewStatus.APPROVED.value,
                or_(
                    PrivilegeAssignment.expires_at.is_(None),
                    PrivilegeAssignment.expires_at > datetime.now(timezone.utc),
                ),
            )
        ).all()
    
    def get_active_escalations(self, user_id: Optional[int] = None) -> List[PrivilegeEscalation]:
        """Get active privilege escalations"""
        query = self.db.query(PrivilegeEscalation).filter(
            and_(
                PrivilegeEscalation.org_id == self.org_id,
                PrivilegeEscalation.is_active == True,
                PrivilegeEscalation.expires_at > datetime.now(timezone.utc),
            )
        )
        
        if user_id:
            query = query.filter(PrivilegeEscalation.user_id == user_id)
        
        return query.all()
    
    def _audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: AuditOutcome,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create audit log entry"""
        audit = ComprehensiveAuditLog(
            org_id=self.org_id,
            user_id=self.user_id,
            event_type=AuditEventType.AUTHORIZATION.value,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome.value,
            metadata=metadata or {},
        )
        self.db.add(audit)
        self.db.commit()
