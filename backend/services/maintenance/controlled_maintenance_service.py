"""
Controlled Maintenance Service for FedRAMP MA-2 Compliance

FedRAMP MA-2: Controlled Maintenance
- Schedule maintenance
- Approval workflow
- Maintenance logging
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.maintenance import (
    ControlledMaintenance,
    MaintenanceStatus,
    MaintenanceType,
    MaintenancePriority,
    ApprovalStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class ControlledMaintenanceService:
    """
    Service for managing controlled maintenance (MA-2).
    
    Implements FedRAMP MA-2 control requirements.
    """
    
    @staticmethod
    def _generate_maintenance_number(db: Session, org_id: int) -> str:
        """Generate unique maintenance number."""
        year = datetime.now(timezone.utc).year
        last_maint = db.query(ControlledMaintenance).filter(
            ControlledMaintenance.org_id == org_id,
            ControlledMaintenance.maintenance_number.like(f"MAINT-{year}-%"),
        ).order_by(desc(ControlledMaintenance.maintenance_number)).first()
        
        if last_maint:
            try:
                last_num = int(last_maint.maintenance_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"MAINT-{year}-{next_num:04d}"
    
    @staticmethod
    def create_maintenance(
        db: Session,
        org_id: int,
        title: str,
        description: str,
        maintenance_type: str,
        system_name: str,
        scheduled_start_date: datetime,
        scheduled_end_date: datetime,
        requested_by_user_id: int,
        requested_by_email: Optional[str] = None,
        priority: str = MaintenancePriority.MEDIUM.value,
        component_name: Optional[str] = None,
        component_type: Optional[str] = None,
        impact_assessment: Optional[str] = None,
        downtime_expected: bool = False,
        downtime_duration_minutes: Optional[int] = None,
        approval_required: bool = True,
    ) -> ControlledMaintenance:
        """
        Create a maintenance record (MA-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            title: Maintenance title
            description: Maintenance description
            maintenance_type: Type of maintenance
            system_name: System being maintained
            scheduled_start_date: Scheduled start date
            scheduled_end_date: Scheduled end date
            requested_by_user_id: User ID requesting
            requested_by_email: User email (denormalized)
            priority: Maintenance priority
            component_name: Component name
            component_type: Component type
            impact_assessment: Impact assessment
            downtime_expected: Whether downtime is expected
            downtime_duration_minutes: Expected downtime duration
            approval_required: Whether approval is required
            
        Returns:
            Created ControlledMaintenance record
        """
        maintenance_number = ControlledMaintenanceService._generate_maintenance_number(db, org_id)
        
        maintenance = ControlledMaintenance(
            org_id=org_id,
            maintenance_number=maintenance_number,
            title=title,
            description=description,
            maintenance_type=maintenance_type,
            priority=priority,
            system_name=system_name,
            component_name=component_name,
            component_type=component_type,
            scheduled_start_date=scheduled_start_date,
            scheduled_end_date=scheduled_end_date,
            maintenance_status=MaintenanceStatus.SCHEDULED.value,
            approval_required=approval_required,
            approval_status=ApprovalStatus.PENDING.value if approval_required else None,
            requested_by_user_id=requested_by_user_id,
            requested_by_email=requested_by_email,
            requested_at=datetime.now(timezone.utc),
            impact_assessment=impact_assessment,
            downtime_expected=downtime_expected,
            downtime_duration_minutes=downtime_duration_minutes,
            maintenance_log=[],
        )
        
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        
        # Log audit event
        ControlledMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=requested_by_user_id,
            action="create_maintenance",
            resource_type="controlled_maintenance",
            resource_id=str(maintenance.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "maintenance_number": maintenance_number,
                "system_name": system_name,
                "maintenance_type": maintenance_type,
            },
        )
        
        logger.info(
            "Created maintenance: maintenance_number=%s, system=%s",
            maintenance_number,
            system_name,
        )
        
        return maintenance
    
    @staticmethod
    def approve_maintenance(
        db: Session,
        maintenance_id: UUID,
        org_id: int,
        approved_by_user_id: int,
        approval_comment: Optional[str] = None,
    ) -> ControlledMaintenance:
        """
        Approve maintenance (MA-2).
        
        Args:
            db: Database session
            maintenance_id: Maintenance ID
            org_id: Organization ID
            approved_by_user_id: User ID approving
            approval_comment: Approval comment
            
        Returns:
            Updated ControlledMaintenance record
        """
        maintenance = db.query(ControlledMaintenance).filter(
            ControlledMaintenance.id == maintenance_id,
            ControlledMaintenance.org_id == org_id,
        ).first()
        
        if not maintenance:
            raise ValueError(f"Maintenance {maintenance_id} not found")
        
        if maintenance.approval_status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Maintenance approval status is {maintenance.approval_status}, not pending")
        
        maintenance.approval_status = ApprovalStatus.APPROVED.value
        maintenance.approved_by_user_id = approved_by_user_id
        maintenance.approved_at = datetime.now(timezone.utc)
        maintenance.approval_comment = approval_comment
        
        db.commit()
        db.refresh(maintenance)
        
        # Log audit event
        ControlledMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=approved_by_user_id,
            action="approve_maintenance",
            resource_type="controlled_maintenance",
            resource_id=str(maintenance_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "maintenance_number": maintenance.maintenance_number,
                "approval_comment": approval_comment,
            },
        )
        
        logger.info("Approved maintenance: maintenance_id=%s", maintenance_id)
        
        return maintenance
    
    @staticmethod
    def start_maintenance(
        db: Session,
        maintenance_id: UUID,
        org_id: int,
        started_by_user_id: Optional[int] = None,
    ) -> ControlledMaintenance:
        """
        Start maintenance (MA-2).
        
        Args:
            db: Database session
            maintenance_id: Maintenance ID
            org_id: Organization ID
            started_by_user_id: User ID starting maintenance
            
        Returns:
            Updated ControlledMaintenance record
        """
        maintenance = db.query(ControlledMaintenance).filter(
            ControlledMaintenance.id == maintenance_id,
            ControlledMaintenance.org_id == org_id,
        ).first()
        
        if not maintenance:
            raise ValueError(f"Maintenance {maintenance_id} not found")
        
        if maintenance.maintenance_status != MaintenanceStatus.SCHEDULED.value:
            raise ValueError(f"Maintenance status is {maintenance.maintenance_status}, not scheduled")
        
        if maintenance.approval_required and maintenance.approval_status != ApprovalStatus.APPROVED.value:
            raise ValueError("Maintenance must be approved before starting")
        
        maintenance.maintenance_status = MaintenanceStatus.IN_PROGRESS.value
        maintenance.actual_start_date = datetime.now(timezone.utc)
        
        # Add log entry
        if not maintenance.maintenance_log:
            maintenance.maintenance_log = []
        maintenance.maintenance_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "started",
            "user_id": started_by_user_id,
        })
        
        db.commit()
        db.refresh(maintenance)
        
        # Log audit event
        ControlledMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=started_by_user_id,
            action="start_maintenance",
            resource_type="controlled_maintenance",
            resource_id=str(maintenance_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "maintenance_number": maintenance.maintenance_number,
            },
        )
        
        logger.info("Started maintenance: maintenance_id=%s", maintenance_id)
        
        return maintenance
    
    @staticmethod
    def complete_maintenance(
        db: Session,
        maintenance_id: UUID,
        org_id: int,
        completion_notes: Optional[str] = None,
        completed_by_user_id: Optional[int] = None,
    ) -> ControlledMaintenance:
        """
        Complete maintenance (MA-2).
        
        Args:
            db: Database session
            maintenance_id: Maintenance ID
            org_id: Organization ID
            completion_notes: Completion notes
            completed_by_user_id: User ID completing
            
        Returns:
            Updated ControlledMaintenance record
        """
        maintenance = db.query(ControlledMaintenance).filter(
            ControlledMaintenance.id == maintenance_id,
            ControlledMaintenance.org_id == org_id,
        ).first()
        
        if not maintenance:
            raise ValueError(f"Maintenance {maintenance_id} not found")
        
        if maintenance.maintenance_status != MaintenanceStatus.IN_PROGRESS.value:
            raise ValueError(f"Maintenance status is {maintenance.maintenance_status}, not in_progress")
        
        maintenance.maintenance_status = MaintenanceStatus.COMPLETED.value
        maintenance.actual_end_date = datetime.now(timezone.utc)
        maintenance.completion_notes = completion_notes
        maintenance.completed_by_user_id = completed_by_user_id
        
        # Add log entry
        if not maintenance.maintenance_log:
            maintenance.maintenance_log = []
        maintenance.maintenance_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "completed",
            "user_id": completed_by_user_id,
            "notes": completion_notes,
        })
        
        db.commit()
        db.refresh(maintenance)
        
        # Log audit event
        ControlledMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=completed_by_user_id,
            action="complete_maintenance",
            resource_type="controlled_maintenance",
            resource_id=str(maintenance_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "maintenance_number": maintenance.maintenance_number,
            },
        )
        
        logger.info("Completed maintenance: maintenance_id=%s", maintenance_id)
        
        return maintenance
    
    @staticmethod
    def list_maintenance(
        db: Session,
        org_id: int,
        maintenance_status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        system_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ControlledMaintenance]:
        """
        List maintenance records (MA-2).
        
        Args:
            db: Database session
            org_id: Organization ID
            maintenance_status: Optional status filter
            maintenance_type: Optional type filter
            system_name: Optional system name filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of ControlledMaintenance records
        """
        query = db.query(ControlledMaintenance).filter(
            ControlledMaintenance.org_id == org_id,
        )
        
        if maintenance_status:
            query = query.filter(ControlledMaintenance.maintenance_status == maintenance_status)
        
        if maintenance_type:
            query = query.filter(ControlledMaintenance.maintenance_type == maintenance_type)
        
        if system_name:
            query = query.filter(ControlledMaintenance.system_name.ilike(f"%{system_name}%"))
        
        return query.order_by(desc(ControlledMaintenance.scheduled_start_date)).limit(limit).offset(offset).all()
    
    @staticmethod
    def _log_audit(
        db: Session,
        org_id: int,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        metadata: Optional[dict] = None,
    ):
        """Log maintenance audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.SYSTEM_EVENT.value,
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
