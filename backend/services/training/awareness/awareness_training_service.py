"""
AT-2: Security Awareness Training Service
Implements FedRAMP AT-2 requirements for training module management, completion tracking, and automated reminders.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.awareness_training import (
    SecurityAwarenessTraining,
    SecurityAwarenessTrainingAssignment,
    TrainingStatus,
    TrainingDeliveryMethod,
)
from models.user import User
from core.logger import logger


class AwarenessTrainingService:
    """Service for managing security awareness training per FedRAMP AT-2"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_training_module(
        self,
        org_id: int,
        module_code: str,
        module_name: str,
        module_description: Optional[str] = None,
        module_category: str = "general",
        delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE,
        duration_minutes: int = 60,
        training_content_path: Optional[str] = None,
        mandatory: bool = True,
        required_frequency_months: int = 12,
        passing_score_percentage: float = 80.0,
        reminder_days_before_due: Optional[List[int]] = None,
        created_by_user_id: int = None,
    ) -> SecurityAwarenessTraining:
        """
        Create a new security awareness training module.
        
        Args:
            org_id: Organization ID
            module_code: Unique module code
            module_name: Module name
            module_description: Module description
            module_category: Module category
            delivery_method: Delivery method
            duration_minutes: Duration in minutes
            training_content_path: Path to training content
            mandatory: Whether training is mandatory
            required_frequency_months: How often training must be completed
            passing_score_percentage: Required passing score
            reminder_days_before_due: Days before due to send reminders
            created_by_user_id: User creating the module
            
        Returns:
            Created SecurityAwarenessTraining
        """
        try:
            # Check if module_code already exists
            existing = self.db.query(SecurityAwarenessTraining).filter(
                SecurityAwarenessTraining.module_code == module_code,
                SecurityAwarenessTraining.org_id == org_id,
            ).first()
            
            if existing:
                raise ValueError(f"Module code {module_code} already exists")
            
            reminder_days = reminder_days_before_due or [30, 15, 7]
            
            training = SecurityAwarenessTraining(
                org_id=org_id,
                module_code=module_code,
                module_name=module_name,
                module_description=module_description,
                module_category=module_category,
                delivery_method=delivery_method,
                duration_minutes=duration_minutes,
                training_content_path=training_content_path,
                mandatory=mandatory,
                required_frequency_months=required_frequency_months,
                passing_score_percentage=passing_score_percentage,
                reminder_days_before_due=reminder_days,
                active=True,
                created_by_user_id=created_by_user_id,
            )
            
            self.db.add(training)
            self.db.commit()
            self.db.refresh(training)
            
            logger.info(
                f"Created security awareness training module: {module_code}",
                extra={
                    "org_id": org_id,
                    "module_code": module_code,
                    "event_type": "awareness_training.created",
                }
            )
            
            return training
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create training module: {e}", exc_info=True)
            raise
    
    def assign_training(
        self,
        org_id: int,
        user_id: int,
        training_id: int,
        due_date: Optional[date] = None,
        assigned_by_user_id: int = None,
    ) -> SecurityAwarenessTrainingAssignment:
        """
        Assign training to a user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            training_id: Training module ID
            due_date: Due date (defaults to required_frequency_months from now)
            assigned_by_user_id: User assigning the training
            
        Returns:
            Created SecurityAwarenessTrainingAssignment
        """
        try:
            training = self.db.query(SecurityAwarenessTraining).filter(
                SecurityAwarenessTraining.id == training_id,
                SecurityAwarenessTraining.org_id == org_id,
            ).first()
            
            if not training:
                raise ValueError(f"Training module {training_id} not found")
            
            assigned_date = date.today()
            if not due_date:
                due_date = assigned_date + timedelta(days=training.required_frequency_months * 30)
            
            assignment = SecurityAwarenessTrainingAssignment(
                org_id=org_id,
                user_id=user_id,
                training_id=training_id,
                assigned_date=assigned_date,
                due_date=due_date,
                status=TrainingStatus.NOT_STARTED,
                assigned_by_user_id=assigned_by_user_id or user_id,
            )
            
            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)
            
            logger.info(
                f"Assigned training {training_id} to user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "training_id": training_id,
                    "event_type": "awareness_training.assigned",
                }
            )
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to assign training: {e}", exc_info=True)
            raise
    
    def start_training(
        self,
        assignment_id: int,
        org_id: int,
    ) -> SecurityAwarenessTrainingAssignment:
        """
        Mark training as started.
        
        Args:
            assignment_id: Assignment ID
            org_id: Organization ID (for verification)
            
        Returns:
            Updated SecurityAwarenessTrainingAssignment
        """
        try:
            assignment = self.db.query(SecurityAwarenessTrainingAssignment).filter(
                SecurityAwarenessTrainingAssignment.id == assignment_id,
                SecurityAwarenessTrainingAssignment.org_id == org_id,
            ).first()
            
            if not assignment:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            assignment.status = TrainingStatus.IN_PROGRESS
            assignment.started_at = datetime.utcnow()
            assignment.attempt_count += 1
            assignment.last_attempt_at = datetime.utcnow()
            assignment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(assignment)
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start training: {e}", exc_info=True)
            raise
    
    def complete_training(
        self,
        assignment_id: int,
        org_id: int,
        score_percentage: float,
        passed: bool = None,
    ) -> SecurityAwarenessTrainingAssignment:
        """
        Complete training assignment.
        
        Args:
            assignment_id: Assignment ID
            org_id: Organization ID (for verification)
            score_percentage: Score achieved
            passed: Whether training was passed (auto-calculated if None)
            
        Returns:
            Updated SecurityAwarenessTrainingAssignment
        """
        try:
            assignment = self.db.query(SecurityAwarenessTrainingAssignment).filter(
                SecurityAwarenessTrainingAssignment.id == assignment_id,
                SecurityAwarenessTrainingAssignment.org_id == org_id,
            ).first()
            
            if not assignment:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            training = self.db.query(SecurityAwarenessTraining).filter(
                SecurityAwarenessTraining.id == assignment.training_id,
            ).first()
            
            if passed is None:
                passed = score_percentage >= training.passing_score_percentage
            
            assignment.status = TrainingStatus.COMPLETED if passed else TrainingStatus.FAILED
            assignment.completed_at = datetime.utcnow()
            assignment.score_percentage = score_percentage
            assignment.passed = passed
            assignment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(assignment)
            
            logger.info(
                f"Completed training assignment {assignment_id}",
                extra={
                    "org_id": org_id,
                    "assignment_id": assignment_id,
                    "user_id": assignment.user_id,
                    "passed": passed,
                    "event_type": "awareness_training.completed",
                }
            )
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete training: {e}", exc_info=True)
            raise
    
    def get_training_module(
        self,
        training_id: int,
        org_id: int,
    ) -> Optional[SecurityAwarenessTraining]:
        """Get a training module by ID"""
        return self.db.query(SecurityAwarenessTraining).filter(
            SecurityAwarenessTraining.id == training_id,
            SecurityAwarenessTraining.org_id == org_id,
        ).first()
    
    def list_training_modules(
        self,
        org_id: int,
        mandatory: Optional[bool] = None,
        active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityAwarenessTraining]:
        """
        List training modules for an organization.
        
        Args:
            org_id: Organization ID
            mandatory: Filter by mandatory status (optional)
            active: Filter by active status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of SecurityAwarenessTraining
        """
        query = self.db.query(SecurityAwarenessTraining).filter(
            SecurityAwarenessTraining.org_id == org_id,
        )
        
        if mandatory is not None:
            query = query.filter(SecurityAwarenessTraining.mandatory == mandatory)
        
        if active is not None:
            query = query.filter(SecurityAwarenessTraining.active == active)
        
        return query.order_by(
            SecurityAwarenessTraining.module_name
        ).limit(limit).offset(offset).all()
    
    def get_user_assignments(
        self,
        org_id: int,
        user_id: int,
        status: Optional[TrainingStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityAwarenessTrainingAssignment]:
        """
        Get training assignments for a user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of SecurityAwarenessTrainingAssignment
        """
        query = self.db.query(SecurityAwarenessTrainingAssignment).filter(
            SecurityAwarenessTrainingAssignment.org_id == org_id,
            SecurityAwarenessTrainingAssignment.user_id == user_id,
        )
        
        if status:
            query = query.filter(SecurityAwarenessTrainingAssignment.status == status)
        
        return query.order_by(
            SecurityAwarenessTrainingAssignment.due_date
        ).limit(limit).offset(offset).all()
    
    def get_overdue_assignments(
        self,
        org_id: int,
    ) -> List[SecurityAwarenessTrainingAssignment]:
        """
        Get overdue training assignments.
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of overdue SecurityAwarenessTrainingAssignment
        """
        today = date.today()
        
        return self.db.query(SecurityAwarenessTrainingAssignment).filter(
            SecurityAwarenessTrainingAssignment.org_id == org_id,
            SecurityAwarenessTrainingAssignment.due_date < today,
            SecurityAwarenessTrainingAssignment.status != TrainingStatus.COMPLETED,
        ).order_by(SecurityAwarenessTrainingAssignment.due_date).all()
    
    def get_assignments_due_soon(
        self,
        org_id: int,
        days_ahead: int = 30,
    ) -> List[SecurityAwarenessTrainingAssignment]:
        """
        Get training assignments due soon.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 30)
            
        Returns:
            List of SecurityAwarenessTrainingAssignment due soon
        """
        today = date.today()
        threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(SecurityAwarenessTrainingAssignment).filter(
            SecurityAwarenessTrainingAssignment.org_id == org_id,
            SecurityAwarenessTrainingAssignment.due_date <= threshold,
            SecurityAwarenessTrainingAssignment.due_date >= today,
            SecurityAwarenessTrainingAssignment.status != TrainingStatus.COMPLETED,
        ).order_by(SecurityAwarenessTrainingAssignment.due_date).all()
