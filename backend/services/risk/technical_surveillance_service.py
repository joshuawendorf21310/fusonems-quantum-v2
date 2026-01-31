"""
Technical Surveillance Countermeasures Service for FedRAMP RA-6 Compliance

This service provides:
- Surveillance detection
- Counter-surveillance measures
- Physical security monitoring
- Surveillance event tracking
- Response coordination

FedRAMP RA-6: Technical surveillance countermeasures.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.risk_assessment import (
    SurveillanceEvent,
    SurveillanceType,
    SurveillanceStatus,
    CountermeasureType,
)
from utils.logger import logger


class TechnicalSurveillanceService:
    """
    Service for managing technical surveillance countermeasures per FedRAMP RA-6.
    
    Provides capabilities for:
    - Detecting surveillance activities
    - Tracking surveillance events
    - Coordinating counter-surveillance measures
    - Monitoring physical security
    - Response planning and execution
    """
    
    def __init__(self, db: Session):
        """
        Initialize technical surveillance service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_surveillance_event(
        self,
        event_name: str,
        surveillance_type: SurveillanceType,
        detected_by: Optional[str] = None,
        detection_method: Optional[str] = None,
        detection_source: Optional[str] = None,
        event_description: Optional[str] = None,
        location: Optional[str] = None,
        affected_systems: Optional[List[str]] = None,
        affected_data: Optional[List[str]] = None,
        threat_source: Optional[str] = None,
        threat_capability: Optional[str] = None,
        threat_intent: Optional[str] = None,
        potential_impact: Optional[str] = None,
    ) -> SurveillanceEvent:
        """
        Create a new surveillance detection event.
        
        Args:
            event_name: Name of the event
            surveillance_type: Type of surveillance detected
            detected_by: Who or what detected the surveillance
            detection_method: Method used to detect
            detection_source: Source of detection
            event_description: Description of the event
            location: Location where surveillance was detected
            affected_systems: List of affected system IDs
            affected_data: List of affected data types
            threat_source: Source of the threat
            threat_capability: Capability level of threat
            threat_intent: Intent of the threat
            potential_impact: Description of potential impact
            
        Returns:
            Created SurveillanceEvent record
        """
        event = SurveillanceEvent(
            event_name=event_name,
            event_description=event_description,
            surveillance_type=surveillance_type.value,
            detected_by=detected_by,
            detection_method=detection_method,
            detection_source=detection_source,
            location=location,
            affected_systems=affected_systems,
            affected_data=affected_data,
            threat_source=threat_source,
            threat_capability=threat_capability,
            threat_intent=threat_intent,
            potential_impact=potential_impact,
            status=SurveillanceStatus.DETECTED.value,
            detected_at=datetime.utcnow(),
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        logger.warning(
            f"Surveillance event detected: {event_name}",
            extra={
                "surveillance_event_id": event.id,
                "surveillance_type": surveillance_type.value,
                "detected_by": detected_by,
                "event_type": "surveillance.event.detected",
            }
        )
        
        return event
    
    def update_surveillance_event(
        self,
        event_id: int,
        status: Optional[SurveillanceStatus] = None,
        investigation_notes: Optional[str] = None,
        investigated_by: Optional[str] = None,
        response_actions: Optional[List[str]] = None,
        countermeasures_applied: Optional[List[str]] = None,
        data_exposed: Optional[bool] = None,
        systems_compromised: Optional[bool] = None,
        impact_level: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[str] = None,
    ) -> Optional[SurveillanceEvent]:
        """
        Update a surveillance event.
        
        Args:
            event_id: ID of the event
            status: New status
            investigation_notes: Investigation notes
            investigated_by: Person investigating
            response_actions: List of response actions taken
            countermeasures_applied: List of countermeasures applied
            data_exposed: Whether data was exposed
            systems_compromised: Whether systems were compromised
            impact_level: Impact level
            resolution_notes: Resolution notes
            resolved_by: Person who resolved
            
        Returns:
            Updated SurveillanceEvent or None if not found
        """
        event = self.db.query(SurveillanceEvent).filter(
            SurveillanceEvent.id == event_id
        ).first()
        
        if not event:
            return None
        
        if status:
            event.status = status.value
            
            # Update timestamps based on status
            if status == SurveillanceStatus.INVESTIGATING:
                if not event.investigated_by:
                    event.investigated_by = investigated_by
            elif status == SurveillanceStatus.RESOLVED:
                event.resolved_at = datetime.utcnow()
                event.resolved_by = resolved_by or investigated_by
            elif status == SurveillanceStatus.MITIGATED:
                event.resolved_at = datetime.utcnow()
        
        if investigation_notes is not None:
            event.investigation_notes = investigation_notes
        if investigated_by:
            event.investigated_by = investigated_by
        if response_actions is not None:
            event.response_actions = response_actions
        if countermeasures_applied is not None:
            event.countermeasures_applied = countermeasures_applied
        if data_exposed is not None:
            event.data_exposed = data_exposed
        if systems_compromised is not None:
            event.systems_compromised = systems_compromised
        if impact_level is not None:
            event.impact_level = impact_level
        if resolution_notes is not None:
            event.resolution_notes = resolution_notes
        
        if status == SurveillanceStatus.RESOLVED or status == SurveillanceStatus.MITIGATED:
            event.investigation_completed_at = datetime.utcnow()
        
        event.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(
            f"Updated surveillance event: {event.event_name}",
            extra={
                "surveillance_event_id": event.id,
                "status": event.status,
                "event_type": "surveillance.event.updated",
            }
        )
        
        return event
    
    def add_response_action(
        self,
        event_id: int,
        action: str
    ) -> Optional[SurveillanceEvent]:
        """
        Add a response action to a surveillance event.
        
        Args:
            event_id: ID of the event
            action: Response action taken
            
        Returns:
            Updated SurveillanceEvent or None if not found
        """
        event = self.db.query(SurveillanceEvent).filter(
            SurveillanceEvent.id == event_id
        ).first()
        
        if not event:
            return None
        
        current_actions = event.response_actions or []
        if action not in current_actions:
            current_actions.append(action)
            event.response_actions = current_actions
            event.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(event)
        
        return event
    
    def add_countermeasure(
        self,
        event_id: int,
        countermeasure: str
    ) -> Optional[SurveillanceEvent]:
        """
        Add a countermeasure to a surveillance event.
        
        Args:
            event_id: ID of the event
            countermeasure: Countermeasure applied
            
        Returns:
            Updated SurveillanceEvent or None if not found
        """
        event = self.db.query(SurveillanceEvent).filter(
            SurveillanceEvent.id == event_id
        ).first()
        
        if not event:
            return None
        
        current_countermeasures = event.countermeasures_applied or []
        if countermeasure not in current_countermeasures:
            current_countermeasures.append(countermeasure)
            event.countermeasures_applied = current_countermeasures
            event.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(event)
        
        return event
    
    def get_surveillance_event(self, event_id: int) -> Optional[SurveillanceEvent]:
        """
        Get surveillance event by ID.
        
        Args:
            event_id: ID of the event
            
        Returns:
            SurveillanceEvent or None if not found
        """
        return self.db.query(SurveillanceEvent).filter(
            SurveillanceEvent.id == event_id
        ).first()
    
    def list_surveillance_events(
        self,
        status: Optional[str] = None,
        surveillance_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[SurveillanceEvent], int]:
        """
        List surveillance events with filters.
        
        Args:
            status: Filter by status
            surveillance_type: Filter by surveillance type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (events list, total count)
        """
        query = self.db.query(SurveillanceEvent)
        
        if status:
            query = query.filter(SurveillanceEvent.status == status)
        
        if surveillance_type:
            query = query.filter(SurveillanceEvent.surveillance_type == surveillance_type)
        
        if start_date:
            query = query.filter(SurveillanceEvent.detected_at >= start_date)
        
        if end_date:
            query = query.filter(SurveillanceEvent.detected_at <= end_date)
        
        total = query.count()
        events = query.order_by(
            SurveillanceEvent.detected_at.desc()
        ).offset(offset).limit(limit).all()
        
        return events, total
    
    def get_active_surveillance_events(self) -> List[SurveillanceEvent]:
        """
        Get all active (non-resolved) surveillance events.
        
        Returns:
            List of active SurveillanceEvent records
        """
        active_statuses = [
            SurveillanceStatus.DETECTED.value,
            SurveillanceStatus.INVESTIGATING.value,
            SurveillanceStatus.CONFIRMED.value,
        ]
        
        return self.db.query(SurveillanceEvent).filter(
            SurveillanceEvent.status.in_(active_statuses)
        ).order_by(SurveillanceEvent.detected_at.desc()).all()
    
    def mark_as_false_positive(
        self,
        event_id: int,
        notes: Optional[str] = None,
        resolved_by: Optional[str] = None
    ) -> Optional[SurveillanceEvent]:
        """
        Mark a surveillance event as false positive.
        
        Args:
            event_id: ID of the event
            notes: Notes about false positive determination
            resolved_by: Person who determined false positive
            
        Returns:
            Updated SurveillanceEvent or None if not found
        """
        return self.update_surveillance_event(
            event_id=event_id,
            status=SurveillanceStatus.FALSE_POSITIVE,
            resolution_notes=notes,
            resolved_by=resolved_by
        )
    
    def resolve_event(
        self,
        event_id: int,
        resolution_notes: str,
        resolved_by: str,
        countermeasures_applied: Optional[List[str]] = None
    ) -> Optional[SurveillanceEvent]:
        """
        Resolve a surveillance event.
        
        Args:
            event_id: ID of the event
            resolution_notes: Notes about resolution
            resolved_by: Person who resolved
            countermeasures_applied: List of countermeasures applied
            
        Returns:
            Updated SurveillanceEvent or None if not found
        """
        return self.update_surveillance_event(
            event_id=event_id,
            status=SurveillanceStatus.RESOLVED,
            resolution_notes=resolution_notes,
            resolved_by=resolved_by,
            countermeasures_applied=countermeasures_applied
        )
    
    def generate_surveillance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate surveillance activity report.
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            Dictionary with surveillance report data
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        events, total = self.list_surveillance_events(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        # Count by status
        by_status = {}
        for event in events:
            status = event.status
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by type
        by_type = {}
        for event in events:
            event_type = event.surveillance_type
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        # Count by impact
        data_exposed_count = sum(1 for e in events if e.data_exposed)
        systems_compromised_count = sum(1 for e in events if e.systems_compromised)
        
        # Active events
        active_events = [e for e in events if e.status not in [
            SurveillanceStatus.RESOLVED.value,
            SurveillanceStatus.FALSE_POSITIVE.value,
            SurveillanceStatus.MITIGATED.value
        ]]
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_events": total,
            "by_status": by_status,
            "by_type": by_type,
            "data_exposed_events": data_exposed_count,
            "systems_compromised_events": systems_compromised_count,
            "active_events": len(active_events),
            "compliance_status": "compliant" if len(active_events) == 0 else "needs_attention",
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def generate_compliance_report(self) -> Dict:
        """
        Generate FedRAMP RA-6 compliance report.
        
        Returns:
            Dictionary with compliance report data
        """
        # Get all events
        events, total = self.list_surveillance_events(limit=1000)
        
        # Get active events
        active_events = self.get_active_surveillance_events()
        
        # Count by type
        by_type = {}
        for event_type in SurveillanceType:
            count = sum(1 for e in events if e.surveillance_type == event_type.value)
            by_type[event_type.value] = count
        
        # Count by status
        by_status = {}
        for status in SurveillanceStatus:
            count = sum(1 for e in events if e.status == status.value)
            by_status[status.value] = count
        
        # Response metrics
        events_with_response = sum(
            1 for e in events
            if e.response_actions and len(e.response_actions) > 0
        )
        events_with_countermeasures = sum(
            1 for e in events
            if e.countermeasures_applied and len(e.countermeasures_applied) > 0
        )
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "total_events": total,
            "active_events": len(active_events),
            "by_type": by_type,
            "by_status": by_status,
            "events_with_response": events_with_response,
            "events_with_countermeasures": events_with_countermeasures,
            "response_rate": events_with_response / total if total > 0 else 0.0,
            "countermeasure_rate": events_with_countermeasures / total if total > 0 else 0.0,
            "compliance_status": "compliant" if len(active_events) == 0 else "needs_attention",
        }
