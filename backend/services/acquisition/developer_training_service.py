"""
SA-16: Developer-Provided Training Service

FedRAMP SA-16 compliance service for:
- Training requirements
- Completion tracking
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    DeveloperTraining,
    DeveloperTrainingRecord,
    TrainingStatus,
)


class DeveloperTrainingService:
    """Service for SA-16: Developer-Provided Training"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_training(
        self,
        training_name: str,
        training_type: str,
        mandatory: bool = True,
        training_description: Optional[str] = None,
        training_provider: Optional[str] = None,
        training_duration_hours: Optional[float] = None,
        training_format: Optional[str] = None,
        training_url: Optional[str] = None,
        required_for_roles: Optional[List[str]] = None,
        required_for_systems: Optional[List[str]] = None,
        valid_for_days: Optional[int] = None,
        requires_refresher: bool = False,
        refresher_interval_days: Optional[int] = None,
    ) -> DeveloperTraining:
        """Create a developer training"""
        training = DeveloperTraining(
            training_name=training_name,
            training_description=training_description,
            training_type=training_type,
            mandatory=mandatory,
            training_provider=training_provider,
            training_duration_hours=training_duration_hours,
            training_format=training_format,
            training_url=training_url,
            required_for_roles=required_for_roles,
            required_for_systems=required_for_systems,
            valid_for_days=valid_for_days,
            requires_refresher=requires_refresher,
            refresher_interval_days=refresher_interval_days,
        )
        self.db.add(training)
        self.db.commit()
        self.db.refresh(training)
        return training
    
    def create_training_record(
        self,
        developer_training_id: int,
        developer_name: str,
        developer_email: Optional[str] = None,
        developer_role: Optional[str] = None,
    ) -> DeveloperTrainingRecord:
        """Create a training record for a developer"""
        record = DeveloperTrainingRecord(
            developer_training_id=developer_training_id,
            developer_name=developer_name,
            developer_email=developer_email,
            developer_role=developer_role,
            status=TrainingStatus.REQUIRED.value,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def enroll_developer(
        self,
        record_id: int,
    ) -> DeveloperTrainingRecord:
        """Enroll a developer in training"""
        record = self.db.query(DeveloperTrainingRecord).filter(
            DeveloperTrainingRecord.id == record_id
        ).first()
        if not record:
            raise ValueError(f"Training record {record_id} not found")
        
        record.status = TrainingStatus.ENROLLED.value
        record.enrolled_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def start_training(
        self,
        record_id: int,
    ) -> DeveloperTrainingRecord:
        """Mark training as started"""
        record = self.db.query(DeveloperTrainingRecord).filter(
            DeveloperTrainingRecord.id == record_id
        ).first()
        if not record:
            raise ValueError(f"Training record {record_id} not found")
        
        record.status = TrainingStatus.IN_PROGRESS.value
        record.started_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def complete_training(
        self,
        record_id: int,
        score: Optional[float] = None,
        passed: Optional[bool] = None,
        certificate_number: Optional[str] = None,
        certificate_url: Optional[str] = None,
    ) -> DeveloperTrainingRecord:
        """Complete training"""
        record = self.db.query(DeveloperTrainingRecord).filter(
            DeveloperTrainingRecord.id == record_id
        ).first()
        if not record:
            raise ValueError(f"Training record {record_id} not found")
        
        record.status = TrainingStatus.COMPLETED.value
        record.completed_date = datetime.utcnow()
        record.completion_percentage = 100.0
        
        if score is not None:
            record.score = score
        
        if passed is not None:
            record.passed = passed
        
        if certificate_number:
            record.certificate_number = certificate_number
            record.certificate_issued = True
        
        if certificate_url:
            record.certificate_url = certificate_url
        
        # Calculate expiration date
        training = self.db.query(DeveloperTraining).filter(
            DeveloperTraining.id == record.developer_training_id
        ).first()
        if training and training.valid_for_days:
            record.expires_date = datetime.utcnow() + timedelta(days=training.valid_for_days)
        
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def check_expirations(self) -> List[DeveloperTrainingRecord]:
        """Check for expired training records"""
        now = datetime.utcnow()
        expired_records = self.db.query(DeveloperTrainingRecord).filter(
            and_(
                DeveloperTrainingRecord.expires_date.isnot(None),
                DeveloperTrainingRecord.expires_date < now,
                DeveloperTrainingRecord.is_expired == False,
            )
        ).all()
        
        for record in expired_records:
            record.is_expired = True
            record.status = TrainingStatus.EXPIRED.value
        
        self.db.commit()
        return expired_records
    
    def list_training_records(
        self,
        developer_email: Optional[str] = None,
        developer_training_id: Optional[int] = None,
        status: Optional[TrainingStatus] = None,
        is_expired: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DeveloperTrainingRecord], int]:
        """List training records"""
        query = self.db.query(DeveloperTrainingRecord)
        
        if developer_email:
            query = query.filter(DeveloperTrainingRecord.developer_email == developer_email)
        
        if developer_training_id:
            query = query.filter(DeveloperTrainingRecord.developer_training_id == developer_training_id)
        
        if status:
            query = query.filter(DeveloperTrainingRecord.status == status.value)
        
        if is_expired is not None:
            query = query.filter(DeveloperTrainingRecord.is_expired == is_expired)
        
        total = query.count()
        records = query.order_by(desc(DeveloperTrainingRecord.created_at)).offset(offset).limit(limit).all()
        
        return records, total
    
    def get_training_summary(self, developer_email: Optional[str] = None) -> Dict[str, Any]:
        """Get training summary"""
        query = self.db.query(DeveloperTrainingRecord)
        
        if developer_email:
            query = query.filter(DeveloperTrainingRecord.developer_email == developer_email)
        
        records = query.all()
        
        return {
            "total_training_records": len(records),
            "completed": sum(1 for r in records if r.status == TrainingStatus.COMPLETED.value),
            "in_progress": sum(1 for r in records if r.status == TrainingStatus.IN_PROGRESS.value),
            "required": sum(1 for r in records if r.status == TrainingStatus.REQUIRED.value),
            "expired": sum(1 for r in records if r.is_expired),
            "expiring_soon": self._get_expiring_soon(records),
        }
    
    def _get_expiring_soon(self, records: List[DeveloperTrainingRecord], days: int = 30) -> int:
        """Get count of records expiring soon"""
        cutoff = datetime.utcnow() + timedelta(days=days)
        return sum(
            1 for r in records
            if r.expires_date and r.expires_date <= cutoff and not r.is_expired
        )
