"""
Predictable Failure Prevention Service for FedRAMP SI-13 Compliance

This service provides:
- Failure prevention tracking
- Redundancy monitoring
- Backup verification

FedRAMP SI-13: Predictable Failure Prevention
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.system_integrity import (
    FailurePreventionAction,
    FailureType,
)
from utils.logger import logger


class FailurePreventionService:
    """
    Service for predictable failure prevention.
    
    FedRAMP SI-13: Predictable Failure Prevention
    """
    
    def __init__(self, db: Session):
        """
        Initialize failure prevention service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_prevention_action(
        self,
        action_id: str,
        action_name: str,
        failure_type: FailureType,
        component_name: str,
        prevention_type: str,
        redundancy_level: Optional[int] = None,
        backup_frequency: Optional[str] = None,
    ) -> FailurePreventionAction:
        """
        Create a failure prevention action.
        
        Args:
            action_id: Unique action identifier
            action_name: Action name
            failure_type: Type of failure being prevented
            component_name: Component name
            prevention_type: Type of prevention ("redundancy", "backup", "monitoring", "maintenance")
            redundancy_level: Number of redundant components
            backup_frequency: Backup frequency
            
        Returns:
            Created FailurePreventionAction
        """
        action = FailurePreventionAction(
            action_id=action_id,
            action_name=action_name,
            failure_type=failure_type.value,
            component_name=component_name,
            prevention_type=prevention_type,
            redundancy_level=redundancy_level,
            backup_frequency=backup_frequency,
            active=True,
            last_verified_at=datetime.utcnow(),
            next_verification_due=datetime.utcnow() + timedelta(days=30),
        )
        
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(
            f"Failure prevention action created: {action_id}",
            extra={
                "action_id": action_id,
                "component_name": component_name,
                "failure_type": failure_type.value,
                "event_type": "failure_prevention.created",
            }
        )
        
        return action
    
    def record_failure_prevented(
        self,
        action_id: str,
    ) -> FailurePreventionAction:
        """
        Record that a failure was prevented.
        
        Args:
            action_id: Action identifier
            
        Returns:
            Updated FailurePreventionAction
        """
        action = self.db.query(FailurePreventionAction).filter(
            FailurePreventionAction.action_id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"Prevention action not found: {action_id}")
        
        action.failures_prevented += 1
        action.last_failure_prevented_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(
            f"Failure prevented recorded: {action_id}",
            extra={
                "action_id": action_id,
                "failures_prevented": action.failures_prevented,
                "event_type": "failure_prevention.recorded",
            }
        )
        
        return action
    
    def verify_prevention_action(
        self,
        action_id: str,
    ) -> FailurePreventionAction:
        """
        Verify a prevention action is still active and effective.
        
        Args:
            action_id: Action identifier
            
        Returns:
            Updated FailurePreventionAction
        """
        action = self.db.query(FailurePreventionAction).filter(
            FailurePreventionAction.action_id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"Prevention action not found: {action_id}")
        
        action.last_verified_at = datetime.utcnow()
        action.next_verification_due = datetime.utcnow() + timedelta(days=30)
        
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(
            f"Prevention action verified: {action_id}",
            extra={
                "action_id": action_id,
                "event_type": "failure_prevention.verified",
            }
        )
        
        return action
    
    def get_prevention_actions(
        self,
        failure_type: Optional[FailureType] = None,
        component_name: Optional[str] = None,
        active_only: bool = True,
    ) -> List[FailurePreventionAction]:
        """
        Get failure prevention actions.
        
        Args:
            failure_type: Filter by failure type
            component_name: Filter by component name
            active_only: Only return active actions
            
        Returns:
            List of FailurePreventionAction records
        """
        query = self.db.query(FailurePreventionAction)
        
        if failure_type:
            query = query.filter(FailurePreventionAction.failure_type == failure_type.value)
        
        if component_name:
            query = query.filter(FailurePreventionAction.component_name == component_name)
        
        if active_only:
            query = query.filter(FailurePreventionAction.active == True)
        
        return query.order_by(FailurePreventionAction.created_at.desc()).all()
    
    def get_prevention_summary(self) -> Dict:
        """
        Get summary of failure prevention actions.
        
        Returns:
            Dictionary with prevention statistics
        """
        total = self.db.query(FailurePreventionAction).filter(
            FailurePreventionAction.active == True
        ).count()
        
        by_failure_type = {}
        for failure_type in FailureType:
            count = self.db.query(FailurePreventionAction).filter(
                FailurePreventionAction.failure_type == failure_type.value,
                FailurePreventionAction.active == True,
            ).count()
            by_failure_type[failure_type.value] = count
        
        total_prevented = self.db.query(FailurePreventionAction).with_entities(
            func.sum(FailurePreventionAction.failures_prevented)
        ).scalar() or 0
        
        return {
            "total_active_actions": total,
            "by_failure_type": by_failure_type,
            "total_failures_prevented": total_prevented,
        }
