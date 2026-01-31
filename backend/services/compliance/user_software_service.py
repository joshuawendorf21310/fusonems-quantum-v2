"""
User-Installed Software Service for FedRAMP CM-11 Compliance

FedRAMP Requirement CM-11: User-Installed Software
- Installation tracking
- Approval workflow
- Unauthorized software detection
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import UserInstalledSoftware, ApprovalStatus


class UserSoftwareService:
    """
    Service for user-installed software management (CM-11).
    """
    
    # Software that requires approval
    APPROVAL_REQUIRED_SOFTWARE = [
        'development_tools',
        'system_utilities',
        'network_tools',
        'security_tools',
    ]
    
    @staticmethod
    def detect_installation(
        db: Session,
        org_id: int,
        user_id: int,
        software_name: str,
        software_version: Optional[str] = None,
        vendor: Optional[str] = None,
        installation_path: Optional[str] = None,
        installation_method: Optional[str] = None,
        installation_reason: Optional[str] = None,
        detection_method: str = "automated_scan",
    ) -> UserInstalledSoftware:
        """
        Detect and record user-installed software.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User who installed software
            software_name: Name of software
            software_version: Software version
            vendor: Vendor name
            installation_path: Installation path
            installation_method: How software was installed
            installation_reason: Reason for installation
            detection_method: How installation was detected
            
        Returns:
            Created UserInstalledSoftware record
        """
        # Check if already recorded
        existing = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.org_id == org_id,
            UserInstalledSoftware.user_id == user_id,
            UserInstalledSoftware.software_name == software_name,
            UserInstalledSoftware.software_version == software_version,
            UserInstalledSoftware.approval_status != "removed",
        ).first()
        
        if existing:
            return existing
        
        # Determine if approval is required
        approval_required = UserSoftwareService._requires_approval(software_name, installation_method)
        
        software = UserInstalledSoftware(
            org_id=org_id,
            user_id=user_id,
            software_name=software_name,
            software_version=software_version,
            vendor=vendor,
            installation_path=installation_path,
            installed_at=datetime.now(timezone.utc),
            installation_method=installation_method,
            installation_reason=installation_reason,
            approval_status=ApprovalStatus.PENDING.value if approval_required else ApprovalStatus.APPROVED.value,
            approval_required=approval_required,
            detected_at=datetime.now(timezone.utc),
            detection_method=detection_method,
        )
        
        db.add(software)
        db.commit()
        db.refresh(software)
        
        logger.info(
            f"User-installed software detected: {software_name} "
            f"(user_id={user_id}, approval_required={approval_required})"
        )
        
        return software
    
    @staticmethod
    def _requires_approval(software_name: str, installation_method: Optional[str]) -> bool:
        """Determine if software requires approval"""
        # Check if software type requires approval
        for required_type in UserSoftwareService.APPROVAL_REQUIRED_SOFTWARE:
            if required_type.lower() in software_name.lower():
                return True
        
        # Check installation method
        if installation_method in ['manual', 'package_manager']:
            return True
        
        return False
    
    @staticmethod
    def approve_installation(
        db: Session,
        software_id: str,
        org_id: int,
        approved_by_user_id: int,
        approval_notes: Optional[str] = None,
    ) -> UserInstalledSoftware:
        """Approve user-installed software"""
        software = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.id == software_id,
            UserInstalledSoftware.org_id == org_id,
        ).first()
        
        if not software:
            raise ValueError(f"Software installation {software_id} not found")
        
        if software.approval_status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Software installation already {software.approval_status}")
        
        software.approval_status = ApprovalStatus.APPROVED.value
        software.approved_by_user_id = approved_by_user_id
        software.approved_at = datetime.now(timezone.utc)
        software.approval_notes = approval_notes
        
        db.commit()
        db.refresh(software)
        
        logger.info(f"Software installation approved: {software.software_name}")
        
        return software
    
    @staticmethod
    def reject_installation(
        db: Session,
        software_id: str,
        org_id: int,
        rejected_by_user_id: int,
        rejection_reason: str,
    ) -> UserInstalledSoftware:
        """Reject user-installed software"""
        software = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.id == software_id,
            UserInstalledSoftware.org_id == org_id,
        ).first()
        
        if not software:
            raise ValueError(f"Software installation {software_id} not found")
        
        software.approval_status = ApprovalStatus.REJECTED.value
        software.rejected_by_user_id = rejected_by_user_id
        software.rejected_at = datetime.now(timezone.utc)
        software.rejection_reason = rejection_reason
        
        db.commit()
        db.refresh(software)
        
        logger.warning(f"Software installation rejected: {software.software_name} (reason: {rejection_reason})")
        
        return software
    
    @staticmethod
    def record_removal(
        db: Session,
        software_id: str,
        org_id: int,
        removed_by_user_id: int,
        removal_reason: Optional[str] = None,
    ) -> UserInstalledSoftware:
        """Record software removal"""
        software = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.id == software_id,
            UserInstalledSoftware.org_id == org_id,
        ).first()
        
        if not software:
            raise ValueError(f"Software installation {software_id} not found")
        
        software.removed_at = datetime.now(timezone.utc)
        software.removed_by_user_id = removed_by_user_id
        software.removal_reason = removal_reason
        
        db.commit()
        db.refresh(software)
        
        logger.info(f"Software removal recorded: {software.software_name}")
        
        return software
    
    @staticmethod
    def get_pending_approvals(
        db: Session,
        org_id: int,
        limit: int = 100,
    ) -> List[UserInstalledSoftware]:
        """Get pending software installation approvals"""
        return db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.org_id == org_id,
            UserInstalledSoftware.approval_status == ApprovalStatus.PENDING.value,
        ).order_by(desc(UserInstalledSoftware.installed_at)).limit(limit).all()
    
    @staticmethod
    def get_user_software(
        db: Session,
        user_id: int,
        org_id: int,
        active_only: bool = True,
    ) -> List[UserInstalledSoftware]:
        """Get software installed by a user"""
        query = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.user_id == user_id,
            UserInstalledSoftware.org_id == org_id,
        )
        
        if active_only:
            query = query.filter(UserInstalledSoftware.removed_at.is_(None))
        
        return query.order_by(desc(UserInstalledSoftware.installed_at)).all()
    
    @staticmethod
    def detect_unauthorized_software(
        db: Session,
        org_id: int,
        allowed_software_list: List[str],
    ) -> List[UserInstalledSoftware]:
        """Detect unauthorized software installations"""
        all_software = db.query(UserInstalledSoftware).filter(
            UserInstalledSoftware.org_id == org_id,
            UserInstalledSoftware.removed_at.is_(None),
        ).all()
        
        unauthorized = []
        allowed_lower = [s.lower() for s in allowed_software_list]
        
        for software in all_software:
            if software.software_name.lower() not in allowed_lower:
                unauthorized.append(software)
        
        if unauthorized:
            logger.warning(f"Detected {len(unauthorized)} unauthorized software installations")
        
        return unauthorized
