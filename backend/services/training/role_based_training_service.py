"""
AT-3: Role-Based Security Training Service
Implements FedRAMP AT-3 requirements for role-specific training requirements, training assignment, and competency validation.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.awareness_training import (
    RoleBasedSecurityTraining,
    RoleBasedTrainingAssignment,
    TrainingStatus,
    TrainingDeliveryMethod,
    CompetencyLevel,
)
from models.user import User, UserRole
from core.logger import logger


class RoleBasedTrainingService:
    """Service for managing role-based security training per FedRAMP AT-3"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_role_training(
        self,
        org_id: int,
        training_code: str,
        training_name: str,
        training_description: Optional[str] = None,
        training_category: str = "general",
        required_role: Optional[str] = None,
        required_roles: Optional[List[str]] = None,
        delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE,
        duration_minutes: int = 60,
        training_content_path: Optional[str] = None,
        mandatory: bool = True,
        required_frequency_months: int = 12,
        passing_score_percentage: float = 80.0,
        requires_competency_validation: bool = False,
        competency_level_required: Optional[CompetencyLevel] = None,
        created_by_user_id: int = None,
    ) -> RoleBasedSecurityTraining:
        """
        Create a new role-based security training.
        
        Args:
            org_id: Organization ID
            training_code: Unique training code
            training_name: Training name
            training_description: Training description
            training_category: Training category
            required_role: Single required role (optional)
            required_roles: Multiple required roles (optional)
            delivery_method: Delivery method
            duration_minutes: Duration in minutes
            training_content_path: Path to training content
            mandatory: Whether training is mandatory
            required_frequency_months: How often training must be completed
            passing_score_percentage: Required passing score
            requires_competency_validation: Whether competency validation is required
            competency_level_required: Required competency level
            created_by_user_id: User creating the training
            
        Returns:
            Created RoleBasedSecurityTraining
        """
        try:
            # Check if training_code already exists
            existing = self.db.query(RoleBasedSecurityTraining).filter(
                RoleBasedSecurityTraining.training_code == training_code,
                RoleBasedSecurityTraining.org_id == org_id,
            ).first()
            
            if existing:
                raise ValueError(f"Training code {training_code} already exists")
            
            if not required_role and not required_roles:
                raise ValueError("Either required_role or required_roles must be provided")
            
            training = RoleBasedSecurityTraining(
                org_id=org_id,
                training_code=training_code,
                training_name=training_name,
                training_description=training_description,
                training_category=training_category,
                required_role=required_role or "",
                required_roles=required_roles,
                delivery_method=delivery_method,
                duration_minutes=duration_minutes,
                training_content_path=training_content_path,
                mandatory=mandatory,
                required_frequency_months=required_frequency_months,
                passing_score_percentage=passing_score_percentage,
                requires_competency_validation=requires_competency_validation,
                competency_level_required=competency_level_required,
                active=True,
                created_by_user_id=created_by_user_id,
            )
            
            self.db.add(training)
            self.db.commit()
            self.db.refresh(training)
            
            logger.info(
                f"Created role-based training: {training_code}",
                extra={
                    "org_id": org_id,
                    "training_code": training_code,
                    "required_role": required_role,
                    "event_type": "role_training.created",
                }
            )
            
            return training
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create role training: {e}", exc_info=True)
            raise
    
    def assign_training(
        self,
        org_id: int,
        user_id: int,
        training_id: int,
        due_date: Optional[date] = None,
        assigned_by_user_id: int = None,
    ) -> RoleBasedTrainingAssignment:
        """
        Assign role-based training to a user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            training_id: Training ID
            due_date: Due date (defaults to required_frequency_months from now)
            assigned_by_user_id: User assigning the training
            
        Returns:
            Created RoleBasedTrainingAssignment
        """
        try:
            training = self.db.query(RoleBasedSecurityTraining).filter(
                RoleBasedSecurityTraining.id == training_id,
                RoleBasedSecurityTraining.org_id == org_id,
            ).first()
            
            if not training:
                raise ValueError(f"Training {training_id} not found")
            
            assigned_date = date.today()
            if not due_date:
                due_date = assigned_date + timedelta(days=training.required_frequency_months * 30)
            
            assignment = RoleBasedTrainingAssignment(
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
                f"Assigned role training {training_id} to user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "training_id": training_id,
                    "event_type": "role_training.assigned",
                }
            )
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to assign training: {e}", exc_info=True)
            raise
    
    def complete_training(
        self,
        assignment_id: int,
        org_id: int,
        score_percentage: float,
        passed: bool = None,
    ) -> RoleBasedTrainingAssignment:
        """
        Complete role-based training assignment.
        
        Args:
            assignment_id: Assignment ID
            org_id: Organization ID (for verification)
            score_percentage: Score achieved
            passed: Whether training was passed (auto-calculated if None)
            
        Returns:
            Updated RoleBasedTrainingAssignment
        """
        try:
            assignment = self.db.query(RoleBasedTrainingAssignment).filter(
                RoleBasedTrainingAssignment.id == assignment_id,
                RoleBasedTrainingAssignment.org_id == org_id,
            ).first()
            
            if not assignment:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            training = self.db.query(RoleBasedSecurityTraining).filter(
                RoleBasedSecurityTraining.id == assignment.training_id,
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
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete training: {e}", exc_info=True)
            raise
    
    def validate_competency(
        self,
        assignment_id: int,
        org_id: int,
        competency_level_achieved: CompetencyLevel,
        assessed_by_user_id: int = None,
    ) -> RoleBasedTrainingAssignment:
        """
        Validate competency for role-based training.
        
        Args:
            assignment_id: Assignment ID
            org_id: Organization ID (for verification)
            competency_level_achieved: Competency level achieved
            assessed_by_user_id: User assessing competency
            
        Returns:
            Updated RoleBasedTrainingAssignment
        """
        try:
            assignment = self.db.query(RoleBasedTrainingAssignment).filter(
                RoleBasedTrainingAssignment.id == assignment_id,
                RoleBasedTrainingAssignment.org_id == org_id,
            ).first()
            
            if not assignment:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            training = self.db.query(RoleBasedSecurityTraining).filter(
                RoleBasedSecurityTraining.id == assignment.training_id,
            ).first()
            
            if not training.requires_competency_validation:
                raise ValueError("This training does not require competency validation")
            
            assignment.competency_assessed = True
            assignment.competency_level_achieved = competency_level_achieved
            assignment.competency_assessed_at = datetime.utcnow()
            assignment.competency_assessed_by_user_id = assessed_by_user_id
            assignment.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(assignment)
            
            logger.info(
                f"Validated competency for assignment {assignment_id}",
                extra={
                    "org_id": org_id,
                    "assignment_id": assignment_id,
                    "competency_level": competency_level_achieved.value,
                    "event_type": "role_training.competency_validated",
                }
            )
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to validate competency: {e}", exc_info=True)
            raise
    
    def get_training(
        self,
        training_id: int,
        org_id: int,
    ) -> Optional[RoleBasedSecurityTraining]:
        """Get a role-based training by ID"""
        return self.db.query(RoleBasedSecurityTraining).filter(
            RoleBasedSecurityTraining.id == training_id,
            RoleBasedSecurityTraining.org_id == org_id,
        ).first()
    
    def list_trainings(
        self,
        org_id: int,
        required_role: Optional[str] = None,
        active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RoleBasedSecurityTraining]:
        """
        List role-based trainings for an organization.
        
        Args:
            org_id: Organization ID
            required_role: Filter by required role (optional)
            active: Filter by active status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of RoleBasedSecurityTraining
        """
        query = self.db.query(RoleBasedSecurityTraining).filter(
            RoleBasedSecurityTraining.org_id == org_id,
        )
        
        if required_role:
            query = query.filter(
                (RoleBasedSecurityTraining.required_role == required_role) |
                (RoleBasedSecurityTraining.required_roles.contains([required_role]))
            )
        
        if active is not None:
            query = query.filter(RoleBasedSecurityTraining.active == active)
        
        return query.order_by(
            RoleBasedSecurityTraining.training_name
        ).limit(limit).offset(offset).all()
    
    def get_user_assignments(
        self,
        org_id: int,
        user_id: int,
        status: Optional[TrainingStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RoleBasedTrainingAssignment]:
        """
        Get role-based training assignments for a user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of RoleBasedTrainingAssignment
        """
        query = self.db.query(RoleBasedTrainingAssignment).filter(
            RoleBasedTrainingAssignment.org_id == org_id,
            RoleBasedTrainingAssignment.user_id == user_id,
        )
        
        if status:
            query = query.filter(RoleBasedTrainingAssignment.status == status)
        
        return query.order_by(
            RoleBasedTrainingAssignment.due_date
        ).limit(limit).offset(offset).all()
