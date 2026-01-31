"""
AC-4: Information Flow Enforcement Service

Implements network segmentation rules, data flow policies, and cross-domain enforcement
for FedRAMP AC-4 compliance.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.access_control import (
    InformationFlowRule,
    InformationFlowLog,
    FlowDirection,
    FlowAction,
    NetworkSegment,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from utils.logger import logger


class InformationFlowService:
    """Service for managing information flow enforcement rules and logging"""
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_flow_rule(
        self,
        rule_name: str,
        source_segment: str,
        destination_segment: str,
        direction: str,
        action: str,
        description: Optional[str] = None,
        protocol: Optional[str] = None,
        port_range: Optional[str] = None,
        data_classification: Optional[str] = None,
        requires_encryption: bool = False,
        requires_authentication: bool = True,
        priority: int = 100,
        conditions: Optional[Dict[str, Any]] = None,
        action_parameters: Optional[Dict[str, Any]] = None,
    ) -> InformationFlowRule:
        """
        Create a new information flow rule.
        
        Args:
            rule_name: Name of the rule
            source_segment: Source network segment
            destination_segment: Destination network segment
            direction: Flow direction (inbound, outbound, bidirectional)
            action: Action to take (allow, deny, encrypt, log, quarantine)
            description: Optional description
            protocol: Optional protocol filter
            port_range: Optional port range filter
            data_classification: Data classification level
            requires_encryption: Whether encryption is required
            requires_authentication: Whether authentication is required
            priority: Rule priority (lower = higher priority)
            conditions: Additional conditions
            action_parameters: Action-specific parameters
        
        Returns:
            Created InformationFlowRule
        """
        rule = InformationFlowRule(
            org_id=self.org_id,
            rule_name=rule_name,
            description=description,
            priority=priority,
            source_segment=source_segment,
            destination_segment=destination_segment,
            direction=direction,
            protocol=protocol,
            port_range=port_range,
            data_classification=data_classification,
            requires_encryption=requires_encryption,
            requires_authentication=requires_authentication,
            action=action,
            action_parameters=action_parameters or {},
            conditions=conditions or {},
            is_active=True,
            created_by=self.user_id,
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        # Audit log
        self._audit_log(
            action="create_flow_rule",
            resource_type="information_flow_rule",
            resource_id=str(rule.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "rule_name": rule_name,
                "source_segment": source_segment,
                "destination_segment": destination_segment,
                "action": action,
            }
        )
        
        logger.info(f"Created information flow rule: {rule_name} (ID: {rule.id})")
        return rule
    
    def evaluate_flow(
        self,
        source_segment: str,
        destination_segment: str,
        direction: str,
        protocol: Optional[str] = None,
        port: Optional[int] = None,
        data_classification: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
        data_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an information flow request against active rules.
        
        Returns:
            Dict with 'allowed', 'action', 'rule_id', and other details
        """
        # Get active rules matching the flow, ordered by priority
        query = self.db.query(InformationFlowRule).filter(
            and_(
                InformationFlowRule.org_id == self.org_id,
                InformationFlowRule.is_active == True,
                or_(
                    InformationFlowRule.source_segment == source_segment,
                    InformationFlowRule.source_segment == "*",
                ),
                or_(
                    InformationFlowRule.destination_segment == destination_segment,
                    InformationFlowRule.destination_segment == "*",
                ),
                or_(
                    InformationFlowRule.direction == direction,
                    InformationFlowRule.direction == FlowDirection.BIDIRECTIONAL.value,
                ),
            )
        )
        
        # Apply protocol filter if specified
        if protocol:
            query = query.filter(
                or_(
                    InformationFlowRule.protocol == protocol,
                    InformationFlowRule.protocol.is_(None),
                )
            )
        
        # Apply port filter if specified
        if port and InformationFlowRule.port_range.isnot(None):
            # Simple port range matching (can be enhanced)
            pass
        
        rules = query.order_by(InformationFlowRule.priority.asc()).all()
        
        # Evaluate rules in priority order
        for rule in rules:
            # Check additional conditions
            if not self._check_conditions(rule.conditions, user_id=user_id):
                continue
            
            # Check data classification requirements
            if rule.data_classification and data_classification:
                if data_classification != rule.data_classification:
                    continue
            
            # Rule matches - apply action
            action_result = "allowed" if rule.action == FlowAction.ALLOW.value else "denied"
            
            # Log the flow
            flow_log = InformationFlowLog(
                org_id=self.org_id,
                rule_id=rule.id,
                timestamp=datetime.now(timezone.utc),
                source_segment=source_segment,
                destination_segment=destination_segment,
                source_ip=source_ip,
                destination_ip=destination_ip,
                protocol=protocol,
                port=port,
                action_taken=rule.action,
                action_result=action_result,
                user_id=user_id,
                session_id=session_id,
                data_size=data_size,
                data_classification=data_classification,
            )
            self.db.add(flow_log)
            self.db.commit()
            
            # Audit log
            self._audit_log(
                action="evaluate_flow",
                resource_type="information_flow",
                resource_id=str(flow_log.id),
                outcome=AuditOutcome.SUCCESS if rule.action == FlowAction.ALLOW.value else AuditOutcome.DENIED,
                metadata={
                    "source_segment": source_segment,
                    "destination_segment": destination_segment,
                    "action": rule.action,
                    "rule_id": rule.id,
                }
            )
            
            return {
                "allowed": rule.action == FlowAction.ALLOW.value,
                "action": rule.action,
                "rule_id": rule.id,
                "rule_name": rule.rule_name,
                "requires_encryption": rule.requires_encryption,
                "requires_authentication": rule.requires_authentication,
            }
        
        # No matching rule - default deny
        flow_log = InformationFlowLog(
            org_id=self.org_id,
            timestamp=datetime.now(timezone.utc),
            source_segment=source_segment,
            destination_segment=destination_segment,
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol=protocol,
            port=port,
            action_taken=FlowAction.DENY.value,
            action_result="denied_no_rule",
            user_id=user_id,
            session_id=session_id,
            data_size=data_size,
            data_classification=data_classification,
        )
        self.db.add(flow_log)
        self.db.commit()
        
        # Audit log
        self._audit_log(
            action="evaluate_flow",
            resource_type="information_flow",
            resource_id=str(flow_log.id),
            outcome=AuditOutcome.DENIED,
            metadata={
                "source_segment": source_segment,
                "destination_segment": destination_segment,
                "reason": "no_matching_rule",
            }
        )
        
        return {
            "allowed": False,
            "action": FlowAction.DENY.value,
            "rule_id": None,
            "reason": "no_matching_rule",
        }
    
    def get_active_rules(self) -> List[InformationFlowRule]:
        """Get all active information flow rules"""
        return self.db.query(InformationFlowRule).filter(
            and_(
                InformationFlowRule.org_id == self.org_id,
                InformationFlowRule.is_active == True,
            )
        ).order_by(InformationFlowRule.priority.asc()).all()
    
    def get_flow_logs(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        rule_id: Optional[int] = None,
        action_taken: Optional[str] = None,
    ) -> List[InformationFlowLog]:
        """Get information flow logs"""
        query = self.db.query(InformationFlowLog).filter(
            InformationFlowLog.org_id == self.org_id
        )
        
        if start_date:
            query = query.filter(InformationFlowLog.timestamp >= start_date)
        if end_date:
            query = query.filter(InformationFlowLog.timestamp <= end_date)
        if rule_id:
            query = query.filter(InformationFlowLog.rule_id == rule_id)
        if action_taken:
            query = query.filter(InformationFlowLog.action_taken == action_taken)
        
        return query.order_by(desc(InformationFlowLog.timestamp)).limit(limit).all()
    
    def approve_rule(self, rule_id: int, approved_by: int) -> InformationFlowRule:
        """Approve an information flow rule"""
        rule = self.db.query(InformationFlowRule).filter(
            and_(
                InformationFlowRule.id == rule_id,
                InformationFlowRule.org_id == self.org_id,
            )
        ).first()
        
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        
        rule.approved_by = approved_by
        rule.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)
        
        # Audit log
        self._audit_log(
            action="approve_flow_rule",
            resource_type="information_flow_rule",
            resource_id=str(rule_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"approved_by": approved_by}
        )
        
        return rule
    
    def deactivate_rule(self, rule_id: int, reason: Optional[str] = None) -> InformationFlowRule:
        """Deactivate an information flow rule"""
        rule = self.db.query(InformationFlowRule).filter(
            and_(
                InformationFlowRule.id == rule_id,
                InformationFlowRule.org_id == self.org_id,
            )
        ).first()
        
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        
        rule.is_active = False
        self.db.commit()
        self.db.refresh(rule)
        
        # Audit log
        self._audit_log(
            action="deactivate_flow_rule",
            resource_type="information_flow_rule",
            resource_id=str(rule_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"reason": reason}
        )
        
        return rule
    
    def _check_conditions(self, conditions: Optional[Dict[str, Any]], **context) -> bool:
        """Check if conditions are met"""
        if not conditions:
            return True
        
        # Implement condition checking logic
        # This is a simplified version - can be enhanced with more complex conditions
        return True
    
    def _audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: AuditOutcome,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create audit log entry"""
        audit = ComprehensiveAuditLog(
            org_id=self.org_id,
            user_id=self.user_id,
            event_type=AuditEventType.AUTHORIZATION.value,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome.value,
            metadata=metadata or {},
        )
        self.db.add(audit)
        self.db.commit()
