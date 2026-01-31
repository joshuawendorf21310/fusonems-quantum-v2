"""
CP-9: Information System Backup Service

Manages automated backup scheduling, backup verification,
restore testing, and retention management.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.contingency import (
    SystemBackup,
    BackupSchedule,
    BackupStatus,
    BackupType,
)
from utils.logger import logger


class BackupService:
    """Service for managing system backups (CP-9)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    def create_backup(
        self,
        backup_name: str,
        backup_type: str,
        system_component: str,
        scheduled_time: datetime,
        backup_location: str,
        retention_days: int = 90,
        backup_format: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemBackup:
        """Create a new backup record"""
        retention_until = scheduled_time + timedelta(days=retention_days)
        
        backup = SystemBackup(
            org_id=self.org_id,
            backup_name=backup_name,
            backup_type=backup_type,
            system_component=system_component,
            scheduled_time=scheduled_time,
            backup_location=backup_location,
            status=BackupStatus.SCHEDULED.value,
            backup_format=backup_format,
            retention_days=retention_days,
            retention_until=retention_until,
            metadata=metadata or {},
        )
        
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)
        
        logger.info(f"Created backup {backup_name} for {system_component}")
        return backup
    
    def get_backup(self, backup_id: int) -> Optional[SystemBackup]:
        """Get a backup by ID"""
        return self.db.query(SystemBackup).filter(
            and_(
                SystemBackup.id == backup_id,
                SystemBackup.org_id == self.org_id,
            )
        ).first()
    
    def list_backups(
        self,
        system_component: Optional[str] = None,
        backup_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SystemBackup]:
        """List backups with optional filters"""
        query = self.db.query(SystemBackup).filter(
            SystemBackup.org_id == self.org_id
        )
        
        if system_component:
            query = query.filter(SystemBackup.system_component == system_component)
        
        if backup_type:
            query = query.filter(SystemBackup.backup_type == backup_type)
        
        if status:
            query = query.filter(SystemBackup.status == status)
        
        return query.order_by(desc(SystemBackup.scheduled_time)).offset(offset).limit(limit).all()
    
    def start_backup(self, backup_id: int) -> Optional[SystemBackup]:
        """Mark a backup as started"""
        backup = self.get_backup(backup_id)
        if not backup:
            return None
        
        backup.status = BackupStatus.IN_PROGRESS.value
        backup.start_time = datetime.utcnow()
        backup.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(backup)
        
        logger.info(f"Started backup {backup_id}")
        return backup
    
    def complete_backup(
        self,
        backup_id: int,
        backup_size_bytes: Optional[int] = None,
        compression_ratio: Optional[float] = None,
    ) -> Optional[SystemBackup]:
        """Mark a backup as completed"""
        backup = self.get_backup(backup_id)
        if not backup:
            return None
        
        backup.status = BackupStatus.COMPLETED.value
        backup.end_time = datetime.utcnow()
        
        if backup.start_time:
            duration = (backup.end_time - backup.start_time).total_seconds()
            backup.duration_seconds = int(duration)
        
        if backup_size_bytes is not None:
            backup.backup_size_bytes = backup_size_bytes
        
        if compression_ratio is not None:
            backup.compression_ratio = compression_ratio
        
        backup.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(backup)
        
        logger.info(f"Completed backup {backup_id}")
        return backup
    
    def verify_backup(
        self,
        backup_id: int,
        verification_method: str,
        verification_result: Optional[str] = None,
    ) -> Optional[SystemBackup]:
        """Verify a backup"""
        backup = self.get_backup(backup_id)
        if not backup:
            return None
        
        backup.verification_status = BackupStatus.VERIFIED.value
        backup.verification_time = datetime.utcnow()
        backup.verification_method = verification_method
        backup.verification_result = verification_result
        backup.status = BackupStatus.VERIFIED.value
        backup.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(backup)
        
        logger.info(f"Verified backup {backup_id}")
        return backup
    
    def fail_backup_verification(
        self,
        backup_id: int,
        verification_method: str,
        verification_result: str,
    ) -> Optional[SystemBackup]:
        """Mark backup verification as failed"""
        backup = self.get_backup(backup_id)
        if not backup:
            return None
        
        backup.verification_status = BackupStatus.VERIFICATION_FAILED.value
        backup.verification_time = datetime.utcnow()
        backup.verification_method = verification_method
        backup.verification_result = verification_result
        backup.status = BackupStatus.VERIFICATION_FAILED.value
        backup.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(backup)
        
        logger.warning(f"Backup {backup_id} verification failed")
        return backup
    
    def record_restore_test(
        self,
        backup_id: int,
        restore_test_status: str,
        restore_test_result: Optional[str] = None,
    ) -> Optional[SystemBackup]:
        """Record a restore test for a backup"""
        backup = self.get_backup(backup_id)
        if not backup:
            return None
        
        backup.last_restore_test = datetime.utcnow()
        backup.restore_test_status = restore_test_status
        backup.restore_test_result = restore_test_result
        backup.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(backup)
        
        logger.info(f"Recorded restore test for backup {backup_id}: {restore_test_status}")
        return backup
    
    def get_expired_backups(self) -> List[SystemBackup]:
        """Get backups that have exceeded their retention period"""
        return self.db.query(SystemBackup).filter(
            and_(
                SystemBackup.org_id == self.org_id,
                SystemBackup.retention_until < datetime.utcnow(),
            )
        ).all()
    
    def create_backup_schedule(
        self,
        schedule_name: str,
        system_component: str,
        backup_type: str,
        schedule_frequency: str,
        retention_days: int = 90,
        schedule_cron: Optional[str] = None,
        schedule_time: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BackupSchedule:
        """Create a backup schedule"""
        schedule = BackupSchedule(
            org_id=self.org_id,
            schedule_name=schedule_name,
            system_component=system_component,
            backup_type=backup_type,
            schedule_frequency=schedule_frequency,
            schedule_cron=schedule_cron,
            schedule_time=schedule_time,
            retention_days=retention_days,
            active=True,
            metadata=metadata or {},
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Created backup schedule {schedule_name}")
        return schedule
    
    def get_backup_schedule(self, schedule_id: int) -> Optional[BackupSchedule]:
        """Get a backup schedule by ID"""
        return self.db.query(BackupSchedule).filter(
            and_(
                BackupSchedule.id == schedule_id,
                BackupSchedule.org_id == self.org_id,
            )
        ).first()
    
    def list_backup_schedules(
        self,
        active: Optional[bool] = None,
        system_component: Optional[str] = None,
    ) -> List[BackupSchedule]:
        """List backup schedules"""
        query = self.db.query(BackupSchedule).filter(
            BackupSchedule.org_id == self.org_id
        )
        
        if active is not None:
            query = query.filter(BackupSchedule.active == active)
        
        if system_component:
            query = query.filter(BackupSchedule.system_component == system_component)
        
        return query.order_by(desc(BackupSchedule.created_at)).all()
    
    def update_backup_schedule(
        self,
        schedule_id: int,
        active: Optional[bool] = None,
        retention_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[BackupSchedule]:
        """Update a backup schedule"""
        schedule = self.get_backup_schedule(schedule_id)
        if not schedule:
            return None
        
        if active is not None:
            schedule.active = active
        
        if retention_days is not None:
            schedule.retention_days = retention_days
        
        if metadata is not None:
            schedule.metadata = {**(schedule.metadata or {}), **metadata}
        
        schedule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Updated backup schedule {schedule_id}")
        return schedule
