"""
PS-8: Personnel Sanctions Service
Implements FedRAMP PS-8 requirements for sanctions tracking, violation documentation, and remediation plans.
"""
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.personnel_security import PersonnelSanction, SanctionStatus
from models.user import User
from core.logger import logger


class SanctionsService:
    """Service for managing personnel sanctions per FedRAMP PS-8"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_sanction(
        self,
        org_id: int,
        user_id: int,
        violation_type: str,  # security_violation, policy_violation, etc.
        violation_description: str,
        violation_date: date,
        sanction_type: str,  # warning, suspension, termination, etc.
        sanction_severity: str,  # low, medium, high, critical
        sanction_start_date: date,
        sanction_end_date: Optional[date] = None,
        sanction_conditions: Optional[str] = None,
        remediation_required: bool = True,
        remediation_plan: Optional[str] = None,
        incident_report_path: Optional[str] = None,
        supporting_documents: Optional[List[str]] = None,
        notes: Optional[str] = None,
        reported_by_user_id: int = None,
    ) -> PersonnelSanction:
        """
        Create a personnel sanction.
        
        Args:
            org_id: Organization ID
            user_id: User ID being sanctioned
            violation_type: Type of violation
            violation_description: Description of violation
            violation_date: Date of violation
            sanction_type: Type of sanction
            sanction_severity: Severity level
            sanction_start_date: Start date of sanction
            sanction_end_date: End date of sanction (optional)
            sanction_conditions: Conditions of sanction
            remediation_required: Whether remediation is required
            remediation_plan: Remediation plan text
            incident_report_path: Path to incident report
            supporting_documents: List of supporting document paths
            notes: Additional notes
            reported_by_user_id: User reporting the violation
            
        Returns:
            Created PersonnelSanction
        """
        try:
            sanction = PersonnelSanction(
                org_id=org_id,
                user_id=user_id,
                violation_type=violation_type,
                violation_description=violation_description,
                violation_date=violation_date,
                sanction_type=sanction_type,
                sanction_severity=sanction_severity,
                status=SanctionStatus.ACTIVE,
                sanction_start_date=sanction_start_date,
                sanction_end_date=sanction_end_date,
                sanction_conditions=sanction_conditions,
                remediation_required=remediation_required,
                remediation_plan=remediation_plan,
                incident_report_path=incident_report_path,
                supporting_documents=supporting_documents,
                notes=notes,
                reported_by_user_id=reported_by_user_id,
            )
            
            self.db.add(sanction)
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Created sanction for user {user_id}",
                extra={
                    "org_id": org_id,
                    "user_id": user_id,
                    "sanction_type": sanction_type,
                    "sanction_severity": sanction_severity,
                    "event_type": "sanction.created",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create sanction: {e}", exc_info=True)
            raise
    
    def update_sanction(
        self,
        sanction_id: int,
        org_id: int,
        sanction_type: Optional[str] = None,
        sanction_severity: Optional[str] = None,
        sanction_end_date: Optional[date] = None,
        sanction_conditions: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PersonnelSanction:
        """
        Update a personnel sanction.
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            sanction_type: New sanction type (optional)
            sanction_severity: New severity (optional)
            sanction_end_date: New end date (optional)
            sanction_conditions: New conditions (optional)
            notes: Additional notes (optional)
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            if sanction_type is not None:
                sanction.sanction_type = sanction_type
            if sanction_severity is not None:
                sanction.sanction_severity = sanction_severity
            if sanction_end_date is not None:
                sanction.sanction_end_date = sanction_end_date
            if sanction_conditions is not None:
                sanction.sanction_conditions = sanction_conditions
            if notes is not None:
                sanction.notes = notes
            
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Updated sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "event_type": "sanction.updated",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update sanction: {e}", exc_info=True)
            raise
    
    def update_remediation_plan(
        self,
        sanction_id: int,
        org_id: int,
        remediation_plan: str,
    ) -> PersonnelSanction:
        """
        Update remediation plan for a sanction.
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            remediation_plan: Remediation plan text
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.remediation_plan = remediation_plan
            sanction.remediation_required = True
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update remediation plan: {e}", exc_info=True)
            raise
    
    def complete_remediation(
        self,
        sanction_id: int,
        org_id: int,
        remediation_completed_date: Optional[date] = None,
    ) -> PersonnelSanction:
        """
        Mark remediation as completed.
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            remediation_completed_date: Completion date
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.remediation_completed = True
            sanction.remediation_completed_date = remediation_completed_date or date.today()
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Completed remediation for sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "event_type": "sanction.remediation_completed",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete remediation: {e}", exc_info=True)
            raise
    
    def file_appeal(
        self,
        sanction_id: int,
        org_id: int,
        appeal_date: Optional[date] = None,
    ) -> PersonnelSanction:
        """
        File an appeal for a sanction.
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            appeal_date: Appeal filing date
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.appeal_filed = True
            sanction.appeal_date = appeal_date or date.today()
            sanction.status = SanctionStatus.APPEALED
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Filed appeal for sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "event_type": "sanction.appeal_filed",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to file appeal: {e}", exc_info=True)
            raise
    
    def resolve_appeal(
        self,
        sanction_id: int,
        org_id: int,
        appeal_decision: str,
        appeal_decision_date: Optional[date] = None,
    ) -> PersonnelSanction:
        """
        Resolve an appeal for a sanction.
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            appeal_decision: Appeal decision
            appeal_decision_date: Decision date
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.appeal_decision = appeal_decision
            sanction.appeal_decision_date = appeal_decision_date or date.today()
            
            # Update status based on decision
            if appeal_decision.lower() in ["granted", "upheld", "overturned"]:
                sanction.status = SanctionStatus.RESOLVED
            else:
                sanction.status = SanctionStatus.ACTIVE
            
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Resolved appeal for sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "decision": appeal_decision,
                    "event_type": "sanction.appeal_resolved",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to resolve appeal: {e}", exc_info=True)
            raise
    
    def resolve_sanction(
        self,
        sanction_id: int,
        org_id: int,
        reviewed_by_user_id: int = None,
    ) -> PersonnelSanction:
        """
        Resolve a sanction (mark as resolved).
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            reviewed_by_user_id: User resolving the sanction
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.status = SanctionStatus.RESOLVED
            sanction.reviewed_by_user_id = reviewed_by_user_id
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Resolved sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "event_type": "sanction.resolved",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to resolve sanction: {e}", exc_info=True)
            raise
    
    def close_sanction(
        self,
        sanction_id: int,
        org_id: int,
        sanctioned_by_user_id: int = None,
    ) -> PersonnelSanction:
        """
        Close a sanction (mark as closed).
        
        Args:
            sanction_id: Sanction ID
            org_id: Organization ID (for verification)
            sanctioned_by_user_id: User closing the sanction
            
        Returns:
            Updated PersonnelSanction
        """
        try:
            sanction = self.db.query(PersonnelSanction).filter(
                PersonnelSanction.id == sanction_id,
                PersonnelSanction.org_id == org_id,
            ).first()
            
            if not sanction:
                raise ValueError(f"Sanction {sanction_id} not found")
            
            sanction.status = SanctionStatus.CLOSED
            sanction.sanctioned_by_user_id = sanctioned_by_user_id
            sanction.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sanction)
            
            logger.info(
                f"Closed sanction {sanction_id}",
                extra={
                    "org_id": org_id,
                    "sanction_id": sanction_id,
                    "event_type": "sanction.closed",
                }
            )
            
            return sanction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to close sanction: {e}", exc_info=True)
            raise
    
    def get_sanction(
        self,
        sanction_id: int,
        org_id: int,
    ) -> Optional[PersonnelSanction]:
        """Get a sanction by ID"""
        return self.db.query(PersonnelSanction).filter(
            PersonnelSanction.id == sanction_id,
            PersonnelSanction.org_id == org_id,
        ).first()
    
    def list_sanctions(
        self,
        org_id: int,
        user_id: Optional[int] = None,
        violation_type: Optional[str] = None,
        status: Optional[SanctionStatus] = None,
        sanction_severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PersonnelSanction]:
        """
        List sanctions for an organization.
        
        Args:
            org_id: Organization ID
            user_id: Filter by user ID (optional)
            violation_type: Filter by violation type (optional)
            status: Filter by status (optional)
            sanction_severity: Filter by severity (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of PersonnelSanction
        """
        query = self.db.query(PersonnelSanction).filter(
            PersonnelSanction.org_id == org_id,
        )
        
        if user_id:
            query = query.filter(PersonnelSanction.user_id == user_id)
        
        if violation_type:
            query = query.filter(PersonnelSanction.violation_type == violation_type)
        
        if status:
            query = query.filter(PersonnelSanction.status == status)
        
        if sanction_severity:
            query = query.filter(PersonnelSanction.sanction_severity == sanction_severity)
        
        return query.order_by(
            PersonnelSanction.violation_date.desc()
        ).limit(limit).offset(offset).all()
