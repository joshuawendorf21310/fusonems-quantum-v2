"""
Fail-Safe Procedures Service for FedRAMP SI-17 Compliance

This service provides:
- Fail-safe procedure management
- Trigger condition monitoring
- Automated fail-safe actions

FedRAMP SI-17: Fail-Safe Procedures
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.system_integrity import (
    FailSafeProcedure,
    FailSafeStatus,
)
from utils.logger import logger


class FailSafeService:
    """
    Service for fail-safe procedures management.
    
    FedRAMP SI-17: Fail-Safe Procedures
    """
    
    def __init__(self, db: Session):
        """
        Initialize fail-safe service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_failsafe_procedure(
        self,
        procedure_id: str,
        procedure_name: str,
        trigger_type: str,
        trigger_conditions: Dict,
        action_type: str,
        action_description: str,
        component_name: Optional[str] = None,
        system_name: Optional[str] = None,
        action_script: Optional[str] = None,
        threshold_value: Optional[str] = None,
    ) -> FailSafeProcedure:
        """
        Create a fail-safe procedure.
        
        Args:
            procedure_id: Unique procedure identifier
            procedure_name: Procedure name
            trigger_type: Type of trigger ("failure", "error", "threshold", "manual")
            trigger_conditions: Conditions that trigger fail-safe (JSON dict)
            action_type: Type of action ("shutdown", "isolate", "rollback", "alert", "degrade")
            action_description: Description of action
            component_name: Component name
            system_name: System name
            action_script: Automated action script
            threshold_value: Threshold value for threshold-based triggers
            
        Returns:
            Created FailSafeProcedure
        """
        procedure = FailSafeProcedure(
            procedure_id=procedure_id,
            procedure_name=procedure_name,
            trigger_type=trigger_type,
            trigger_conditions=trigger_conditions,
            action_type=action_type,
            action_description=action_description,
            component_name=component_name,
            system_name=system_name,
            action_script=action_script,
            threshold_value=threshold_value,
            status=FailSafeStatus.ACTIVE.value,
            enabled=True,
        )
        
        self.db.add(procedure)
        self.db.commit()
        self.db.refresh(procedure)
        
        logger.info(
            f"Fail-safe procedure created: {procedure_id}",
            extra={
                "procedure_id": procedure_id,
                "procedure_name": procedure_name,
                "trigger_type": trigger_type,
                "action_type": action_type,
                "event_type": "failsafe.created",
            }
        )
        
        return procedure
    
    def trigger_failsafe(
        self,
        procedure_id: str,
        trigger_reason: Optional[str] = None,
    ) -> FailSafeProcedure:
        """
        Trigger a fail-safe procedure.
        
        Args:
            procedure_id: Procedure identifier
            trigger_reason: Reason for trigger
            
        Returns:
            Updated FailSafeProcedure
        """
        procedure = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.procedure_id == procedure_id
        ).first()
        
        if not procedure:
            raise ValueError(f"Fail-safe procedure not found: {procedure_id}")
        
        if not procedure.enabled:
            logger.warning(f"Fail-safe procedure {procedure_id} is disabled")
            return procedure
        
        procedure.status = FailSafeStatus.TRIGGERED.value
        procedure.times_triggered += 1
        procedure.last_triggered_at = datetime.utcnow()
        
        # Execute action
        try:
            action_successful = self._execute_failsafe_action(procedure)
            procedure.action_successful = action_successful
        except Exception as e:
            logger.error(f"Fail-safe action execution failed: {e}", exc_info=True)
            procedure.action_successful = False
        
        self.db.commit()
        self.db.refresh(procedure)
        
        logger.warning(
            f"Fail-safe procedure triggered: {procedure_id}",
            extra={
                "procedure_id": procedure_id,
                "action_type": procedure.action_type,
                "action_successful": procedure.action_successful,
                "trigger_reason": trigger_reason,
                "event_type": "failsafe.triggered",
            }
        )
        
        return procedure
    
    def resolve_failsafe(
        self,
        procedure_id: str,
    ) -> FailSafeProcedure:
        """
        Resolve a triggered fail-safe procedure.
        
        Args:
            procedure_id: Procedure identifier
            
        Returns:
            Updated FailSafeProcedure
        """
        procedure = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.procedure_id == procedure_id
        ).first()
        
        if not procedure:
            raise ValueError(f"Fail-safe procedure not found: {procedure_id}")
        
        procedure.status = FailSafeStatus.RESOLVED.value
        procedure.last_resolved_at = datetime.utcnow()
        
        if procedure.last_triggered_at:
            resolution_time = (
                procedure.last_resolved_at - procedure.last_triggered_at
            ).total_seconds()
            procedure.resolution_time_seconds = int(resolution_time)
        
        self.db.commit()
        self.db.refresh(procedure)
        
        logger.info(
            f"Fail-safe procedure resolved: {procedure_id}",
            extra={
                "procedure_id": procedure_id,
                "resolution_time_seconds": procedure.resolution_time_seconds,
                "event_type": "failsafe.resolved",
            }
        )
        
        return procedure
    
    def enable_failsafe(
        self,
        procedure_id: str,
    ) -> FailSafeProcedure:
        """
        Enable a fail-safe procedure.
        
        Args:
            procedure_id: Procedure identifier
            
        Returns:
            Updated FailSafeProcedure
        """
        procedure = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.procedure_id == procedure_id
        ).first()
        
        if not procedure:
            raise ValueError(f"Fail-safe procedure not found: {procedure_id}")
        
        procedure.enabled = True
        procedure.status = FailSafeStatus.ACTIVE.value
        
        self.db.commit()
        self.db.refresh(procedure)
        
        return procedure
    
    def disable_failsafe(
        self,
        procedure_id: str,
    ) -> FailSafeProcedure:
        """
        Disable a fail-safe procedure.
        
        Args:
            procedure_id: Procedure identifier
            
        Returns:
            Updated FailSafeProcedure
        """
        procedure = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.procedure_id == procedure_id
        ).first()
        
        if not procedure:
            raise ValueError(f"Fail-safe procedure not found: {procedure_id}")
        
        procedure.enabled = False
        procedure.status = FailSafeStatus.DISABLED.value
        
        self.db.commit()
        self.db.refresh(procedure)
        
        logger.warning(
            f"Fail-safe procedure disabled: {procedure_id}",
            extra={
                "procedure_id": procedure_id,
                "event_type": "failsafe.disabled",
            }
        )
        
        return procedure
    
    def get_failsafe_procedures(
        self,
        status: Optional[FailSafeStatus] = None,
        enabled: Optional[bool] = None,
        component_name: Optional[str] = None,
    ) -> List[FailSafeProcedure]:
        """
        Get fail-safe procedures.
        
        Args:
            status: Filter by status
            enabled: Filter by enabled status
            component_name: Filter by component name
            
        Returns:
            List of FailSafeProcedure records
        """
        query = self.db.query(FailSafeProcedure)
        
        if status:
            query = query.filter(FailSafeProcedure.status == status.value)
        
        if enabled is not None:
            query = query.filter(FailSafeProcedure.enabled == enabled)
        
        if component_name:
            query = query.filter(FailSafeProcedure.component_name == component_name)
        
        return query.order_by(FailSafeProcedure.created_at.desc()).all()
    
    def get_failsafe_summary(self) -> Dict:
        """
        Get summary of fail-safe procedures.
        
        Returns:
            Dictionary with fail-safe statistics
        """
        total = self.db.query(FailSafeProcedure).count()
        active = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.status == FailSafeStatus.ACTIVE.value
        ).count()
        triggered = self.db.query(FailSafeProcedure).filter(
            FailSafeProcedure.status == FailSafeStatus.TRIGGERED.value
        ).count()
        
        total_triggered = self.db.query(FailSafeProcedure).with_entities(
            func.sum(FailSafeProcedure.times_triggered)
        ).scalar() or 0
        
        return {
            "total_procedures": total,
            "active_procedures": active,
            "triggered_procedures": triggered,
            "total_times_triggered": total_triggered,
        }
    
    def _execute_failsafe_action(self, procedure: FailSafeProcedure) -> bool:
        """
        Execute fail-safe action.
        
        Args:
            procedure: Fail-safe procedure
            
        Returns:
            True if action successful
        """
        # This is a placeholder - in production, this would:
        # 1. Execute the action_script if provided
        # 2. Perform action based on action_type
        # 3. Log the action
        # 4. Return success/failure
        
        logger.info(
            f"Executing fail-safe action: {procedure.action_type}",
            extra={
                "procedure_id": procedure.procedure_id,
                "action_type": procedure.action_type,
            }
        )
        
        # For now, assume success
        return True
