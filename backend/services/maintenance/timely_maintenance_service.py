"""
Timely Maintenance Service for FedRAMP MA-6 Compliance

FedRAMP MA-6: Timely Maintenance
- Maintenance SLAs
- Preventive maintenance scheduling
- Compliance tracking
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.maintenance import (
    TimelyMaintenance,
    MaintenanceType,
    SLAStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class TimelyMaintenanceService:
    """
    Service for managing timely maintenance (MA-6).
    
    Implements FedRAMP MA-6 control requirements.
    """
    
    @staticmethod
    def create_sla(
        db: Session,
        org_id: int,
        system_name: str,
        maintenance_type: str,
        sla_hours: int,
        maintenance_due_date: datetime,
        component_name: Optional[str] = None,
        component_type: Optional[str] = None,
        preventive_schedule_days: Optional[int] = None,
    ) -> TimelyMaintenance:
        """
        Create a maintenance SLA record (MA-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            system_name: System name
            maintenance_type: Type of maintenance
            sla_hours: Hours within which maintenance must be completed
            maintenance_due_date: When maintenance is due
            component_name: Component name
            component_type: Component type
            preventive_schedule_days: Days between preventive maintenance
            
        Returns:
            Created TimelyMaintenance record
        """
        # Calculate next preventive maintenance date
        next_preventive_date = None
        if preventive_schedule_days:
            next_preventive_date = datetime.now(timezone.utc) + timedelta(days=preventive_schedule_days)
        
        timely_maint = TimelyMaintenance(
            org_id=org_id,
            system_name=system_name,
            component_name=component_name,
            component_type=component_type,
            maintenance_type=maintenance_type,
            sla_hours=sla_hours,
            maintenance_due_date=maintenance_due_date,
            preventive_schedule_days=preventive_schedule_days,
            next_preventive_maintenance_date=next_preventive_date,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(timely_maint)
        db.commit()
        db.refresh(timely_maint)
        
        # Log audit event
        TimelyMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=None,
            action="create_maintenance_sla",
            resource_type="timely_maintenance",
            resource_id=str(timely_maint.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "system_name": system_name,
                "maintenance_type": maintenance_type,
                "sla_hours": sla_hours,
            },
        )
        
        logger.info(
            "Created maintenance SLA: system=%s, sla_hours=%d",
            system_name,
            sla_hours,
        )
        
        return timely_maint
    
    @staticmethod
    def update_completion(
        db: Session,
        timely_maint_id: UUID,
        org_id: int,
        maintenance_id: UUID,
        maintenance_completed_date: datetime,
    ) -> TimelyMaintenance:
        """
        Update maintenance completion (MA-6).
        
        Args:
            db: Database session
            timely_maint_id: Timely maintenance ID
            org_id: Organization ID
            maintenance_id: Maintenance ID
            maintenance_completed_date: Completion date
            
        Returns:
            Updated TimelyMaintenance record
        """
        timely_maint = db.query(TimelyMaintenance).filter(
            TimelyMaintenance.id == timely_maint_id,
            TimelyMaintenance.org_id == org_id,
        ).first()
        
        if not timely_maint:
            raise ValueError(f"Timely maintenance {timely_maint_id} not found")
        
        timely_maint.maintenance_id = maintenance_id
        timely_maint.maintenance_completed_date = maintenance_completed_date
        
        # Calculate SLA compliance
        if maintenance_completed_date <= timely_maint.maintenance_due_date:
            timely_maint.sla_status = SLAStatus.ON_TIME.value
            timely_maint.sla_met = True
            variance = (timely_maint.maintenance_due_date - maintenance_completed_date).total_seconds() / 3600
            timely_maint.sla_variance_hours = int(variance)
        else:
            timely_maint.sla_status = SLAStatus.OVERDUE.value
            timely_maint.sla_met = False
            variance = (maintenance_completed_date - timely_maint.maintenance_due_date).total_seconds() / 3600
            timely_maint.sla_variance_hours = int(variance)
        
        # Update preventive maintenance schedule
        if timely_maint.preventive_schedule_days:
            timely_maint.last_preventive_maintenance_date = maintenance_completed_date
            timely_maint.next_preventive_maintenance_date = maintenance_completed_date + timedelta(
                days=timely_maint.preventive_schedule_days
            )
        
        db.commit()
        db.refresh(timely_maint)
        
        # Log audit event
        TimelyMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=None,
            action="update_maintenance_completion",
            resource_type="timely_maintenance",
            resource_id=str(timely_maint_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "system_name": timely_maint.system_name,
                "sla_met": timely_maint.sla_met,
                "sla_variance_hours": timely_maint.sla_variance_hours,
            },
        )
        
        logger.info(
            "Updated maintenance completion: timely_maint_id=%s, sla_met=%s",
            timely_maint_id,
            timely_maint.sla_met,
        )
        
        return timely_maint
    
    @staticmethod
    def check_sla_compliance(
        db: Session,
        org_id: int,
    ) -> dict:
        """
        Check SLA compliance for all systems (MA-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            
        Returns:
            Compliance summary
        """
        now = datetime.now(timezone.utc)
        
        # Find overdue maintenance
        overdue = db.query(TimelyMaintenance).filter(
            TimelyMaintenance.org_id == org_id,
            TimelyMaintenance.maintenance_completed_date.is_(None),
            TimelyMaintenance.maintenance_due_date < now,
        ).all()
        
        # Find at-risk maintenance (due within 24 hours)
        at_risk = db.query(TimelyMaintenance).filter(
            TimelyMaintenance.org_id == org_id,
            TimelyMaintenance.maintenance_completed_date.is_(None),
            TimelyMaintenance.maintenance_due_date >= now,
            TimelyMaintenance.maintenance_due_date <= now + timedelta(hours=24),
        ).all()
        
        # Update SLA status for overdue
        for item in overdue:
            item.sla_status = SLAStatus.OVERDUE.value
        
        # Update SLA status for at-risk
        for item in at_risk:
            item.sla_status = SLAStatus.AT_RISK.value
        
        db.commit()
        
        return {
            "overdue_count": len(overdue),
            "at_risk_count": len(at_risk),
            "overdue": [{"id": str(item.id), "system_name": item.system_name} for item in overdue],
            "at_risk": [{"id": str(item.id), "system_name": item.system_name} for item in at_risk],
        }
    
    @staticmethod
    def list_slas(
        db: Session,
        org_id: int,
        system_name: Optional[str] = None,
        sla_status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TimelyMaintenance]:
        """
        List maintenance SLAs (MA-6).
        
        Args:
            db: Database session
            org_id: Organization ID
            system_name: Optional system name filter
            sla_status: Optional SLA status filter
            maintenance_type: Optional maintenance type filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of TimelyMaintenance records
        """
        query = db.query(TimelyMaintenance).filter(
            TimelyMaintenance.org_id == org_id,
        )
        
        if system_name:
            query = query.filter(TimelyMaintenance.system_name.ilike(f"%{system_name}%"))
        
        if sla_status:
            query = query.filter(TimelyMaintenance.sla_status == sla_status)
        
        if maintenance_type:
            query = query.filter(TimelyMaintenance.maintenance_type == maintenance_type)
        
        return query.order_by(desc(TimelyMaintenance.maintenance_due_date)).limit(limit).offset(offset).all()
    
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
        """Log timely maintenance audit event."""
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
