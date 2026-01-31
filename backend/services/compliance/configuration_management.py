"""
Configuration Management Service for FedRAMP CM-2, CM-3, CM-6 Compliance

FedRAMP Requirements:
- CM-2: Baseline Configurations - Establish and maintain baseline configurations
- CM-3: Configuration Change Control - Track and approve configuration changes
- CM-6: Configuration Settings - Establish and enforce security configuration settings

This service provides:
- Configuration baseline management
- Configuration change request workflow
- Change approval tracking
- Configuration drift detection
- Automated compliance checking
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.logger import logger
from models.configuration import (
    ConfigurationBaseline,
    ConfigurationChangeRequest,
    ConfigurationChangeApproval,
    ConfigurationComplianceStatus,
    ConfigurationBaselineStatus,
    ChangeRequestStatus,
    ChangeRequestPriority,
    ComplianceStatus,
    DriftSeverity,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class ConfigurationManagementService:
    """
    Service for managing configuration baselines, changes, and compliance.
    
    Implements FedRAMP CM-2, CM-3, CM-5, and CM-6 controls.
    
    CM-5: Access Restrictions for Change
    - Enforces role-based access controls for configuration changes
    - Requires approval for privileged changes
    - Logs all change access attempts
    """
    
    # Roles allowed to make configuration changes
    CHANGE_AUTHORIZED_ROLES = ['admin', 'ops_admin', 'founder', 'compliance']
    
    # Roles allowed to approve changes
    APPROVAL_AUTHORIZED_ROLES = ['admin', 'founder', 'compliance']
    
    # Critical changes that require multiple approvals
    CRITICAL_CHANGE_TYPES = ['security_settings', 'authentication', 'encryption', 'audit_config']
    
    @staticmethod
    def create_baseline(
        db: Session,
        org_id: int,
        name: str,
        configuration_snapshot: Dict,
        description: Optional[str] = None,
        version: str = "1.0",
        scope: Optional[List[str]] = None,
        created_by_user_id: Optional[int] = None,
        created_by_email: Optional[str] = None,
    ) -> ConfigurationBaseline:
        """
        Create a new configuration baseline (CM-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            name: Baseline name
            configuration_snapshot: Full configuration state as JSON
            description: Optional description
            version: Version string (e.g., "1.0")
            scope: List of components included in baseline
            created_by_user_id: User ID creating the baseline
            created_by_email: User email (denormalized)
            
        Returns:
            Created ConfigurationBaseline
        """
        baseline = ConfigurationBaseline(
            org_id=org_id,
            name=name,
            description=description,
            version=version,
            status=ConfigurationBaselineStatus.DRAFT.value,
            configuration_snapshot=configuration_snapshot,
            scope=scope or [],
            created_by_user_id=created_by_user_id,
            created_by_email=created_by_email,
        )
        
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=org_id,
            user_id=created_by_user_id,
            action="create_baseline",
            resource_type="configuration_baseline",
            resource_id=str(baseline.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "baseline_name": name,
                "version": version,
                "scope": scope,
            },
        )
        
        logger.info(
            "Created configuration baseline %s (version %s) for org %d",
            name,
            version,
            org_id,
        )
        
        return baseline
    
    @staticmethod
    def activate_baseline(
        db: Session,
        baseline_id: uuid.UUID,
        org_id: int,
        activated_by_user_id: Optional[int] = None,
    ) -> ConfigurationBaseline:
        """
        Activate a configuration baseline (CM-2).
        
        Deactivates other active baselines for the same organization.
        
        Args:
            db: Database session
            baseline_id: Baseline ID to activate
            org_id: Organization ID
            activated_by_user_id: User ID activating the baseline
            
        Returns:
            Activated ConfigurationBaseline
            
        Raises:
            ValueError: If baseline not found or invalid
        """
        baseline = db.query(ConfigurationBaseline).filter(
            ConfigurationBaseline.id == baseline_id,
            ConfigurationBaseline.org_id == org_id,
        ).first()
        
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} not found")
        
        if baseline.status != ConfigurationBaselineStatus.DRAFT.value:
            raise ValueError(f"Baseline must be in DRAFT status to activate")
        
        # Deactivate other active baselines
        db.query(ConfigurationBaseline).filter(
            ConfigurationBaseline.org_id == org_id,
            ConfigurationBaseline.status == ConfigurationBaselineStatus.ACTIVE.value,
        ).update({
            "status": ConfigurationBaselineStatus.SUPERSEDED.value,
            "archived_at": datetime.now(timezone.utc),
        })
        
        # Activate this baseline
        baseline.status = ConfigurationBaselineStatus.ACTIVE.value
        baseline.activated_at = datetime.now(timezone.utc)
        baseline.activated_by_user_id = activated_by_user_id
        
        db.commit()
        db.refresh(baseline)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=org_id,
            user_id=activated_by_user_id,
            action="activate_baseline",
            resource_type="configuration_baseline",
            resource_id=str(baseline_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "baseline_name": baseline.name,
                "version": baseline.version,
            },
        )
        
        logger.info(
            "Activated configuration baseline %s (version %s) for org %d",
            baseline.name,
            baseline.version,
            org_id,
        )
        
        return baseline
    
    @staticmethod
    def check_change_permission(
        db: Session,
        user_id: int,
        org_id: int,
        change_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has permission to make configuration changes (CM-5).
        
        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            change_type: Type of change (optional, for critical change checks)
            
        Returns:
            Tuple of (has_permission, error_message)
        """
        from models.user import User
        
        user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
        
        if not user:
            return False, "User not found"
        
        # Check if user role is authorized
        if user.role.lower() not in [r.lower() for r in ConfigurationManagementService.CHANGE_AUTHORIZED_ROLES]:
            # Log unauthorized access attempt
            ConfigurationManagementService._log_audit(
                db=db,
                org_id=org_id,
                user_id=user_id,
                action="change_request_denied",
                resource_type="configuration_change",
                resource_id=None,
                outcome=AuditOutcome.DENIED.value,
                metadata={
                    "reason": "insufficient_permissions",
                    "user_role": user.role,
                    "change_type": change_type,
                },
            )
            return False, f"User role '{user.role}' is not authorized to make configuration changes"
        
        return True, None
    
    @staticmethod
    def check_approval_permission(
        db: Session,
        user_id: int,
        org_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has permission to approve configuration changes (CM-5).
        
        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            Tuple of (has_permission, error_message)
        """
        from models.user import User
        
        user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
        
        if not user:
            return False, "User not found"
        
        # Check if user role is authorized for approval
        if user.role.lower() not in [r.lower() for r in ConfigurationManagementService.APPROVAL_AUTHORIZED_ROLES]:
            return False, f"User role '{user.role}' is not authorized to approve configuration changes"
        
        return True, None
    
    @staticmethod
    def create_change_request(
        db: Session,
        org_id: int,
        title: str,
        description: str,
        configuration_changes: Dict,
        change_reason: str,
        priority: ChangeRequestPriority = ChangeRequestPriority.MEDIUM,
        baseline_id: Optional[uuid.UUID] = None,
        affected_components: Optional[List[str]] = None,
        risk_level: Optional[str] = None,
        impact_assessment: Optional[str] = None,
        scheduled_implementation_date: Optional[datetime] = None,
        requested_by_user_id: Optional[int] = None,
        requested_by_email: Optional[str] = None,
    ) -> ConfigurationChangeRequest:
        """
        Create a configuration change request (CM-3, CM-5).
        
        Enforces access restrictions per CM-5 requirements.
        
        Args:
            db: Database session
            org_id: Organization ID
            title: Change request title
            description: Detailed description
            configuration_changes: JSON describing what is changing
            change_reason: Reason for the change
            priority: Change priority
            baseline_id: Associated baseline (optional)
            affected_components: List of affected components
            risk_level: Risk level assessment
            impact_assessment: Impact analysis
            scheduled_implementation_date: When change is scheduled
            requested_by_user_id: User ID requesting change
            requested_by_email: User email (denormalized)
            
        Returns:
            Created ConfigurationChangeRequest
            
        Raises:
            PermissionError: If user does not have permission to create change requests
        """
        # Check access permissions (CM-5)
        if requested_by_user_id:
            has_permission, error_msg = ConfigurationManagementService.check_change_permission(
                db, requested_by_user_id, org_id, change_type=configuration_changes.get('type')
            )
            if not has_permission:
                raise PermissionError(error_msg)
        
        # Generate change number
        change_number = ConfigurationManagementService._generate_change_number(db, org_id)
        
        change_request = ConfigurationChangeRequest(
            org_id=org_id,
            change_number=change_number,
            title=title,
            description=description,
            configuration_changes=configuration_changes,
            change_reason=change_reason,
            priority=priority.value,
            baseline_id=baseline_id,
            affected_components=affected_components or [],
            risk_level=risk_level,
            impact_assessment=impact_assessment,
            status=ChangeRequestStatus.PENDING.value,
            requested_by_user_id=requested_by_user_id,
            requested_by_email=requested_by_email,
            scheduled_implementation_date=scheduled_implementation_date,
        )
        
        db.add(change_request)
        db.commit()
        db.refresh(change_request)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=org_id,
            user_id=requested_by_user_id,
            action="create_change_request",
            resource_type="configuration_change_request",
            resource_id=str(change_request.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "change_number": change_number,
                "title": title,
                "priority": priority.value,
            },
        )
        
        logger.info(
            "Created configuration change request %s for org %d",
            change_number,
            org_id,
        )
        
        return change_request
    
    @staticmethod
    def create_approval(
        db: Session,
        change_request_id: uuid.UUID,
        approval_level: int,
        approval_role_required: Optional[str] = None,
        approver_user_id: Optional[int] = None,
        approver_email: Optional[str] = None,
    ) -> ConfigurationChangeApproval:
        """
        Create an approval record for a change request (CM-3).
        
        Args:
            db: Database session
            change_request_id: Change request ID
            approval_level: Approval level (1, 2, 3, etc.)
            approval_role_required: Required role for approval
            approver_user_id: User ID of approver (if pre-assigned)
            approver_email: Approver email (denormalized)
            
        Returns:
            Created ConfigurationChangeApproval
        """
        approval = ConfigurationChangeApproval(
            change_request_id=change_request_id,
            approval_level=approval_level,
            approval_role_required=approval_role_required,
            approver_user_id=approver_user_id,
            approver_email=approver_email,
            approval_status="pending",
        )
        
        db.add(approval)
        db.commit()
        db.refresh(approval)
        
        return approval
    
    @staticmethod
    def approve_change_request(
        db: Session,
        approval_id: uuid.UUID,
        approver_user_id: int,
        approver_email: Optional[str] = None,
        approval_comment: Optional[str] = None,
    ) -> Tuple[ConfigurationChangeApproval, ConfigurationChangeRequest]:
        """
        Approve a change request (CM-3, CM-5).
        
        Enforces access restrictions per CM-5 requirements.
        
        Args:
            db: Database session
            approval_id: Approval ID
            approver_user_id: User ID approving
            approver_email: User email (denormalized)
            approval_comment: Optional comment
            
        Returns:
            Tuple of (ConfigurationChangeApproval, ConfigurationChangeRequest)
            
        Raises:
            ValueError: If approval not found or already processed
            PermissionError: If user does not have permission to approve changes
        """
        approval = db.query(ConfigurationChangeApproval).filter(
            ConfigurationChangeApproval.id == approval_id,
        ).first()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.approval_status != "pending":
            raise ValueError(f"Approval already processed: {approval.approval_status}")
        
        # Get change request for org_id
        change_request = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.id == approval.change_request_id,
        ).first()
        
        if not change_request:
            raise ValueError(f"Change request not found")
        
        # Check approval permissions (CM-5)
        has_permission, error_msg = ConfigurationManagementService.check_approval_permission(
            db, approver_user_id, change_request.org_id
        )
        if not has_permission:
            # Log unauthorized approval attempt
            ConfigurationManagementService._log_audit(
                db=db,
                org_id=change_request.org_id,
                user_id=approver_user_id,
                action="change_approval_denied",
                resource_type="configuration_change_approval",
                resource_id=str(approval_id),
                outcome=AuditOutcome.DENIED.value,
                metadata={
                    "reason": "insufficient_permissions",
                    "change_request_id": str(change_request.id),
                },
            )
            raise PermissionError(error_msg)
        
        # Update approval
        approval.approval_status = "approved"
        approval.approver_user_id = approver_user_id
        approval.approver_email = approver_email
        approval.approval_comment = approval_comment
        approval.responded_at = datetime.now(timezone.utc)
        
        # Check if all required approvals are complete
        all_approvals = db.query(ConfigurationChangeApproval).filter(
            ConfigurationChangeApproval.change_request_id == change_request.id,
        ).all()
        
        all_approved = all(
            a.approval_status == "approved"
            for a in all_approvals
            if a.approval_status != "pending"
        )
        
        # If all approvals complete, update change request status
        if all_approved and change_request.status == ChangeRequestStatus.UNDER_REVIEW.value:
            change_request.status = ChangeRequestStatus.APPROVED.value
        
        db.commit()
        db.refresh(approval)
        db.refresh(change_request)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=change_request.org_id,
            user_id=approver_user_id,
            action="approve_change_request",
            resource_type="configuration_change_request",
            resource_id=str(change_request.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "change_number": change_request.change_number,
                "approval_level": approval.approval_level,
                "approval_comment": approval_comment,
            },
        )
        
        logger.info(
            "Approved change request %s (approval level %d)",
            change_request.change_number,
            approval.approval_level,
        )
        
        return approval, change_request
    
    @staticmethod
    def reject_change_request(
        db: Session,
        approval_id: uuid.UUID,
        approver_user_id: int,
        approver_email: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> Tuple[ConfigurationChangeApproval, ConfigurationChangeRequest]:
        """
        Reject a change request (CM-3).
        
        Args:
            db: Database session
            approval_id: Approval ID
            approver_user_id: User ID rejecting
            approver_email: User email (denormalized)
            rejection_reason: Reason for rejection
            
        Returns:
            Tuple of (ConfigurationChangeApproval, ConfigurationChangeRequest)
        """
        approval = db.query(ConfigurationChangeApproval).filter(
            ConfigurationChangeApproval.id == approval_id,
        ).first()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        # Update approval
        approval.approval_status = "rejected"
        approval.approver_user_id = approver_user_id
        approval.approver_email = approver_email
        approval.approval_comment = rejection_reason
        approval.responded_at = datetime.now(timezone.utc)
        
        # Get change request
        change_request = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.id == approval.change_request_id,
        ).first()
        
        # Update change request status
        change_request.status = ChangeRequestStatus.REJECTED.value
        
        db.commit()
        db.refresh(approval)
        db.refresh(change_request)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=change_request.org_id,
            user_id=approver_user_id,
            action="reject_change_request",
            resource_type="configuration_change_request",
            resource_id=str(change_request.id),
            outcome=AuditOutcome.DENIED.value,
            metadata={
                "change_number": change_request.change_number,
                "approval_level": approval.approval_level,
                "rejection_reason": rejection_reason,
            },
        )
        
        logger.info(
            "Rejected change request %s (approval level %d)",
            change_request.change_number,
            approval.approval_level,
        )
        
        return approval, change_request
    
    @staticmethod
    def implement_change_request(
        db: Session,
        change_request_id: uuid.UUID,
        org_id: int,
        implemented_by_user_id: Optional[int] = None,
    ) -> ConfigurationChangeRequest:
        """
        Mark a change request as implemented (CM-3, CM-5).
        
        Enforces access restrictions per CM-5 requirements.
        
        Args:
            db: Database session
            change_request_id: Change request ID
            org_id: Organization ID
            implemented_by_user_id: User ID implementing the change
            
        Returns:
            Updated ConfigurationChangeRequest
            
        Raises:
            ValueError: If change request not found or not approved
            PermissionError: If user does not have permission to implement changes
        """
        change_request = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.id == change_request_id,
            ConfigurationChangeRequest.org_id == org_id,
        ).first()
        
        if not change_request:
            raise ValueError(f"Change request {change_request_id} not found")
        
        if change_request.status != ChangeRequestStatus.APPROVED.value:
            raise ValueError(f"Change request must be APPROVED to implement")
        
        # Check implementation permissions (CM-5)
        if implemented_by_user_id:
            has_permission, error_msg = ConfigurationManagementService.check_change_permission(
                db, implemented_by_user_id, org_id
            )
            if not has_permission:
                raise PermissionError(error_msg)
        
        change_request.status = ChangeRequestStatus.IMPLEMENTED.value
        change_request.actual_implementation_date = datetime.now(timezone.utc)
        change_request.implemented_by_user_id = implemented_by_user_id
        
        db.commit()
        db.refresh(change_request)
        
        # Log audit event
        ConfigurationManagementService._log_audit(
            db=db,
            org_id=org_id,
            user_id=implemented_by_user_id,
            action="implement_change_request",
            resource_type="configuration_change_request",
            resource_id=str(change_request_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "change_number": change_request.change_number,
                "configuration_changes": change_request.configuration_changes,
            },
        )
        
        logger.info(
            "Implemented change request %s for org %d",
            change_request.change_number,
            org_id,
        )
        
        return change_request
    
    @staticmethod
    def get_active_baseline(
        db: Session,
        org_id: int,
    ) -> Optional[ConfigurationBaseline]:
        """
        Get the active configuration baseline for an organization (CM-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            
        Returns:
            Active ConfigurationBaseline or None
        """
        return db.query(ConfigurationBaseline).filter(
            ConfigurationBaseline.org_id == org_id,
            ConfigurationBaseline.status == ConfigurationBaselineStatus.ACTIVE.value,
        ).first()
    
    @staticmethod
    def list_baselines(
        db: Session,
        org_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConfigurationBaseline]:
        """
        List configuration baselines for an organization.
        
        Args:
            db: Database session
            org_id: Organization ID
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of ConfigurationBaseline
        """
        query = db.query(ConfigurationBaseline).filter(
            ConfigurationBaseline.org_id == org_id,
        )
        
        if status:
            query = query.filter(ConfigurationBaseline.status == status)
        
        return query.order_by(desc(ConfigurationBaseline.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def list_change_requests(
        db: Session,
        org_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConfigurationChangeRequest]:
        """
        List configuration change requests for an organization.
        
        Args:
            db: Database session
            org_id: Organization ID
            status: Optional status filter
            priority: Optional priority filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of ConfigurationChangeRequest
        """
        query = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.org_id == org_id,
        )
        
        if status:
            query = query.filter(ConfigurationChangeRequest.status == status)
        
        if priority:
            query = query.filter(ConfigurationChangeRequest.priority == priority)
        
        return query.order_by(desc(ConfigurationChangeRequest.requested_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def _generate_change_number(db: Session, org_id: int) -> str:
        """
        Generate a unique change request number.
        
        Format: CHG-YYYY-NNNN
        """
        year = datetime.now(timezone.utc).year
        
        # Find the highest number for this year
        last_change = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.org_id == org_id,
            ConfigurationChangeRequest.change_number.like(f"CHG-{year}-%"),
        ).order_by(desc(ConfigurationChangeRequest.change_number)).first()
        
        if last_change:
            # Extract number from last change number
            try:
                last_num = int(last_change.change_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"CHG-{year}-{next_num:04d}"
    
    @staticmethod
    def _log_audit(
        db: Session,
        org_id: int,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        metadata: Optional[Dict] = None,
    ):
        """Log configuration management audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.CONFIGURATION_CHANGE.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                metadata=metadata,
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error("Failed to log audit event: %s", e)
            db.rollback()
