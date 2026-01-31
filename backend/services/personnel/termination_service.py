"""
PS-4: Personnel Termination Service
Implements FedRAMP PS-4 requirements for termination workflow, access revocation, and exit interviews.
"""
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.personnel_security import PersonnelTermination, TerminationStatus
from models.user import User, AccountStatus
from core.logger import logger


class TerminationService:
    """Service for managing personnel termination per FedRAMP PS-4"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initiate_termination(
        self,
        org_id: int,
        user_id: int,
        termination_date: date,
        termination_reason: str,
        termination_type: str,  # voluntary, involuntary, retirement
        termination_notes: Optional[str] = None,
        initiated_by_user_id: int = None,
    ) -> PersonnelTermination:
        """
        Initiate a personnel termination.
        
        Args:
            org_id: Organization ID
            user_id: User ID to terminate
            termination_date: Termination date
            termination_reason: Reason for termination
            termination_type: Type of termination
            termination_notes: Additional notes
            initiated_by_user_id: User initiating the termination
            
        Returns:
            Created PersonnelTermination
        """
        try:
            termination = PersonnelTermination(
                org_id=org_id,
                user_id=user_id,
                termination_date=termination_date,
                termination_reason=termination_reason,
                termination_type=termination_type,
                termination_notes=termination_notes,
                status=TerminationStatus.INITIATED,
                termination_initiated_by_user_id=initiated_by_user_id,
            )
            
            self.db.add(termination)
            self.db.commit()
            self.db.refresh(termination)
            
            logger.info(
                f"Initiated termination for user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "termination_type": termination_type,
                    "event_type": "termination.initiated",
                }
            )
            
            return termination
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to initiate termination: {e}", exc_info=True)
            raise
    
    def revoke_access(
        self,
        termination_id: int,
        org_id: int,
        systems_access_revoked: List[str],
        revoked_by_user_id: int = None,
    ) -> PersonnelTermination:
        """
        Revoke system access for terminated personnel.
        
        Args:
            termination_id: Termination ID
            org_id: Organization ID (for verification)
            systems_access_revoked: List of systems where access was revoked
            revoked_by_user_id: User revoking access
            
        Returns:
            Updated PersonnelTermination
        """
        try:
            termination = self.db.query(PersonnelTermination).filter(
                PersonnelTermination.id == termination_id,
                PersonnelTermination.org_id == org_id,
            ).first()
            
            if not termination:
                raise ValueError(f"Termination {termination_id} not found")
            
            # Revoke user account access
            user = self.db.query(User).filter(User.id == termination.user_id).first()
            if user:
                user.account_status = AccountStatus.TERMINATED.value
                user.deactivation_reason = f"Termination: {termination.termination_reason}"
            
            termination.access_revoked_at = datetime.utcnow()
            termination.access_revoked_by_user_id = revoked_by_user_id
            termination.systems_access_revoked = systems_access_revoked
            termination.status = TerminationStatus.ACCESS_REVOKED
            termination.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(termination)
            
            logger.info(
                f"Revoked access for termination {termination_id}",
                extra={
                    "org_id": org_id,
                    "termination_id": termination_id,
                    "user_id": termination.user_id,
                    "event_type": "termination.access_revoked",
                }
            )
            
            return termination
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke access: {e}", exc_info=True)
            raise
    
    def complete_exit_interview(
        self,
        termination_id: int,
        org_id: int,
        exit_interview_notes: str,
        conducted_by_user_id: int = None,
    ) -> PersonnelTermination:
        """
        Complete exit interview for terminated personnel.
        
        Args:
            termination_id: Termination ID
            org_id: Organization ID (for verification)
            exit_interview_notes: Exit interview notes
            conducted_by_user_id: User conducting the interview
            
        Returns:
            Updated PersonnelTermination
        """
        try:
            termination = self.db.query(PersonnelTermination).filter(
                PersonnelTermination.id == termination_id,
                PersonnelTermination.org_id == org_id,
            ).first()
            
            if not termination:
                raise ValueError(f"Termination {termination_id} not found")
            
            termination.exit_interview_completed = True
            termination.exit_interview_date = date.today()
            termination.exit_interview_notes = exit_interview_notes
            termination.exit_interview_conducted_by_user_id = conducted_by_user_id
            
            # Update status if access already revoked
            if termination.status == TerminationStatus.ACCESS_REVOKED:
                termination.status = TerminationStatus.EXIT_INTERVIEW_COMPLETED
            
            termination.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(termination)
            
            logger.info(
                f"Completed exit interview for termination {termination_id}",
                extra={
                    "org_id": org_id,
                    "termination_id": termination_id,
                    "event_type": "termination.exit_interview_completed",
                }
            )
            
            return termination
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete exit interview: {e}", exc_info=True)
            raise
    
    def record_asset_return(
        self,
        termination_id: int,
        org_id: int,
        assets_returned_list: List[str],
    ) -> PersonnelTermination:
        """
        Record asset return for terminated personnel.
        
        Args:
            termination_id: Termination ID
            org_id: Organization ID (for verification)
            assets_returned_list: List of assets returned
            
        Returns:
            Updated PersonnelTermination
        """
        try:
            termination = self.db.query(PersonnelTermination).filter(
                PersonnelTermination.id == termination_id,
                PersonnelTermination.org_id == org_id,
            ).first()
            
            if not termination:
                raise ValueError(f"Termination {termination_id} not found")
            
            termination.assets_returned = True
            termination.assets_returned_date = date.today()
            termination.assets_returned_list = assets_returned_list
            
            # Update status
            if termination.status == TerminationStatus.EXIT_INTERVIEW_COMPLETED:
                termination.status = TerminationStatus.ASSETS_RETURNED
            
            termination.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(termination)
            
            logger.info(
                f"Recorded asset return for termination {termination_id}",
                extra={
                    "org_id": org_id,
                    "termination_id": termination_id,
                    "event_type": "termination.assets_returned",
                }
            )
            
            return termination
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record asset return: {e}", exc_info=True)
            raise
    
    def complete_termination(
        self,
        termination_id: int,
        org_id: int,
        final_paycheck_processed: bool = False,
        benefits_terminated: bool = False,
        cobra_notification_sent: bool = False,
    ) -> PersonnelTermination:
        """
        Complete the termination process.
        
        Args:
            termination_id: Termination ID
            org_id: Organization ID (for verification)
            final_paycheck_processed: Whether final paycheck was processed
            benefits_terminated: Whether benefits were terminated
            cobra_notification_sent: Whether COBRA notification was sent
            
        Returns:
            Updated PersonnelTermination
        """
        try:
            termination = self.db.query(PersonnelTermination).filter(
                PersonnelTermination.id == termination_id,
                PersonnelTermination.org_id == org_id,
            ).first()
            
            if not termination:
                raise ValueError(f"Termination {termination_id} not found")
            
            termination.status = TerminationStatus.COMPLETED
            termination.final_paycheck_processed = final_paycheck_processed
            termination.benefits_terminated = benefits_terminated
            termination.cobra_notification_sent = cobra_notification_sent
            termination.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(termination)
            
            logger.info(
                f"Completed termination {termination_id}",
                extra={
                    "org_id": org_id,
                    "termination_id": termination_id,
                    "event_type": "termination.completed",
                }
            )
            
            return termination
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete termination: {e}", exc_info=True)
            raise
    
    def get_termination(
        self,
        termination_id: int,
        org_id: int,
    ) -> Optional[PersonnelTermination]:
        """Get a termination by ID"""
        return self.db.query(PersonnelTermination).filter(
            PersonnelTermination.id == termination_id,
            PersonnelTermination.org_id == org_id,
        ).first()
    
    def list_terminations(
        self,
        org_id: int,
        user_id: Optional[int] = None,
        status: Optional[TerminationStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PersonnelTermination]:
        """
        List terminations for an organization.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of PersonnelTermination
        """
        query = self.db.query(PersonnelTermination).filter(
            PersonnelTermination.org_id == org_id,
        )
        
        if user_id:
            query = query.filter(PersonnelTermination.user_id == user_id)
        
        if status:
            query = query.filter(PersonnelTermination.status == status)
        
        return query.order_by(
            PersonnelTermination.termination_date.desc()
        ).limit(limit).offset(offset).all()
