"""
Incident Management Service for FedRAMP IR-4, IR-5, IR-6 Compliance

Provides core incident management functionality:
- Create and classify incidents
- Assign to responders
- Track investigation progress
- Generate incident reports
- US-CERT notification handling
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.logger import logger
from models.incident import (
    SecurityIncident,
    IncidentActivity,
    IncidentTimeline,
    IncidentSeverity,
    IncidentStatus,
    IncidentCategory,
)
from models.user import User
from utils.audit import record_audit


class IncidentService:
    """Service for managing security incidents per FedRAMP IR-4, IR-5, IR-6 requirements"""

    @staticmethod
    def generate_incident_number(org_id: int) -> str:
        """Generate unique incident number"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        # In production, use a sequence or counter for uniqueness
        random_part = str(uuid4())[:8].upper()
        return f"INC-{org_id}-{timestamp}-{random_part}"

    @staticmethod
    def create_incident(
        db: Session,
        org_id: int,
        title: str,
        description: str,
        severity: IncidentSeverity,
        category: IncidentCategory,
        detected_by_user_id: Optional[int] = None,
        detected_by_system: bool = False,
        detection_method: Optional[str] = None,
        affected_systems: Optional[List[str]] = None,
        affected_users: Optional[List[int]] = None,
        affected_resources: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        classification: Optional[str] = None,
        training_mode: bool = False,
        request=None,
    ) -> SecurityIncident:
        """
        Create a new security incident.
        
        Returns the created incident with initial timeline entry.
        """
        incident_number = IncidentService.generate_incident_number(org_id)
        
        incident = SecurityIncident(
            org_id=org_id,
            incident_number=incident_number,
            title=title,
            description=description,
            severity=severity.value,
            category=category.value,
            status=IncidentStatus.NEW.value,
            detected_at=datetime.now(timezone.utc),
            detected_by_user_id=detected_by_user_id,
            detected_by_system=detected_by_system,
            detection_method=detection_method,
            affected_systems=affected_systems or [],
            affected_users=affected_users or [],
            affected_resources=affected_resources or [],
            tags=tags or [],
            metadata=metadata or {},
            classification=classification,
            training_mode=training_mode,
        )
        
        db.add(incident)
        db.flush()
        
        # Create initial timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=incident.detected_at,
            event_type="detected",
            event_description=f"Incident detected: {title}",
            source="system" if detected_by_system else "user",
            source_id=str(detected_by_user_id) if detected_by_user_id else None,
        )
        db.add(timeline_entry)
        
        # Create initial activity log
        activity = IncidentActivity(
            incident_id=incident.id,
            activity_type="created",
            description=f"Incident created: {title}",
            user_id=detected_by_user_id,
            user_email=db.query(User).filter(User.id == detected_by_user_id).first().email if detected_by_user_id else None,
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        db.add(activity)
        
        db.commit()
        db.refresh(incident)
        
        # Audit log
        if request and detected_by_user_id:
            try:
                user = db.query(User).filter(User.id == detected_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_created",
                        resource=f"security_incident:{incident.id}",
                        outcome="Success",
                        classification=classification or "NON_PHI",
                        reason_code="INCIDENT_CREATED",
                        after_state={
                            "incident_number": incident_number,
                            "severity": severity.value,
                            "category": category.value,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for incident creation: {e}", exc_info=True)
        
        logger.info(
            f"Security incident created: {incident_number}, "
            f"severity={severity.value}, category={category.value}"
        )
        
        return incident

    @staticmethod
    def update_incident_status(
        db: Session,
        incident_id: UUID,
        new_status: IncidentStatus,
        user_id: int,
        comment: Optional[str] = None,
        request=None,
    ) -> SecurityIncident:
        """
        Update incident status and record activity.
        
        Automatically sets timestamps (contained_at, resolved_at, closed_at)
        based on status transitions.
        """
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        old_status = incident.status
        incident.status = new_status.value
        incident.updated_at = datetime.now(timezone.utc)
        
        # Set status-specific timestamps
        now = datetime.now(timezone.utc)
        if new_status == IncidentStatus.CONTAINED and not incident.contained_at:
            incident.contained_at = now
        elif new_status == IncidentStatus.RESOLVED and not incident.resolved_at:
            incident.resolved_at = now
        elif new_status == IncidentStatus.CLOSED and not incident.closed_at:
            incident.closed_at = now
        
        db.flush()
        
        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=now,
            event_type=f"status_{new_status.value}",
            event_description=f"Status changed from {old_status} to {new_status.value}" + (f": {comment}" if comment else ""),
            source="user",
            source_id=str(user_id),
        )
        db.add(timeline_entry)
        
        # Create activity log
        user = db.query(User).filter(User.id == user_id).first()
        activity = IncidentActivity(
            incident_id=incident.id,
            activity_type="status_change",
            description=f"Status changed from {old_status} to {new_status.value}" + (f": {comment}" if comment else ""),
            user_id=user_id,
            user_email=user.email if user else None,
            old_value=old_status,
            new_value=new_status.value,
            details={"comment": comment} if comment else None,
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        db.add(activity)
        
        db.commit()
        db.refresh(incident)
        
        # Audit log
        if request:
            try:
                record_audit(
                    db=db,
                    request=request,
                    user=user,
                    action="incident_status_update",
                    resource=f"security_incident:{incident.id}",
                    outcome="Success",
                    classification=incident.classification or "NON_PHI",
                    reason_code="STATUS_UPDATE",
                    before_state={"status": old_status},
                    after_state={"status": new_status.value},
                )
            except Exception as e:
                logger.error(f"Failed to record audit for status update: {e}", exc_info=True)
        
        logger.info(
            f"Incident status updated: {incident.incident_number}, "
            f"{old_status} -> {new_status.value}"
        )
        
        return incident

    @staticmethod
    def classify_incident(
        db: Session,
        incident_id: UUID,
        severity: IncidentSeverity,
        user_id: int,
        reason: Optional[str] = None,
        request=None,
    ) -> SecurityIncident:
        """Update incident severity classification"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        old_severity = incident.severity
        incident.severity = severity.value
        incident.updated_at = datetime.now(timezone.utc)
        
        db.flush()
        
        # Create activity log
        user = db.query(User).filter(User.id == user_id).first()
        activity = IncidentActivity(
            incident_id=incident.id,
            activity_type="classification",
            description=f"Severity classified as {severity.value}" + (f": {reason}" if reason else ""),
            user_id=user_id,
            user_email=user.email if user else None,
            old_value=old_severity,
            new_value=severity.value,
            details={"reason": reason} if reason else None,
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        db.add(activity)
        
        db.commit()
        db.refresh(incident)
        
        # Check if US-CERT reporting is required (IR-6)
        if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            logger.warning(
                f"High/Critical severity incident requires US-CERT reporting: {incident.incident_number}"
            )
        
        return incident

    @staticmethod
    def assign_incident(
        db: Session,
        incident_id: UUID,
        assigned_to_user_id: int,
        assigned_by_user_id: int,
        request=None,
    ) -> SecurityIncident:
        """Assign incident to a responder"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        old_assigned_to = incident.assigned_to_user_id
        incident.assigned_to_user_id = assigned_to_user_id
        incident.assigned_at = datetime.now(timezone.utc)
        incident.updated_at = datetime.now(timezone.utc)
        
        db.flush()
        
        # Create activity log
        assigned_by_user = db.query(User).filter(User.id == assigned_by_user_id).first()
        assigned_to_user = db.query(User).filter(User.id == assigned_to_user_id).first()
        activity = IncidentActivity(
            incident_id=incident.id,
            activity_type="assignment",
            description=f"Assigned to {assigned_to_user.email if assigned_to_user else 'unknown'}",
            user_id=assigned_by_user_id,
            user_email=assigned_by_user.email if assigned_by_user else None,
            old_value=str(old_assigned_to) if old_assigned_to else None,
            new_value=str(assigned_to_user_id),
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        db.add(activity)
        
        db.commit()
        db.refresh(incident)
        
        return incident

    @staticmethod
    def add_activity(
        db: Session,
        incident_id: UUID,
        activity_type: str,
        description: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        request=None,
    ) -> IncidentActivity:
        """Add activity log entry to incident"""
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        
        activity = IncidentActivity(
            incident_id=incident_id,
            activity_type=activity_type,
            description=description,
            user_id=user_id,
            user_email=user.email if user else None,
            details=details,
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return activity

    @staticmethod
    def update_investigation_details(
        db: Session,
        incident_id: UUID,
        user_id: int,
        root_cause: Optional[str] = None,
        impact_assessment: Optional[str] = None,
        containment_actions: Optional[str] = None,
        remediation_actions: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        request=None,
    ) -> SecurityIncident:
        """Update investigation details"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        if root_cause is not None:
            incident.root_cause = root_cause
        if impact_assessment is not None:
            incident.impact_assessment = impact_assessment
        if containment_actions is not None:
            incident.containment_actions = containment_actions
        if remediation_actions is not None:
            incident.remediation_actions = remediation_actions
        if lessons_learned is not None:
            incident.lessons_learned = lessons_learned
        
        incident.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(incident)
        
        # Create activity log
        IncidentService.add_activity(
            db=db,
            incident_id=incident_id,
            activity_type="investigation_update",
            description="Investigation details updated",
            user_id=user_id,
            request=request,
        )
        
        return incident

    @staticmethod
    def report_to_us_cert(
        db: Session,
        incident_id: UUID,
        user_id: int,
        report_id: Optional[str] = None,
        request=None,
    ) -> SecurityIncident:
        """
        Mark incident as reported to US-CERT (IR-6 requirement).
        
        Note: This is a placeholder. Actual US-CERT reporting integration
        should be implemented per organizational requirements.
        """
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        incident.us_cert_reported = True
        incident.us_cert_reported_at = datetime.now(timezone.utc)
        if report_id:
            incident.us_cert_report_id = report_id
        incident.updated_at = datetime.now(timezone.utc)
        
        db.flush()
        
        # Create activity log
        user = db.query(User).filter(User.id == user_id).first()
        activity = IncidentActivity(
            incident_id=incident.id,
            activity_type="us_cert_report",
            description=f"Reported to US-CERT" + (f" (Report ID: {report_id})" if report_id else ""),
            user_id=user_id,
            user_email=user.email if user else None,
            details={"report_id": report_id} if report_id else None,
        )
        if request:
            if request.client:
                activity.ip_address = request.client.host
            activity.user_agent = request.headers.get("user-agent")
        db.add(activity)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(
            f"Incident reported to US-CERT: {incident.incident_number}, "
            f"report_id={report_id}"
        )
        
        return incident

    @staticmethod
    def get_incident(
        db: Session,
        incident_id: UUID,
        org_id: Optional[int] = None,
    ) -> Optional[SecurityIncident]:
        """Get incident by ID"""
        query = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id)
        if org_id:
            query = query.filter(SecurityIncident.org_id == org_id)
        return query.first()

    @staticmethod
    def list_incidents(
        db: Session,
        org_id: int,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        category: Optional[IncidentCategory] = None,
        assigned_to_user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityIncident]:
        """List incidents with filters"""
        query = db.query(SecurityIncident).filter(SecurityIncident.org_id == org_id)
        
        if status:
            query = query.filter(SecurityIncident.status == status.value)
        if severity:
            query = query.filter(SecurityIncident.severity == severity.value)
        if category:
            query = query.filter(SecurityIncident.category == category.value)
        if assigned_to_user_id:
            query = query.filter(SecurityIncident.assigned_to_user_id == assigned_to_user_id)
        
        return query.order_by(desc(SecurityIncident.created_at)).limit(limit).offset(offset).all()

    @staticmethod
    def generate_incident_report(
        db: Session,
        incident_id: UUID,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive incident report for compliance.
        
        Returns a dictionary with all incident details, timeline, and activities.
        """
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # Get timeline entries
        timeline = (
            db.query(IncidentTimeline)
            .filter(IncidentTimeline.incident_id == incident_id)
            .order_by(IncidentTimeline.event_time)
            .all()
        )
        
        # Get activity log
        activities = (
            db.query(IncidentActivity)
            .filter(IncidentActivity.incident_id == incident_id)
            .order_by(IncidentActivity.timestamp)
            .all()
        )
        
        return {
            "incident": {
                "id": str(incident.id),
                "incident_number": incident.incident_number,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "category": incident.category,
                "status": incident.status,
                "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
                "contained_at": incident.contained_at.isoformat() if incident.contained_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "closed_at": incident.closed_at.isoformat() if incident.closed_at else None,
                "affected_systems": incident.affected_systems,
                "affected_users": incident.affected_users,
                "affected_resources": incident.affected_resources,
                "root_cause": incident.root_cause,
                "impact_assessment": incident.impact_assessment,
                "containment_actions": incident.containment_actions,
                "remediation_actions": incident.remediation_actions,
                "lessons_learned": incident.lessons_learned,
                "us_cert_reported": incident.us_cert_reported,
                "us_cert_reported_at": incident.us_cert_reported_at.isoformat() if incident.us_cert_reported_at else None,
                "us_cert_report_id": incident.us_cert_report_id,
            },
            "timeline": [
                {
                    "event_time": entry.event_time.isoformat(),
                    "event_type": entry.event_type,
                    "event_description": entry.event_description,
                    "source": entry.source,
                }
                for entry in timeline
            ],
            "activities": [
                {
                    "timestamp": activity.timestamp.isoformat(),
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "user_email": activity.user_email,
                    "old_value": activity.old_value,
                    "new_value": activity.new_value,
                }
                for activity in activities
            ],
        }

    # ============================================================================
    # IR-4(1): Automated Incident Handling
    # ============================================================================

    @staticmethod
    def enable_automated_handling(
        db: Session,
        incident_id: UUID,
        automation_workflow_id: Optional[str] = None,
        user_id: Optional[int] = None,
        request=None,
    ) -> SecurityIncident:
        """Enable automated incident handling (IR-4(1))"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        incident.automated_handling_enabled = True
        if automation_workflow_id:
            incident.automation_workflow_id = automation_workflow_id
        
        incident.updated_at = datetime.now(timezone.utc)
        
        # Record automated action
        automated_actions = incident.automated_actions_taken or []
        automated_actions.append({
            "action": "automated_handling_enabled",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_id": automation_workflow_id,
        })
        incident.automated_actions_taken = automated_actions
        
        db.commit()
        db.refresh(incident)
        
        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=datetime.now(timezone.utc),
            event_type="automation_enabled",
            event_description="Automated incident handling enabled",
            source="system",
            source_id=automation_workflow_id,
        )
        db.add(timeline_entry)
        db.commit()
        
        logger.info(f"Automated handling enabled: incident_id={incident_id}, workflow={automation_workflow_id}")
        return incident

    @staticmethod
    def execute_automated_action(
        db: Session,
        incident_id: UUID,
        action_type: str,
        action_details: Dict[str, Any],
        workflow_id: Optional[str] = None,
    ) -> SecurityIncident:
        """Execute an automated action on an incident"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        if not incident.automated_handling_enabled:
            raise ValueError("Automated handling not enabled for this incident")
        
        # Record automated action
        automated_actions = incident.automated_actions_taken or []
        automated_actions.append({
            "action": action_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": action_details,
            "workflow_id": workflow_id or incident.automation_workflow_id,
        })
        incident.automated_actions_taken = automated_actions
        incident.updated_at = datetime.now(timezone.utc)
        
        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=datetime.now(timezone.utc),
            event_type=f"automated_{action_type}",
            event_description=f"Automated action executed: {action_type}",
            source="system",
            source_id=workflow_id or incident.automation_workflow_id,
            metadata=action_details,
        )
        db.add(timeline_entry)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Automated action executed: incident_id={incident_id}, action={action_type}")
        return incident

    # ============================================================================
    # IR-5(1): Automated Tracking / Data Collection / Analysis
    # ============================================================================

    @staticmethod
    def collect_incident_data(
        db: Session,
        incident_id: UUID,
        collected_data: Dict[str, Any],
        collection_source: Optional[str] = None,
    ) -> SecurityIncident:
        """Collect and store incident data automatically (IR-5(1))"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # Merge with existing collected data
        existing_data = incident.collected_data or {}
        existing_data.update(collected_data)
        if collection_source:
            existing_data["_collection_sources"] = existing_data.get("_collection_sources", [])
            if collection_source not in existing_data["_collection_sources"]:
                existing_data["_collection_sources"].append(collection_source)
        
        incident.collected_data = existing_data
        incident.data_collection_timestamp = datetime.now(timezone.utc)
        incident.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Incident data collected: incident_id={incident_id}, source={collection_source}")
        return incident

    @staticmethod
    def analyze_incident_data(
        db: Session,
        incident_id: UUID,
        analysis_results: Dict[str, Any],
        analysis_type: Optional[str] = None,
    ) -> SecurityIncident:
        """Perform automated analysis on incident data (IR-5(1))"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # Merge with existing analysis results
        existing_analysis = incident.analysis_results or {}
        if analysis_type:
            existing_analysis[analysis_type] = analysis_results
        else:
            existing_analysis.update(analysis_results)
        
        incident.analysis_results = existing_analysis
        incident.analysis_timestamp = datetime.now(timezone.utc)
        incident.updated_at = datetime.now(timezone.utc)
        
        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=datetime.now(timezone.utc),
            event_type="automated_analysis",
            event_description=f"Automated analysis completed: {analysis_type or 'general'}",
            source="system",
            metadata={"analysis_type": analysis_type, "results_summary": str(analysis_results)[:200]},
        )
        db.add(timeline_entry)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Incident data analyzed: incident_id={incident_id}, type={analysis_type}")
        return incident

    @staticmethod
    def correlate_incidents(
        db: Session,
        incident_id: UUID,
        related_incident_ids: List[UUID],
        correlation_reason: Optional[str] = None,
    ) -> SecurityIncident:
        """Correlate incident with related incidents (IR-5(1))"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # Update correlation IDs
        existing_correlations = incident.correlation_ids or []
        for related_id in related_incident_ids:
            if str(related_id) not in existing_correlations:
                existing_correlations.append(str(related_id))
        
        incident.correlation_ids = existing_correlations
        incident.updated_at = datetime.now(timezone.utc)
        
        # Create timeline entry
        timeline_entry = IncidentTimeline(
            incident_id=incident.id,
            event_time=datetime.now(timezone.utc),
            event_type="incident_correlation",
            event_description=f"Correlated with {len(related_incident_ids)} related incidents" + (
                f": {correlation_reason}" if correlation_reason else ""
            ),
            source="system",
            metadata={"related_incident_ids": [str(rid) for rid in related_incident_ids]},
        )
        db.add(timeline_entry)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Incidents correlated: incident_id={incident_id}, related={len(related_incident_ids)}")
        return incident

    @staticmethod
    def get_automated_summary(
        db: Session,
        incident_id: UUID,
    ) -> Dict[str, Any]:
        """Get automated summary of incident handling and analysis"""
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        return {
            "incident_id": str(incident.id),
            "incident_number": incident.incident_number,
            "automated_handling_enabled": incident.automated_handling_enabled,
            "automation_workflow_id": incident.automation_workflow_id,
            "automated_actions_count": len(incident.automated_actions_taken or []),
            "automated_actions": incident.automated_actions_taken,
            "automated_tracking_enabled": incident.automated_tracking_enabled,
            "data_collected": bool(incident.collected_data),
            "data_collection_timestamp": (
                incident.data_collection_timestamp.isoformat()
                if incident.data_collection_timestamp else None
            ),
            "analysis_performed": bool(incident.analysis_results),
            "analysis_timestamp": (
                incident.analysis_timestamp.isoformat()
                if incident.analysis_timestamp else None
            ),
            "correlated_incidents_count": len(incident.correlation_ids or []),
            "correlation_ids": incident.correlation_ids,
        }
