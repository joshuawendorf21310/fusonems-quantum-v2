"""
Nonlocal Maintenance Service for FedRAMP MA-4 Compliance

FedRAMP MA-4: Nonlocal Maintenance
- Remote maintenance authorization
- Session monitoring
- Access controls
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.maintenance import (
    NonlocalMaintenance,
    RemoteMaintenanceStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class NonlocalMaintenanceService:
    """
    Service for managing nonlocal (remote) maintenance (MA-4).
    
    Implements FedRAMP MA-4 control requirements.
    """
    
    @staticmethod
    def _generate_session_number(db: Session, org_id: int) -> str:
        """Generate unique session number."""
        year = datetime.now(timezone.utc).year
        last_session = db.query(NonlocalMaintenance).filter(
            NonlocalMaintenance.org_id == org_id,
            NonlocalMaintenance.session_number.like(f"REMOTE-{year}-%"),
        ).order_by(desc(NonlocalMaintenance.session_number)).first()
        
        if last_session:
            try:
                last_num = int(last_session.session_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"REMOTE-{year}-{next_num:04d}"
    
    @staticmethod
    def create_session(
        db: Session,
        org_id: int,
        session_purpose: str,
        system_name: str,
        personnel_id: UUID,
        authorized_by_user_id: int,
        access_method: str,
        system_ip_address: Optional[str] = None,
        system_hostname: Optional[str] = None,
        maintenance_id: Optional[UUID] = None,
        access_protocol: Optional[str] = None,
        encryption_required: bool = True,
        encryption_method: Optional[str] = None,
        authorization_expires_at: Optional[datetime] = None,
        session_monitored: bool = True,
        allowed_commands: Optional[List[str]] = None,
        restricted_commands: Optional[List[str]] = None,
        allowed_files: Optional[List[str]] = None,
        restricted_files: Optional[List[str]] = None,
    ) -> NonlocalMaintenance:
        """
        Create a remote maintenance session (MA-4).
        
        Args:
            db: Database session
            org_id: Organization ID
            session_purpose: Purpose of session
            system_name: System being maintained
            personnel_id: Personnel ID
            authorized_by_user_id: User ID authorizing
            access_method: Access method (SSH, RDP, etc.)
            system_ip_address: System IP address
            system_hostname: System hostname
            maintenance_id: Associated maintenance ID
            access_protocol: Access protocol (TLS, IPsec, etc.)
            encryption_required: Encryption required
            encryption_method: Encryption method
            authorization_expires_at: When authorization expires
            session_monitored: Whether session is monitored
            allowed_commands: Commands allowed
            restricted_commands: Commands restricted
            allowed_files: Files allowed
            restricted_files: Files restricted
            
        Returns:
            Created NonlocalMaintenance record
        """
        session_number = NonlocalMaintenanceService._generate_session_number(db, org_id)
        
        if not authorization_expires_at:
            authorization_expires_at = datetime.now(timezone.utc) + timedelta(hours=8)
        
        session = NonlocalMaintenance(
            org_id=org_id,
            session_number=session_number,
            session_purpose=session_purpose,
            maintenance_id=maintenance_id,
            system_name=system_name,
            system_ip_address=system_ip_address,
            system_hostname=system_hostname,
            personnel_id=personnel_id,
            authorized_by_user_id=authorized_by_user_id,
            authorized_at=datetime.now(timezone.utc),
            authorization_expires_at=authorization_expires_at,
            access_method=access_method,
            access_protocol=access_protocol,
            encryption_required=encryption_required,
            encryption_method=encryption_method,
            session_status=RemoteMaintenanceStatus.ACTIVE.value,
            session_start_date=datetime.now(timezone.utc),
            session_monitored=session_monitored,
            allowed_commands=allowed_commands,
            restricted_commands=restricted_commands,
            allowed_files=allowed_files,
            restricted_files=restricted_files,
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Log audit event
        NonlocalMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=authorized_by_user_id,
            action="create_remote_maintenance_session",
            resource_type="nonlocal_maintenance",
            resource_id=str(session.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "session_number": session_number,
                "system_name": system_name,
                "access_method": access_method,
            },
        )
        
        logger.info(
            "Created remote maintenance session: session_number=%s, system=%s",
            session_number,
            system_name,
        )
        
        return session
    
    @staticmethod
    def terminate_session(
        db: Session,
        session_id: UUID,
        org_id: int,
        terminated_by_user_id: Optional[int] = None,
        termination_reason: Optional[str] = None,
    ) -> NonlocalMaintenance:
        """
        Terminate a remote maintenance session (MA-4).
        
        Args:
            db: Database session
            session_id: Session ID
            org_id: Organization ID
            terminated_by_user_id: User ID terminating
            termination_reason: Reason for termination
            
        Returns:
            Updated NonlocalMaintenance record
        """
        session = db.query(NonlocalMaintenance).filter(
            NonlocalMaintenance.id == session_id,
            NonlocalMaintenance.org_id == org_id,
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.session_status != RemoteMaintenanceStatus.ACTIVE.value:
            raise ValueError(f"Session status is {session.session_status}, not active")
        
        session.session_status = RemoteMaintenanceStatus.TERMINATED.value
        session.session_end_date = datetime.now(timezone.utc)
        session.terminated_by_user_id = terminated_by_user_id
        session.termination_reason = termination_reason
        
        db.commit()
        db.refresh(session)
        
        # Log audit event
        NonlocalMaintenanceService._log_audit(
            db=db,
            org_id=org_id,
            user_id=terminated_by_user_id,
            action="terminate_remote_maintenance_session",
            resource_type="nonlocal_maintenance",
            resource_id=str(session_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "session_number": session.session_number,
                "termination_reason": termination_reason,
            },
        )
        
        logger.info("Terminated remote maintenance session: session_id=%s", session_id)
        
        return session
    
    @staticmethod
    def list_sessions(
        db: Session,
        org_id: int,
        session_status: Optional[str] = None,
        system_name: Optional[str] = None,
        personnel_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[NonlocalMaintenance]:
        """
        List remote maintenance sessions (MA-4).
        
        Args:
            db: Database session
            org_id: Organization ID
            session_status: Optional status filter
            system_name: Optional system name filter
            personnel_id: Optional personnel ID filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of NonlocalMaintenance records
        """
        query = db.query(NonlocalMaintenance).filter(
            NonlocalMaintenance.org_id == org_id,
        )
        
        if session_status:
            query = query.filter(NonlocalMaintenance.session_status == session_status)
        
        if system_name:
            query = query.filter(NonlocalMaintenance.system_name.ilike(f"%{system_name}%"))
        
        if personnel_id:
            query = query.filter(NonlocalMaintenance.personnel_id == personnel_id)
        
        return query.order_by(desc(NonlocalMaintenance.session_start_date)).limit(limit).offset(offset).all()
    
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
        """Log remote maintenance audit event."""
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
