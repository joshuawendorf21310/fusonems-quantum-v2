"""
PS-3: Personnel Screening Service
Implements FedRAMP PS-3 requirements for background checks, screening, and rescreening.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.personnel_security import PersonnelScreening, ScreeningStatus
from models.personnel_security import PositionRiskDesignation
from models.user import User
from core.logger import logger


class ScreeningService:
    """Service for managing personnel screening per FedRAMP PS-3"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initiate_screening(
        self,
        org_id: int,
        user_id: int,
        position_risk_id: int,
        screening_type: str = "initial",  # initial, periodic, rescreening
        rescreening_frequency_months: int = 36,
        created_by_user_id: int = None,
    ) -> PersonnelScreening:
        """
        Initiate a personnel screening.
        
        Args:
            org_id: Organization ID
            user_id: User ID to screen
            position_risk_id: Position risk designation ID
            screening_type: Type of screening
            rescreening_frequency_months: Frequency for rescreening (default 36 months)
            created_by_user_id: User initiating the screening
            
        Returns:
            Created PersonnelScreening
        """
        try:
            # Get position risk to determine requirements
            position_risk = self.db.query(PositionRiskDesignation).filter(
                PositionRiskDesignation.id == position_risk_id,
                PositionRiskDesignation.org_id == org_id,
            ).first()
            
            if not position_risk:
                raise ValueError(f"Position risk designation {position_risk_id} not found")
            
            # Determine screening requirements based on risk level
            background_check_required = True
            credit_check_required = position_risk.risk_level.value in ["high", "critical"]
            drug_test_required = position_risk.risk_level.value in ["moderate", "high", "critical"]
            
            now = date.today()
            expiration_date = None
            next_rescreening_date = None
            
            if screening_type in ["periodic", "rescreening"]:
                expiration_date = now + timedelta(days=rescreening_frequency_months * 30)
                next_rescreening_date = expiration_date
            
            screening = PersonnelScreening(
                org_id=org_id,
                user_id=user_id,
                position_risk_id=position_risk_id,
                screening_type=screening_type,
                status=ScreeningStatus.PENDING,
                background_check_required=background_check_required,
                credit_check_required=credit_check_required,
                drug_test_required=drug_test_required,
                reference_check_required=True,
                screening_initiated_date=now,
                screening_expiration_date=expiration_date,
                rescreening_required=True,
                rescreening_frequency_months=rescreening_frequency_months,
                next_rescreening_date=next_rescreening_date,
                screening_officer_id=created_by_user_id,
            )
            
            self.db.add(screening)
            self.db.commit()
            self.db.refresh(screening)
            
            logger.info(
                f"Initiated screening for user {user_id} ({screening_type})",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "screening_type": screening_type,
                    "event_type": "screening.initiated",
                }
            )
            
            return screening
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to initiate screening: {e}", exc_info=True)
            raise
    
    def update_screening_component(
        self,
        screening_id: int,
        org_id: int,
        component: str,  # background_check, credit_check, drug_test, reference_check
        completed: bool = True,
        result: Optional[str] = None,
        completed_date: Optional[date] = None,
    ) -> PersonnelScreening:
        """
        Update a screening component status.
        
        Args:
            screening_id: Screening ID
            org_id: Organization ID (for verification)
            component: Component to update
            completed: Whether component is completed
            result: Result of the check (optional)
            completed_date: Completion date (optional)
            
        Returns:
            Updated PersonnelScreening
        """
        try:
            screening = self.db.query(PersonnelScreening).filter(
                PersonnelScreening.id == screening_id,
                PersonnelScreening.org_id == org_id,
            ).first()
            
            if not screening:
                raise ValueError(f"Screening {screening_id} not found")
            
            completed_date = completed_date or date.today()
            
            if component == "background_check":
                screening.background_check_completed = completed
                if completed:
                    screening.background_check_date = completed_date
                    screening.background_check_result = result
            elif component == "credit_check":
                screening.credit_check_completed = completed
                if completed:
                    screening.credit_check_date = completed_date
            elif component == "drug_test":
                screening.drug_test_completed = completed
                if completed:
                    screening.drug_test_date = completed_date
                    screening.drug_test_result = result
            elif component == "reference_check":
                screening.reference_check_completed = completed
                if completed:
                    screening.reference_check_date = completed_date
            
            # Check if all required components are completed
            all_completed = True
            if screening.background_check_required and not screening.background_check_completed:
                all_completed = False
            if screening.credit_check_required and not screening.credit_check_completed:
                all_completed = False
            if screening.drug_test_required and not screening.drug_test_completed:
                all_completed = False
            if screening.reference_check_required and not screening.reference_check_completed:
                all_completed = False
            
            if all_completed:
                screening.status = ScreeningStatus.COMPLETED
                screening.screening_completed_date = completed_date
            
            screening.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(screening)
            
            logger.info(
                f"Updated screening component {component} for screening {screening_id}",
                extra={
                    "org_id": org_id,
                    "screening_id": screening_id,
                    "component": component,
                    "event_type": "screening.component_updated",
                }
            )
            
            return screening
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update screening component: {e}", exc_info=True)
            raise
    
    def complete_screening(
        self,
        screening_id: int,
        org_id: int,
        result: str,
        notes: Optional[str] = None,
        completed_by_user_id: int = None,
    ) -> PersonnelScreening:
        """
        Complete a screening with final result.
        
        Args:
            screening_id: Screening ID
            org_id: Organization ID (for verification)
            result: Final screening result
            notes: Additional notes
            completed_by_user_id: User completing the screening
            
        Returns:
            Updated PersonnelScreening
        """
        try:
            screening = self.db.query(PersonnelScreening).filter(
                PersonnelScreening.id == screening_id,
                PersonnelScreening.org_id == org_id,
            ).first()
            
            if not screening:
                raise ValueError(f"Screening {screening_id} not found")
            
            screening.status = ScreeningStatus.COMPLETED
            screening.screening_completed_date = date.today()
            screening.screening_result = result
            screening.screening_notes = notes
            screening.screening_officer_id = completed_by_user_id
            
            # Set expiration date if not already set
            if not screening.screening_expiration_date and screening.rescreening_required:
                screening.screening_expiration_date = date.today() + timedelta(
                    days=screening.rescreening_frequency_months * 30
                )
                screening.next_rescreening_date = screening.screening_expiration_date
            
            screening.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(screening)
            
            logger.info(
                f"Completed screening {screening_id} with result: {result}",
                extra={
                    "org_id": org_id,
                    "screening_id": screening_id,
                    "result": result,
                    "event_type": "screening.completed",
                }
            )
            
            return screening
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete screening: {e}", exc_info=True)
            raise
    
    def get_screening(
        self,
        screening_id: int,
        org_id: int,
    ) -> Optional[PersonnelScreening]:
        """Get a screening by ID"""
        return self.db.query(PersonnelScreening).filter(
            PersonnelScreening.id == screening_id,
            PersonnelScreening.org_id == org_id,
        ).first()
    
    def list_screenings(
        self,
        org_id: int,
        user_id: Optional[int] = None,
        status: Optional[ScreeningStatus] = None,
        screening_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PersonnelScreening]:
        """
        List screenings for an organization.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            status: Filter by status (optional)
            screening_type: Filter by type (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of PersonnelScreening
        """
        query = self.db.query(PersonnelScreening).filter(
            PersonnelScreening.org_id == org_id,
        )
        
        if user_id:
            query = query.filter(PersonnelScreening.user_id == user_id)
        
        if status:
            query = query.filter(PersonnelScreening.status == status)
        
        if screening_type:
            query = query.filter(PersonnelScreening.screening_type == screening_type)
        
        return query.order_by(
            PersonnelScreening.screening_initiated_date.desc()
        ).limit(limit).offset(offset).all()
    
    def get_screenings_due_for_rescreening(
        self,
        org_id: int,
        days_ahead: int = 90,
    ) -> List[PersonnelScreening]:
        """
        Get screenings due for rescreening.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 90)
            
        Returns:
            List of PersonnelScreening due for rescreening
        """
        today = date.today()
        threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(PersonnelScreening).filter(
            PersonnelScreening.org_id == org_id,
            PersonnelScreening.rescreening_required == True,
            PersonnelScreening.next_rescreening_date <= threshold,
            PersonnelScreening.status == ScreeningStatus.COMPLETED,
        ).order_by(PersonnelScreening.next_rescreening_date).all()
    
    def get_expired_screenings(
        self,
        org_id: int,
    ) -> List[PersonnelScreening]:
        """
        Get expired screenings.
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of expired PersonnelScreening
        """
        today = date.today()
        
        screenings = self.db.query(PersonnelScreening).filter(
            PersonnelScreening.org_id == org_id,
            PersonnelScreening.screening_expiration_date <= today,
            PersonnelScreening.status == ScreeningStatus.COMPLETED,
        ).all()
        
        # Update status to expired
        for screening in screenings:
            screening.status = ScreeningStatus.EXPIRED
            screening.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return screenings
