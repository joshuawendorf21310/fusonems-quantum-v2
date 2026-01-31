"""
CP-3: Contingency Training Service

Manages contingency training schedules, completion tracking, and drill execution.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.contingency import (
    ContingencyTraining,
    ContingencyDrill,
    TrainingStatus,
    DrillStatus,
)
from utils.logger import logger


class ContingencyTrainingService:
    """Service for managing contingency training (CP-3)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    # Training methods
    
    def create_training(
        self,
        training_name: str,
        training_type: str,
        scheduled_date: datetime,
        user_email: str,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        training_content_path: Optional[str] = None,
        training_materials: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContingencyTraining:
        """Create a new contingency training record"""
        training = ContingencyTraining(
            org_id=self.org_id,
            training_name=training_name,
            training_type=training_type,
            description=description,
            scheduled_date=scheduled_date,
            duration_minutes=duration_minutes,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            status=TrainingStatus.SCHEDULED.value,
            training_content_path=training_content_path,
            training_materials=training_materials,
            metadata=metadata or {},
        )
        
        self.db.add(training)
        self.db.commit()
        self.db.refresh(training)
        
        logger.info(f"Created contingency training {training.id} for {user_email}")
        return training
    
    def get_training(self, training_id: int) -> Optional[ContingencyTraining]:
        """Get a training record by ID"""
        return self.db.query(ContingencyTraining).filter(
            and_(
                ContingencyTraining.id == training_id,
                ContingencyTraining.org_id == self.org_id,
            )
        ).first()
    
    def list_trainings(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        training_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContingencyTraining]:
        """List training records with optional filters"""
        query = self.db.query(ContingencyTraining).filter(
            ContingencyTraining.org_id == self.org_id
        )
        
        if user_id:
            query = query.filter(ContingencyTraining.user_id == user_id)
        
        if status:
            query = query.filter(ContingencyTraining.status == status)
        
        if training_type:
            query = query.filter(ContingencyTraining.training_type == training_type)
        
        return query.order_by(desc(ContingencyTraining.scheduled_date)).offset(offset).limit(limit).all()
    
    def update_training(
        self,
        training_id: int,
        status: Optional[str] = None,
        completion_percentage: Optional[float] = None,
        score: Optional[float] = None,
        passed: Optional[bool] = None,
        completed_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ContingencyTraining]:
        """Update a training record"""
        training = self.get_training(training_id)
        if not training:
            return None
        
        if status is not None:
            training.status = status
        
        if completion_percentage is not None:
            training.completion_percentage = completion_percentage
        
        if score is not None:
            training.score = score
        
        if passed is not None:
            training.passed = passed
        
        if completed_date is not None:
            training.completed_date = completed_date
            if status is None:
                training.status = TrainingStatus.COMPLETED.value
        
        if metadata is not None:
            training.metadata = {**(training.metadata or {}), **metadata}
        
        training.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(training)
        
        logger.info(f"Updated training {training_id}")
        return training
    
    def complete_training(
        self,
        training_id: int,
        completion_percentage: float = 100.0,
        score: Optional[float] = None,
        passed: Optional[bool] = None,
    ) -> Optional[ContingencyTraining]:
        """Mark a training as completed"""
        return self.update_training(
            training_id=training_id,
            status=TrainingStatus.COMPLETED.value,
            completion_percentage=completion_percentage,
            score=score,
            passed=passed,
            completed_date=datetime.utcnow(),
        )
    
    def get_user_trainings(
        self,
        user_id: int,
        status: Optional[str] = None,
    ) -> List[ContingencyTraining]:
        """Get all trainings for a specific user"""
        return self.list_trainings(user_id=user_id, status=status)
    
    def get_upcoming_trainings(self, days_ahead: int = 30) -> List[ContingencyTraining]:
        """Get trainings scheduled within the specified days"""
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(ContingencyTraining).filter(
            and_(
                ContingencyTraining.org_id == self.org_id,
                ContingencyTraining.status == TrainingStatus.SCHEDULED.value,
                ContingencyTraining.scheduled_date <= cutoff_date,
            )
        ).order_by(ContingencyTraining.scheduled_date).all()
    
    # Drill methods
    
    def create_drill(
        self,
        drill_name: str,
        drill_type: str,
        scheduled_date: datetime,
        scenario_description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContingencyDrill:
        """Create a new contingency drill"""
        drill = ContingencyDrill(
            org_id=self.org_id,
            drill_name=drill_name,
            drill_type=drill_type,
            scenario_description=scenario_description,
            scheduled_date=scheduled_date,
            status=DrillStatus.SCHEDULED.value,
            metadata=metadata or {},
        )
        
        self.db.add(drill)
        self.db.commit()
        self.db.refresh(drill)
        
        logger.info(f"Created contingency drill {drill.id}")
        return drill
    
    def get_drill(self, drill_id: int) -> Optional[ContingencyDrill]:
        """Get a drill by ID"""
        return self.db.query(ContingencyDrill).filter(
            and_(
                ContingencyDrill.id == drill_id,
                ContingencyDrill.org_id == self.org_id,
            )
        ).first()
    
    def list_drills(
        self,
        status: Optional[str] = None,
        drill_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContingencyDrill]:
        """List drills with optional filters"""
        query = self.db.query(ContingencyDrill).filter(
            ContingencyDrill.org_id == self.org_id
        )
        
        if status:
            query = query.filter(ContingencyDrill.status == status)
        
        if drill_type:
            query = query.filter(ContingencyDrill.drill_type == drill_type)
        
        return query.order_by(desc(ContingencyDrill.scheduled_date)).offset(offset).limit(limit).all()
    
    def start_drill(self, drill_id: int) -> Optional[ContingencyDrill]:
        """Start a drill"""
        drill = self.get_drill(drill_id)
        if not drill:
            return None
        
        drill.status = DrillStatus.IN_PROGRESS.value
        drill.start_date = datetime.utcnow()
        drill.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(drill)
        
        logger.info(f"Started drill {drill_id}")
        return drill
    
    def complete_drill(
        self,
        drill_id: int,
        drill_results: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        action_items: Optional[List[Dict[str, Any]]] = None,
        participants_count: Optional[int] = None,
    ) -> Optional[ContingencyDrill]:
        """Complete a drill with results"""
        drill = self.get_drill(drill_id)
        if not drill:
            return None
        
        drill.status = DrillStatus.COMPLETED.value
        drill.end_date = datetime.utcnow()
        drill.drill_results = drill_results
        drill.lessons_learned = lessons_learned
        drill.action_items = action_items
        if participants_count is not None:
            drill.participants_count = participants_count
        
        drill.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(drill)
        
        logger.info(f"Completed drill {drill_id}")
        return drill
