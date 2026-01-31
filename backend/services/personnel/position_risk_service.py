"""
PS-2: Position Risk Designation Service
Implements FedRAMP PS-2 requirements for position risk categorization and periodic review.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.personnel_security import PositionRiskDesignation, PositionRiskLevel
from models.user import User
from core.logger import logger


class PositionRiskService:
    """Service for managing position risk designations per FedRAMP PS-2"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_position_risk_designation(
        self,
        org_id: int,
        position_title: str,
        position_id: str,
        department: str,
        risk_level: PositionRiskLevel,
        risk_justification: str,
        requires_clearance: bool = False,
        clearance_level: Optional[str] = None,
        special_requirements: Optional[str] = None,
        review_frequency_months: int = 12,
        created_by_user_id: int = None,
    ) -> PositionRiskDesignation:
        """
        Create a new position risk designation.
        
        Args:
            org_id: Organization ID
            position_title: Position title
            position_id: Unique position identifier
            department: Department name
            risk_level: Risk level (low, moderate, high, critical)
            risk_justification: Justification for risk level
            requires_clearance: Whether security clearance is required
            clearance_level: Required clearance level
            special_requirements: Special requirements text
            review_frequency_months: How often to review (default 12 months)
            created_by_user_id: User creating the designation
            
        Returns:
            Created PositionRiskDesignation
        """
        try:
            # Check if position_id already exists
            existing = self.db.query(PositionRiskDesignation).filter(
                PositionRiskDesignation.position_id == position_id,
                PositionRiskDesignation.org_id == org_id,
            ).first()
            
            if existing:
                raise ValueError(f"Position ID {position_id} already exists")
            
            now = date.today()
            next_review = now + timedelta(days=review_frequency_months * 30)
            
            designation = PositionRiskDesignation(
                org_id=org_id,
                position_title=position_title,
                position_id=position_id,
                department=department,
                risk_level=risk_level,
                risk_justification=risk_justification,
                requires_clearance=requires_clearance,
                clearance_level=clearance_level,
                special_requirements=special_requirements,
                last_review_date=now,
                next_review_date=next_review,
                reviewed_by_user_id=created_by_user_id,
            )
            
            self.db.add(designation)
            self.db.commit()
            self.db.refresh(designation)
            
            logger.info(
                f"Created position risk designation: {position_id} ({risk_level.value})",
                extra={
                    "org_id": org_id,
                    "position_id": position_id,
                    "risk_level": risk_level.value,
                    "event_type": "position_risk.created",
                }
            )
            
            return designation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create position risk designation: {e}", exc_info=True)
            raise
    
    def update_position_risk_designation(
        self,
        designation_id: int,
        org_id: int,
        risk_level: Optional[PositionRiskLevel] = None,
        risk_justification: Optional[str] = None,
        requires_clearance: Optional[bool] = None,
        clearance_level: Optional[str] = None,
        special_requirements: Optional[str] = None,
        updated_by_user_id: int = None,
    ) -> PositionRiskDesignation:
        """
        Update an existing position risk designation.
        
        Args:
            designation_id: Designation ID to update
            org_id: Organization ID (for verification)
            risk_level: New risk level (optional)
            risk_justification: New justification (optional)
            requires_clearance: New clearance requirement (optional)
            clearance_level: New clearance level (optional)
            special_requirements: New special requirements (optional)
            updated_by_user_id: User making the update
            
        Returns:
            Updated PositionRiskDesignation
        """
        try:
            designation = self.db.query(PositionRiskDesignation).filter(
                PositionRiskDesignation.id == designation_id,
                PositionRiskDesignation.org_id == org_id,
            ).first()
            
            if not designation:
                raise ValueError(f"Position risk designation {designation_id} not found")
            
            if risk_level is not None:
                designation.risk_level = risk_level
            if risk_justification is not None:
                designation.risk_justification = risk_justification
            if requires_clearance is not None:
                designation.requires_clearance = requires_clearance
            if clearance_level is not None:
                designation.clearance_level = clearance_level
            if special_requirements is not None:
                designation.special_requirements = special_requirements
            
            designation.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(designation)
            
            logger.info(
                f"Updated position risk designation: {designation.position_id}",
                extra={
                    "org_id": org_id,
                    "designation_id": designation_id,
                    "event_type": "position_risk.updated",
                }
            )
            
            return designation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update position risk designation: {e}", exc_info=True)
            raise
    
    def review_position_risk_designation(
        self,
        designation_id: int,
        org_id: int,
        review_frequency_months: int = 12,
        reviewed_by_user_id: int = None,
    ) -> PositionRiskDesignation:
        """
        Complete a periodic review of a position risk designation.
        
        Args:
            designation_id: Designation ID to review
            org_id: Organization ID (for verification)
            review_frequency_months: Next review frequency
            reviewed_by_user_id: User conducting the review
            
        Returns:
            Updated PositionRiskDesignation
        """
        try:
            designation = self.db.query(PositionRiskDesignation).filter(
                PositionRiskDesignation.id == designation_id,
                PositionRiskDesignation.org_id == org_id,
            ).first()
            
            if not designation:
                raise ValueError(f"Position risk designation {designation_id} not found")
            
            now = date.today()
            next_review = now + timedelta(days=review_frequency_months * 30)
            
            designation.last_review_date = now
            designation.next_review_date = next_review
            designation.reviewed_by_user_id = reviewed_by_user_id
            designation.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(designation)
            
            logger.info(
                f"Reviewed position risk designation: {designation.position_id}",
                extra={
                    "org_id": org_id,
                    "designation_id": designation_id,
                    "event_type": "position_risk.reviewed",
                }
            )
            
            return designation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to review position risk designation: {e}", exc_info=True)
            raise
    
    def get_position_risk_designation(
        self,
        designation_id: int,
        org_id: int,
    ) -> Optional[PositionRiskDesignation]:
        """Get a position risk designation by ID"""
        return self.db.query(PositionRiskDesignation).filter(
            PositionRiskDesignation.id == designation_id,
            PositionRiskDesignation.org_id == org_id,
        ).first()
    
    def list_position_risk_designations(
        self,
        org_id: int,
        risk_level: Optional[PositionRiskLevel] = None,
        department: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PositionRiskDesignation]:
        """
        List position risk designations for an organization.
        
        Args:
            org_id: Organization ID
            risk_level: Filter by risk level (optional)
            department: Filter by department (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of PositionRiskDesignation
        """
        query = self.db.query(PositionRiskDesignation).filter(
            PositionRiskDesignation.org_id == org_id,
        )
        
        if risk_level:
            query = query.filter(PositionRiskDesignation.risk_level == risk_level)
        
        if department:
            query = query.filter(PositionRiskDesignation.department == department)
        
        return query.order_by(
            PositionRiskDesignation.position_title
        ).limit(limit).offset(offset).all()
    
    def get_designations_due_for_review(
        self,
        org_id: int,
        days_ahead: int = 30,
    ) -> List[PositionRiskDesignation]:
        """
        Get position risk designations due for review.
        
        Args:
            org_id: Organization ID
            days_ahead: Number of days ahead to check (default 30)
            
        Returns:
            List of PositionRiskDesignation due for review
        """
        today = date.today()
        review_threshold = today + timedelta(days=days_ahead)
        
        return self.db.query(PositionRiskDesignation).filter(
            PositionRiskDesignation.org_id == org_id,
            PositionRiskDesignation.next_review_date <= review_threshold,
        ).order_by(PositionRiskDesignation.next_review_date).all()
    
    def get_risk_statistics(
        self,
        org_id: int,
    ) -> Dict[str, Any]:
        """
        Get risk level statistics for an organization.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dictionary with risk level counts
        """
        designations = self.db.query(PositionRiskDesignation).filter(
            PositionRiskDesignation.org_id == org_id,
        ).all()
        
        stats = {
            "total_positions": len(designations),
            "by_risk_level": {
                "low": 0,
                "moderate": 0,
                "high": 0,
                "critical": 0,
            },
            "due_for_review": 0,
            "overdue_review": 0,
        }
        
        today = date.today()
        
        for designation in designations:
            stats["by_risk_level"][designation.risk_level.value] += 1
            
            if designation.next_review_date <= today:
                stats["overdue_review"] += 1
            elif designation.next_review_date <= today + timedelta(days=30):
                stats["due_for_review"] += 1
        
        return stats
