"""
Flaw Remediation Service for FedRAMP SI-2 Compliance

This service provides:
- Patch management automation
- CVE tracking integration (enhances vulnerability scanner)
- Remediation timeline enforcement
- Emergency patching workflow

FedRAMP SI-2: Flaw Remediation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.system_integrity import (
    PatchRecord,
    PatchStatus,
    PatchPriority,
)
from models.vulnerability import (
    Vulnerability,
    VulnerabilitySeverity,
    RemediationStatus,
)
from utils.logger import logger


class FlawRemediationService:
    """
    Service for managing flaw remediation and patch management.
    
    FedRAMP SI-2: Flaw Remediation
    """
    
    # SLA timelines (in days)
    SLA_CRITICAL = 7  # Critical vulnerabilities must be patched within 7 days
    SLA_HIGH = 30  # High severity within 30 days
    SLA_MEDIUM = 90  # Medium severity within 90 days
    SLA_LOW = 180  # Low severity within 180 days
    
    def __init__(self, db: Session):
        """
        Initialize flaw remediation service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_patch_record(
        self,
        patch_id: str,
        component_type: str,
        component_name: str,
        target_version: str,
        cve_id: Optional[str] = None,
        vulnerability_id: Optional[int] = None,
        priority: PatchPriority = PatchPriority.MEDIUM,
        is_emergency: bool = False,
        patch_description: Optional[str] = None,
        patch_url: Optional[str] = None,
    ) -> PatchRecord:
        """
        Create a new patch record.
        
        Args:
            patch_id: Unique patch identifier
            component_type: Type of component (e.g., "python_package")
            component_name: Name of component
            target_version: Version to patch to
            cve_id: Related CVE ID
            vulnerability_id: Related vulnerability record ID
            priority: Patch priority
            is_emergency: Whether this is an emergency patch
            patch_description: Description of the patch
            patch_url: URL to patch/download
            
        Returns:
            Created PatchRecord
        """
        # Calculate SLA due date based on priority
        sla_due_date = self._calculate_sla_due_date(priority, is_emergency)
        
        patch = PatchRecord(
            patch_id=patch_id,
            cve_id=cve_id,
            vulnerability_id=vulnerability_id,
            component_type=component_type,
            component_name=component_name,
            target_version=target_version,
            priority=priority.value,
            is_emergency=is_emergency,
            patch_description=patch_description,
            patch_url=patch_url,
            status=PatchStatus.PENDING.value,
            sla_due_date=sla_due_date,
        )
        
        self.db.add(patch)
        self.db.commit()
        self.db.refresh(patch)
        
        logger.info(
            f"Created patch record: {patch_id}",
            extra={
                "patch_id": patch_id,
                "component_name": component_name,
                "priority": priority.value,
                "is_emergency": is_emergency,
                "event_type": "patch.created",
            }
        )
        
        return patch
    
    def approve_patch(self, patch_id: str, approver: str) -> PatchRecord:
        """
        Approve a patch for deployment.
        
        Args:
            patch_id: Patch identifier
            approver: User who approved the patch
            
        Returns:
            Updated PatchRecord
        """
        patch = self.db.query(PatchRecord).filter(
            PatchRecord.patch_id == patch_id
        ).first()
        
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        patch.status = PatchStatus.APPROVED.value
        patch.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(patch)
        
        logger.info(
            f"Patch approved: {patch_id}",
            extra={
                "patch_id": patch_id,
                "approver": approver,
                "event_type": "patch.approved",
            }
        )
        
        return patch
    
    def schedule_patch_deployment(
        self,
        patch_id: str,
        scheduled_at: datetime,
        deployed_by: str,
    ) -> PatchRecord:
        """
        Schedule a patch for deployment.
        
        Args:
            patch_id: Patch identifier
            scheduled_at: When to deploy the patch
            deployed_by: User who will deploy
            
        Returns:
            Updated PatchRecord
        """
        patch = self.db.query(PatchRecord).filter(
            PatchRecord.patch_id == patch_id
        ).first()
        
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        patch.status = PatchStatus.SCHEDULED.value
        patch.scheduled_deployment_at = scheduled_at
        
        self.db.commit()
        self.db.refresh(patch)
        
        logger.info(
            f"Patch scheduled: {patch_id}",
            extra={
                "patch_id": patch_id,
                "scheduled_at": scheduled_at.isoformat(),
                "deployed_by": deployed_by,
                "event_type": "patch.scheduled",
            }
        )
        
        return patch
    
    def record_patch_deployment(
        self,
        patch_id: str,
        deployed_by: str,
        deployment_method: str,
        deployment_log: Optional[str] = None,
    ) -> PatchRecord:
        """
        Record that a patch has been deployed.
        
        Args:
            patch_id: Patch identifier
            deployed_by: User who deployed
            deployment_method: Method used for deployment
            deployment_log: Deployment log output
            
        Returns:
            Updated PatchRecord
        """
        patch = self.db.query(PatchRecord).filter(
            PatchRecord.patch_id == patch_id
        ).first()
        
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        patch.status = PatchStatus.DEPLOYED.value
        patch.deployed_at = datetime.utcnow()
        patch.deployed_by = deployed_by
        patch.deployment_method = deployment_method
        patch.deployment_log = deployment_log
        
        self.db.commit()
        self.db.refresh(patch)
        
        logger.info(
            f"Patch deployed: {patch_id}",
            extra={
                "patch_id": patch_id,
                "deployed_by": deployed_by,
                "event_type": "patch.deployed",
            }
        )
        
        return patch
    
    def verify_patch(
        self,
        patch_id: str,
        verified_by: str,
        verification_method: str,
        verification_result: str,
    ) -> PatchRecord:
        """
        Verify that a patch was successfully applied.
        
        Args:
            patch_id: Patch identifier
            verified_by: User who verified
            verification_method: Method used for verification
            verification_result: Result of verification
            
        Returns:
            Updated PatchRecord
        """
        patch = self.db.query(PatchRecord).filter(
            PatchRecord.patch_id == patch_id
        ).first()
        
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        patch.status = PatchStatus.VERIFIED.value
        patch.verified_at = datetime.utcnow()
        patch.verified_by = verified_by
        patch.verification_method = verification_method
        patch.verification_result = verification_result
        
        # Update related vulnerability if exists
        if patch.vulnerability_id:
            vulnerability = self.db.query(Vulnerability).filter(
                Vulnerability.id == patch.vulnerability_id
            ).first()
            if vulnerability:
                vulnerability.remediation_status = RemediationStatus.PATCHED.value
                vulnerability.remediation_date = datetime.utcnow()
                vulnerability.remediation_version = patch.target_version
        
        self.db.commit()
        self.db.refresh(patch)
        
        logger.info(
            f"Patch verified: {patch_id}",
            extra={
                "patch_id": patch_id,
                "verified_by": verified_by,
                "event_type": "patch.verified",
            }
        )
        
        return patch
    
    def create_emergency_patch(
        self,
        patch_id: str,
        component_type: str,
        component_name: str,
        target_version: str,
        emergency_justification: str,
        emergency_approver: str,
        cve_id: Optional[str] = None,
        vulnerability_id: Optional[int] = None,
    ) -> PatchRecord:
        """
        Create an emergency patch record.
        
        Args:
            patch_id: Unique patch identifier
            component_type: Type of component
            component_name: Name of component
            target_version: Version to patch to
            emergency_justification: Justification for emergency patch
            emergency_approver: User who approved emergency patch
            cve_id: Related CVE ID
            vulnerability_id: Related vulnerability record ID
            
        Returns:
            Created PatchRecord
        """
        patch = self.create_patch_record(
            patch_id=patch_id,
            component_type=component_type,
            component_name=component_name,
            target_version=target_version,
            cve_id=cve_id,
            vulnerability_id=vulnerability_id,
            priority=PatchPriority.CRITICAL,
            is_emergency=True,
        )
        
        patch.emergency_justification = emergency_justification
        patch.emergency_approver = emergency_approver
        patch.status = PatchStatus.APPROVED.value  # Auto-approve emergency patches
        patch.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(patch)
        
        logger.warning(
            f"Emergency patch created: {patch_id}",
            extra={
                "patch_id": patch_id,
                "component_name": component_name,
                "emergency_approver": emergency_approver,
                "event_type": "patch.emergency.created",
            }
        )
        
        return patch
    
    def check_sla_compliance(self) -> Dict:
        """
        Check SLA compliance for all pending/approved patches.
        
        Returns:
            Dictionary with compliance statistics
        """
        now = datetime.utcnow()
        
        # Find patches that are past due
        overdue_patches = self.db.query(PatchRecord).filter(
            and_(
                PatchRecord.status.in_([
                    PatchStatus.PENDING.value,
                    PatchStatus.APPROVED.value,
                    PatchStatus.SCHEDULED.value,
                ]),
                PatchRecord.sla_due_date < now,
                PatchRecord.sla_breached == False,
            )
        ).all()
        
        # Mark as breached
        for patch in overdue_patches:
            patch.sla_breached = True
            logger.warning(
                f"Patch SLA breached: {patch.patch_id}",
                extra={
                    "patch_id": patch.patch_id,
                    "sla_due_date": patch.sla_due_date.isoformat() if patch.sla_due_date else None,
                    "event_type": "patch.sla.breached",
                }
            )
        
        self.db.commit()
        
        # Get statistics
        total_patches = self.db.query(PatchRecord).count()
        pending_patches = self.db.query(PatchRecord).filter(
            PatchRecord.status == PatchStatus.PENDING.value
        ).count()
        overdue_count = len(overdue_patches)
        emergency_patches = self.db.query(PatchRecord).filter(
            PatchRecord.is_emergency == True,
            PatchRecord.status != PatchStatus.VERIFIED.value,
        ).count()
        
        return {
            "total_patches": total_patches,
            "pending_patches": pending_patches,
            "overdue_patches": overdue_count,
            "emergency_patches": emergency_patches,
            "sla_compliance_rate": (
                (total_patches - overdue_count) / total_patches * 100
                if total_patches > 0 else 100.0
            ),
        }
    
    def get_patches_by_status(
        self,
        status: Optional[PatchStatus] = None,
        priority: Optional[PatchPriority] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[PatchRecord], int]:
        """
        Get patches filtered by status and priority.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (patches list, total count)
        """
        query = self.db.query(PatchRecord)
        
        if status:
            query = query.filter(PatchRecord.status == status.value)
        
        if priority:
            query = query.filter(PatchRecord.priority == priority.value)
        
        total = query.count()
        patches = query.order_by(
            PatchRecord.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return patches, total
    
    def _calculate_sla_due_date(
        self,
        priority: PatchPriority,
        is_emergency: bool,
    ) -> datetime:
        """
        Calculate SLA due date based on priority.
        
        Args:
            priority: Patch priority
            is_emergency: Whether this is an emergency patch
            
        Returns:
            SLA due date
        """
        if is_emergency:
            days = 1  # Emergency patches must be deployed within 1 day
        elif priority == PatchPriority.CRITICAL:
            days = self.SLA_CRITICAL
        elif priority == PatchPriority.HIGH:
            days = self.SLA_HIGH
        elif priority == PatchPriority.MEDIUM:
            days = self.SLA_MEDIUM
        else:
            days = self.SLA_LOW
        
        return datetime.utcnow() + timedelta(days=days)
    
    def generate_remediation_timeline_report(self) -> Dict:
        """
        Generate remediation timeline report.
        
        Returns:
            Dictionary with timeline statistics
        """
        patches = self.db.query(PatchRecord).all()
        
        timeline_stats = {
            "total_patches": len(patches),
            "by_status": {},
            "by_priority": {},
            "average_time_to_deploy": None,
            "average_time_to_verify": None,
            "sla_compliance": {},
        }
        
        # Calculate averages
        deployed_patches = [
            p for p in patches
            if p.deployed_at and p.discovered_at
        ]
        verified_patches = [
            p for p in patches
            if p.verified_at and p.deployed_at
        ]
        
        if deployed_patches:
            avg_deploy_time = sum(
                (p.deployed_at - p.discovered_at).total_seconds()
                for p in deployed_patches
            ) / len(deployed_patches)
            timeline_stats["average_time_to_deploy"] = avg_deploy_time / 86400  # Convert to days
        
        if verified_patches:
            avg_verify_time = sum(
                (p.verified_at - p.deployed_at).total_seconds()
                for p in verified_patches
            ) / len(verified_patches)
            timeline_stats["average_time_to_verify"] = avg_verify_time / 3600  # Convert to hours
        
        # Count by status
        for status in PatchStatus:
            count = len([p for p in patches if p.status == status.value])
            timeline_stats["by_status"][status.value] = count
        
        # Count by priority
        for priority in PatchPriority:
            count = len([p for p in patches if p.priority == priority.value])
            timeline_stats["by_priority"][priority.value] = count
        
        # SLA compliance
        compliance = self.check_sla_compliance()
        timeline_stats["sla_compliance"] = compliance
        
        return timeline_stats
