"""
Security Monitoring Service for FedRAMP SI-4 Compliance

This service provides comprehensive security monitoring capabilities:
- Real-time security event monitoring
- Anomaly detection algorithms
- Behavioral analytics integration
- Threat intelligence integration
- Alert generation
- Security metrics collection

FedRAMP SI-4: Information System Monitoring requires continuous monitoring
of information system components and detection of security events.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_

from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from models.security_event import (
    SecurityEvent,
    SecurityEventType,
    EventSeverity,
    AlertStatus,
    InvestigationStatus,
    SecurityAlert,
)
from models.user import User
from services.security.behavioral_analytics import BehavioralAnalytics, AnomalyDetection
from utils.logger import logger


@dataclass
class SecurityMetrics:
    """Security metrics for dashboard and reporting"""
    total_events_24h: int
    total_events_7d: int
    total_events_30d: int
    events_by_severity: Dict[str, int]
    events_by_type: Dict[str, int]
    active_alerts: int
    alerts_by_status: Dict[str, int]
    anomalies_detected_24h: int
    threat_intelligence_matches_24h: int
    avg_response_time_seconds: float
    investigation_backlog: int


class ThreatIntelligenceFeed:
    """
    Threat intelligence feed integration.
    
    In production, this would integrate with external threat intelligence
    sources such as:
    - MITRE ATT&CK framework
    - STIX/TAXII feeds
    - Commercial threat intelligence providers
    - Open source threat feeds
    """
    
    def __init__(self):
        self.indicators: Dict[str, Dict] = {}
        self.last_update = None
    
    def check_indicator(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """
        Check if indicators match known threats.
        
        Args:
            ip_address: IP address to check
            user_agent: User agent to check
            
        Returns:
            Tuple of (matched, list of matched indicators)
        """
        matched_indicators = []
        
        # Example: Check against known malicious IPs
        # In production, this would query external threat feeds
        malicious_ips = {
            # Example malicious IPs (would come from threat feed)
        }
        
        if ip_address and ip_address in malicious_ips:
            matched_indicators.append({
                "type": "malicious_ip",
                "value": ip_address,
                "source": "threat_feed",
                "confidence": 0.9,
            })
        
        # Example: Check for known malicious user agents
        malicious_user_agents = [
            "sqlmap",
            "nikto",
            "nmap",
            # Add more known malicious patterns
        ]
        
        if user_agent:
            ua_lower = user_agent.lower()
            for malicious_ua in malicious_user_agents:
                if malicious_ua in ua_lower:
                    matched_indicators.append({
                        "type": "malicious_user_agent",
                        "value": user_agent,
                        "source": "threat_feed",
                        "confidence": 0.8,
                    })
                    break
        
        return len(matched_indicators) > 0, matched_indicators
    
    def update_feed(self):
        """Update threat intelligence feed from external sources"""
        # In production, this would fetch from external APIs
        self.last_update = datetime.utcnow()
        logger.info("Threat intelligence feed updated")


class SecurityMonitoringService:
    """
    Security monitoring service for FedRAMP SI-4 compliance.
    
    Provides:
    - Real-time event monitoring
    - Anomaly detection
    - Threat intelligence correlation
    - Alert generation
    - Metrics collection
    """
    
    def __init__(self, db: Session):
        """
        Initialize security monitoring service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.behavioral_analytics = BehavioralAnalytics(db)
        self.threat_intelligence = ThreatIntelligenceFeed()
    
    def monitor_audit_event(self, audit_event: ComprehensiveAuditLog) -> Optional[SecurityEvent]:
        """
        Monitor an audit event and create security event if needed.
        
        Args:
            audit_event: Audit log event to monitor
            
        Returns:
            SecurityEvent if created, None otherwise
        """
        # Check if this event should generate a security event
        should_create_event = self._should_create_security_event(audit_event)
        
        if not should_create_event:
            return None
        
        # Create security event
        security_event = self._create_security_event_from_audit(audit_event)
        
        # Check threat intelligence
        threat_matched, threat_indicators = self.threat_intelligence.check_indicator(
            ip_address=audit_event.ip_address,
            user_agent=audit_event.user_agent
        )
        
        if threat_matched:
            security_event.threat_intelligence_matched = True
            security_event.threat_indicators = threat_indicators
            security_event.threat_feed_sources = [ind.get("source", "unknown") for ind in threat_indicators]
            security_event.severity = EventSeverity.HIGH.value
        
        # Run behavioral analytics if user is known
        if audit_event.user_id:
            anomalies = self.behavioral_analytics.detect_anomalies(
                user_id=audit_event.user_id,
                org_id=audit_event.org_id,
                recent_events=[audit_event],
                time_window_hours=1
            )
            
            if anomalies:
                # Use highest severity anomaly
                highest_anomaly = max(anomalies, key=lambda a: self._severity_to_numeric(a.severity))
                security_event.behavioral_anomaly_detected = True
                security_event.behavioral_risk_score = highest_anomaly.risk_score
                security_event.behavioral_anomaly_type = highest_anomaly.anomaly_type
                
                # Upgrade severity if anomaly is significant
                if highest_anomaly.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
                    security_event.severity = highest_anomaly.severity.value
        
        # Determine if alert should be generated
        should_alert = self._should_generate_alert(security_event)
        
        if should_alert:
            security_event.alert_generated = True
            security_event.alert_status = AlertStatus.NEW.value
            
            # Create alert
            alert = self._create_alert(security_event)
            self.db.add(alert)
        
        self.db.add(security_event)
        self.db.commit()
        self.db.refresh(security_event)
        
        logger.info(
            f"Security event created: event_id={security_event.id}, type={security_event.event_type}, severity={security_event.severity}",
            extra={
                "event_id": str(security_event.id),
                "event_type": security_event.event_type,
                "severity": security_event.severity,
                "alert_generated": security_event.alert_generated,
                "event_type": "security.monitoring.event_created",
            }
        )
        
        return security_event
    
    def get_security_metrics(
        self,
        org_id: int,
        time_window_hours: int = 24
    ) -> SecurityMetrics:
        """
        Get security metrics for dashboard.
        
        Args:
            org_id: Organization ID
            time_window_hours: Time window for metrics
            
        Returns:
            SecurityMetrics object
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        cutoff_7d = datetime.utcnow() - timedelta(days=7)
        cutoff_30d = datetime.utcnow() - timedelta(days=30)
        
        # Event counts
        total_events_24h = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_24h,
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        total_events_7d = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_7d,
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        total_events_30d = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_30d,
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        # Events by severity
        events_by_severity = {}
        for severity in EventSeverity:
            count = self.db.query(SecurityEvent).filter(
                and_(
                    SecurityEvent.org_id == org_id,
                    SecurityEvent.timestamp >= cutoff_24h,
                    SecurityEvent.severity == severity.value,
                    SecurityEvent.training_mode == False,
                )
            ).count()
            events_by_severity[severity.value] = count
        
        # Events by type
        events_by_type = {}
        events_query = self.db.query(
            SecurityEvent.event_type,
            func.count(SecurityEvent.id).label('count')
        ).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_24h,
                SecurityEvent.training_mode == False,
            )
        ).group_by(SecurityEvent.event_type).all()
        
        for event_type, count in events_query:
            events_by_type[event_type] = count
        
        # Active alerts
        active_alerts = self.db.query(SecurityAlert).filter(
            and_(
                SecurityAlert.org_id == org_id,
                SecurityAlert.status.in_([
                    AlertStatus.NEW.value,
                    AlertStatus.ACKNOWLEDGED.value,
                    AlertStatus.INVESTIGATING.value,
                ]),
                SecurityAlert.training_mode == False,
            )
        ).count()
        
        # Alerts by status
        alerts_by_status = {}
        for status in AlertStatus:
            count = self.db.query(SecurityAlert).filter(
                and_(
                    SecurityAlert.org_id == org_id,
                    SecurityAlert.status == status.value,
                    SecurityAlert.training_mode == False,
                )
            ).count()
            alerts_by_status[status.value] = count
        
        # Anomalies detected
        anomalies_detected_24h = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_24h,
                SecurityEvent.behavioral_anomaly_detected == True,
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        # Threat intelligence matches
        threat_intelligence_matches_24h = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.timestamp >= cutoff_24h,
                SecurityEvent.threat_intelligence_matched == True,
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        # Investigation backlog
        investigation_backlog = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.investigation_status.in_([
                    InvestigationStatus.NOT_STARTED.value,
                    InvestigationStatus.IN_PROGRESS.value,
                ]),
                SecurityEvent.severity.in_([
                    EventSeverity.HIGH.value,
                    EventSeverity.CRITICAL.value,
                ]),
                SecurityEvent.training_mode == False,
            )
        ).count()
        
        return SecurityMetrics(
            total_events_24h=total_events_24h,
            total_events_7d=total_events_7d,
            total_events_30d=total_events_30d,
            events_by_severity=events_by_severity,
            events_by_type=events_by_type,
            active_alerts=active_alerts,
            alerts_by_status=alerts_by_status,
            anomalies_detected_24h=anomalies_detected_24h,
            threat_intelligence_matches_24h=threat_intelligence_matches_24h,
            avg_response_time_seconds=0.0,  # Would calculate from alert response times
            investigation_backlog=investigation_backlog,
        )
    
    def list_security_events(
        self,
        org_id: int,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        alert_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[SecurityEvent], int]:
        """
        List security events with filters.
        
        Args:
            org_id: Organization ID
            severity: Filter by severity
            event_type: Filter by event type
            alert_status: Filter by alert status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (events list, total count)
        """
        query = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.org_id == org_id,
                SecurityEvent.training_mode == False,
            )
        )
        
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        
        if alert_status:
            query = query.filter(SecurityEvent.alert_status == alert_status)
        
        total = query.count()
        events = query.order_by(
            desc(SecurityEvent.timestamp)
        ).offset(offset).limit(limit).all()
        
        return events, total
    
    def acknowledge_alert(
        self,
        alert_id: str,
        user_id: int
    ) -> Optional[SecurityAlert]:
        """
        Acknowledge a security alert.
        
        Args:
            alert_id: Alert ID
            user_id: User acknowledging the alert
            
        Returns:
            Updated SecurityAlert or None
        """
        alert = self.db.query(SecurityAlert).filter(
            SecurityAlert.id == alert_id
        ).first()
        
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        
        # Update related security event
        if alert.event_id:
            event = self.db.query(SecurityEvent).filter(
                SecurityEvent.id == alert.event_id
            ).first()
            if event:
                event.alert_status = AlertStatus.ACKNOWLEDGED.value
                event.alert_acknowledged_at = datetime.utcnow()
                event.alert_acknowledged_by = user_id
        
        self.db.commit()
        return alert
    
    def _should_create_security_event(self, audit_event: ComprehensiveAuditLog) -> bool:
        """Determine if audit event should create a security event"""
        # Create events for security-relevant audit events
        security_relevant_types = [
            AuditEventType.AUTHENTICATION,
            AuditEventType.AUTHORIZATION,
            AuditEventType.SECURITY_EVENT,
        ]
        
        if audit_event.event_type in [t.value for t in security_relevant_types]:
            return True
        
        # Create events for failed operations
        if audit_event.outcome in [AuditOutcome.FAILURE.value, AuditOutcome.DENIED.value]:
            return True
        
        # Create events for configuration changes
        if audit_event.event_type == AuditEventType.CONFIGURATION_CHANGE.value:
            return True
        
        return False
    
    def _create_security_event_from_audit(self, audit_event: ComprehensiveAuditLog) -> SecurityEvent:
        """Create security event from audit log event"""
        # Map audit event type to security event type
        event_type = self._map_event_type(audit_event)
        
        # Determine severity
        severity = self._determine_severity(audit_event)
        
        # Create security event
        security_event = SecurityEvent(
            timestamp=audit_event.timestamp,
            org_id=audit_event.org_id,
            user_id=audit_event.user_id,
            user_email=audit_event.user_email,
            event_type=event_type.value,
            severity=severity.value,
            title=self._generate_title(audit_event),
            description=audit_event.action or "Security event detected",
            source="audit_log",
            source_id=str(audit_event.id),
            ip_address=audit_event.ip_address,
            user_agent=audit_event.user_agent,
            request_method=audit_event.request_method,
            request_path=audit_event.request_path,
            session_id=audit_event.session_id,
            device_id=audit_event.device_id,
            device_fingerprint=audit_event.device_fingerprint,
            resource_type=audit_event.resource_type,
            resource_id=audit_event.resource_id,
            classification=audit_event.classification,
            training_mode=audit_event.training_mode,
            raw_event_data={
                "audit_log_id": str(audit_event.id),
                "action": audit_event.action,
                "outcome": audit_event.outcome,
            },
        )
        
        return security_event
    
    def _map_event_type(self, audit_event: ComprehensiveAuditLog) -> SecurityEventType:
        """Map audit event type to security event type"""
        if audit_event.event_type == AuditEventType.AUTHENTICATION.value:
            if audit_event.outcome == AuditOutcome.FAILURE.value:
                return SecurityEventType.AUTHENTICATION_FAILURE
            return SecurityEventType.SUSPICIOUS_ACTIVITY
        
        if audit_event.event_type == AuditEventType.AUTHORIZATION.value:
            if audit_event.outcome == AuditOutcome.DENIED.value:
                return SecurityEventType.AUTHORIZATION_VIOLATION
            return SecurityEventType.SUSPICIOUS_ACTIVITY
        
        if audit_event.event_type == AuditEventType.SECURITY_EVENT.value:
            return SecurityEventType.SUSPICIOUS_ACTIVITY
        
        if audit_event.event_type == AuditEventType.CONFIGURATION_CHANGE.value:
            return SecurityEventType.CONFIGURATION_CHANGE
        
        return SecurityEventType.OTHER
    
    def _determine_severity(self, audit_event: ComprehensiveAuditLog) -> EventSeverity:
        """Determine severity from audit event"""
        if audit_event.outcome == AuditOutcome.FAILURE.value:
            # Multiple failures might indicate attack
            return EventSeverity.MEDIUM
        
        if audit_event.outcome == AuditOutcome.DENIED.value:
            # Authorization violations are more serious
            return EventSeverity.HIGH
        
        if audit_event.event_type == AuditEventType.SECURITY_EVENT.value:
            return EventSeverity.HIGH
        
        return EventSeverity.LOW
    
    def _generate_title(self, audit_event: ComprehensiveAuditLog) -> str:
        """Generate title for security event"""
        if audit_event.event_type == AuditEventType.AUTHENTICATION.value:
            if audit_event.outcome == AuditOutcome.FAILURE.value:
                return f"Failed authentication attempt"
            return f"Authentication event"
        
        if audit_event.event_type == AuditEventType.AUTHORIZATION.value:
            if audit_event.outcome == AuditOutcome.DENIED.value:
                return f"Authorization violation"
            return f"Authorization event"
        
        return f"Security event: {audit_event.action}"
    
    def _should_generate_alert(self, security_event: SecurityEvent) -> bool:
        """Determine if alert should be generated"""
        # Generate alerts for medium severity and above
        if security_event.severity in [
            EventSeverity.MEDIUM.value,
            EventSeverity.HIGH.value,
            EventSeverity.CRITICAL.value,
        ]:
            return True
        
        # Generate alerts for threat intelligence matches
        if security_event.threat_intelligence_matched:
            return True
        
        # Generate alerts for high-risk behavioral anomalies
        if security_event.behavioral_anomaly_detected:
            if security_event.behavioral_risk_score and security_event.behavioral_risk_score >= 0.7:
                return True
        
        return False
    
    def _create_alert(self, security_event: SecurityEvent) -> SecurityAlert:
        """Create alert from security event"""
        alert = SecurityAlert(
            org_id=security_event.org_id,
            event_id=security_event.id,
            title=f"Security Alert: {security_event.title}",
            description=security_event.description,
            severity=security_event.severity,
            status=AlertStatus.NEW.value,
            classification=security_event.classification,
            training_mode=security_event.training_mode,
        )
        
        return alert
    
    def _severity_to_numeric(self, severity: EventSeverity) -> int:
        """Convert severity to numeric for comparison"""
        severity_map = {
            EventSeverity.INFORMATIONAL: 1,
            EventSeverity.LOW: 2,
            EventSeverity.MEDIUM: 3,
            EventSeverity.HIGH: 4,
            EventSeverity.CRITICAL: 5,
        }
        return severity_map.get(severity, 0)
