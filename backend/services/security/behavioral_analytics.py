"""
Behavioral Analytics Service for FedRAMP SI-4 Compliance

This service provides user behavior analysis and anomaly detection:
- User behavior baseline establishment
- Real-time anomaly detection
- Risk scoring
- Alert trigger generation

FedRAMP SI-4: Information System Monitoring requires monitoring of
user activities and detection of anomalous behavior patterns.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from models.security_event import SecurityEvent, EventSeverity, SecurityEventType
from models.user import User
from utils.logger import logger


@dataclass
class BehaviorBaseline:
    """User behavior baseline metrics"""
    user_id: int
    avg_requests_per_hour: float
    avg_requests_per_day: float
    common_ip_addresses: List[str]
    common_user_agents: List[str]
    common_endpoints: List[str]
    typical_access_times: Dict[str, int]  # Hour of day -> count
    typical_access_days: Dict[str, int]  # Day of week -> count
    baseline_established_at: datetime
    last_updated_at: datetime


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    user_id: int
    anomaly_type: str
    risk_score: float
    confidence: float
    indicators: List[str]
    severity: EventSeverity
    description: str


class BehavioralAnalytics:
    """
    Behavioral analytics service for user behavior analysis and anomaly detection.
    
    Features:
    - Establishes user behavior baselines
    - Detects anomalies in real-time
    - Calculates risk scores
    - Generates security events for anomalies
    """
    
    # Baseline calculation parameters
    BASELINE_WINDOW_DAYS = 30  # Days of history to use for baseline
    MIN_BASELINE_EVENTS = 100  # Minimum events required for baseline
    
    # Anomaly detection thresholds
    ANOMALY_RISK_THRESHOLD_LOW = 0.3
    ANOMALY_RISK_THRESHOLD_MEDIUM = 0.5
    ANOMALY_RISK_THRESHOLD_HIGH = 0.7
    ANOMALY_RISK_THRESHOLD_CRITICAL = 0.9
    
    # IP address anomaly thresholds
    IP_CHANGE_THRESHOLD = 0.8  # If >80% requests from new IPs, flag
    GEOGRAPHIC_DISTANCE_THRESHOLD_KM = 1000  # Flag if IP geolocation changes significantly
    
    # Request rate anomaly thresholds
    REQUEST_RATE_MULTIPLIER = 3.0  # Flag if requests exceed baseline * multiplier
    UNUSUAL_HOUR_THRESHOLD = 0.1  # Flag if >10% requests at unusual hours
    
    def __init__(self, db: Session):
        """
        Initialize behavioral analytics service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._baseline_cache: Dict[int, BehaviorBaseline] = {}
        self._baseline_cache_ttl = timedelta(hours=1)
    
    def establish_baseline(self, user_id: int, org_id: int) -> Optional[BehaviorBaseline]:
        """
        Establish behavior baseline for a user.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            BehaviorBaseline object or None if insufficient data
        """
        # Check cache first
        if user_id in self._baseline_cache:
            baseline = self._baseline_cache[user_id]
            if datetime.utcnow() - baseline.last_updated_at < self._baseline_cache_ttl:
                return baseline
        
        # Calculate baseline from audit logs
        cutoff_date = datetime.utcnow() - timedelta(days=self.BASELINE_WINDOW_DAYS)
        
        # Get user's audit log events
        events = self.db.query(ComprehensiveAuditLog).filter(
            and_(
                ComprehensiveAuditLog.user_id == user_id,
                ComprehensiveAuditLog.org_id == org_id,
                ComprehensiveAuditLog.timestamp >= cutoff_date,
                ComprehensiveAuditLog.training_mode == False,
            )
        ).order_by(ComprehensiveAuditLog.timestamp).all()
        
        if len(events) < self.MIN_BASELINE_EVENTS:
            logger.debug(f"Insufficient events for baseline: user_id={user_id}, events={len(events)}")
            return None
        
        # Calculate metrics
        total_hours = (datetime.utcnow() - cutoff_date).total_seconds() / 3600
        total_days = (datetime.utcnow() - cutoff_date).days
        
        avg_requests_per_hour = len(events) / max(total_hours, 1)
        avg_requests_per_day = len(events) / max(total_days, 1)
        
        # IP addresses
        ip_counts = defaultdict(int)
        for event in events:
            if event.ip_address:
                ip_counts[event.ip_address] += 1
        
        common_ip_addresses = [
            ip for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # User agents
        ua_counts = defaultdict(int)
        for event in events:
            if event.user_agent:
                ua_counts[event.user_agent] += 1
        
        common_user_agents = [
            ua for ua, count in sorted(ua_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Endpoints
        endpoint_counts = defaultdict(int)
        for event in events:
            if event.request_path:
                # Normalize endpoint (remove IDs)
                endpoint = self._normalize_endpoint(event.request_path)
                endpoint_counts[endpoint] += 1
        
        common_endpoints = [
            endpoint for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
        
        # Access times (hour of day)
        access_times = defaultdict(int)
        for event in events:
            hour = event.timestamp.hour
            access_times[str(hour)] += 1
        
        # Access days (day of week)
        access_days = defaultdict(int)
        for event in events:
            day = event.timestamp.strftime("%A")
            access_days[day] += 1
        
        baseline = BehaviorBaseline(
            user_id=user_id,
            avg_requests_per_hour=avg_requests_per_hour,
            avg_requests_per_day=avg_requests_per_day,
            common_ip_addresses=common_ip_addresses,
            common_user_agents=common_user_agents,
            common_endpoints=common_endpoints,
            typical_access_times=dict(access_times),
            typical_access_days=dict(access_days),
            baseline_established_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow(),
        )
        
        # Cache baseline
        self._baseline_cache[user_id] = baseline
        
        logger.info(
            f"Established behavior baseline for user_id={user_id}",
            extra={
                "user_id": user_id,
                "events_analyzed": len(events),
                "avg_requests_per_hour": avg_requests_per_hour,
                "event_type": "behavioral.baseline.established",
            }
        )
        
        return baseline
    
    def detect_anomalies(
        self,
        user_id: int,
        org_id: int,
        recent_events: Optional[List[ComprehensiveAuditLog]] = None,
        time_window_hours: int = 1
    ) -> List[AnomalyDetection]:
        """
        Detect anomalies in user behavior.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            recent_events: Optional list of recent events to analyze
            time_window_hours: Time window for recent activity analysis
            
        Returns:
            List of AnomalyDetection objects
        """
        anomalies = []
        
        # Get baseline
        baseline = self.establish_baseline(user_id, org_id)
        if not baseline:
            # No baseline yet, can't detect anomalies
            return anomalies
        
        # Get recent events if not provided
        if recent_events is None:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            recent_events = self.db.query(ComprehensiveAuditLog).filter(
                and_(
                    ComprehensiveAuditLog.user_id == user_id,
                    ComprehensiveAuditLog.org_id == org_id,
                    ComprehensiveAuditLog.timestamp >= cutoff_time,
                    ComprehensiveAuditLog.training_mode == False,
                )
            ).all()
        
        if not recent_events:
            return anomalies
        
        # Check for various anomaly types
        anomalies.extend(self._detect_ip_anomaly(user_id, recent_events, baseline))
        anomalies.extend(self._detect_request_rate_anomaly(user_id, recent_events, baseline))
        anomalies.extend(self._detect_time_anomaly(user_id, recent_events, baseline))
        anomalies.extend(self._detect_endpoint_anomaly(user_id, recent_events, baseline))
        anomalies.extend(self._detect_user_agent_anomaly(user_id, recent_events, baseline))
        anomalies.extend(self._detect_failed_auth_anomaly(user_id, recent_events))
        anomalies.extend(self._detect_privilege_anomaly(user_id, recent_events))
        
        return anomalies
    
    def calculate_risk_score(self, anomalies: List[AnomalyDetection]) -> float:
        """
        Calculate overall risk score from anomalies.
        
        Args:
            anomalies: List of anomaly detections
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        if not anomalies:
            return 0.0
        
        # Weight anomalies by severity
        severity_weights = {
            EventSeverity.CRITICAL: 1.0,
            EventSeverity.HIGH: 0.7,
            EventSeverity.MEDIUM: 0.4,
            EventSeverity.LOW: 0.2,
            EventSeverity.INFORMATIONAL: 0.1,
        }
        
        weighted_sum = sum(
            anomaly.risk_score * severity_weights.get(anomaly.severity, 0.1)
            for anomaly in anomalies
        )
        
        # Normalize to 0-1 range
        risk_score = min(1.0, weighted_sum / len(anomalies))
        
        return risk_score
    
    def _detect_ip_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog],
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Detect IP address anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Count IP addresses in recent events
        recent_ips = {}
        for event in events:
            if event.ip_address:
                recent_ips[event.ip_address] = recent_ips.get(event.ip_address, 0) + 1
        
        # Check if new IP addresses are being used
        new_ips = [ip for ip in recent_ips.keys() if ip not in baseline.common_ip_addresses]
        new_ip_ratio = len(new_ips) / max(len(recent_ips), 1)
        
        if new_ip_ratio > self.IP_CHANGE_THRESHOLD and len(new_ips) > 0:
            risk_score = min(1.0, new_ip_ratio)
            severity = self._determine_severity(risk_score)
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="ip_address_change",
                risk_score=risk_score,
                confidence=0.8,
                indicators=[f"New IP addresses: {', '.join(new_ips[:5])}"],
                severity=severity,
                description=f"User accessing from {len(new_ips)} new IP address(es) not in baseline",
            ))
        
        return anomalies
    
    def _detect_request_rate_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog],
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Detect request rate anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Calculate request rate for recent events
        if len(events) < 2:
            return anomalies
        
        time_span = (events[-1].timestamp - events[0].timestamp).total_seconds() / 3600
        if time_span == 0:
            time_span = 1.0
        
        recent_rate = len(events) / time_span
        
        # Compare to baseline
        if recent_rate > baseline.avg_requests_per_hour * self.REQUEST_RATE_MULTIPLIER:
            risk_score = min(1.0, recent_rate / (baseline.avg_requests_per_hour * self.REQUEST_RATE_MULTIPLIER))
            severity = self._determine_severity(risk_score)
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="unusual_request_rate",
                risk_score=risk_score,
                confidence=0.7,
                indicators=[f"Request rate: {recent_rate:.2f}/hr (baseline: {baseline.avg_requests_per_hour:.2f}/hr)"],
                severity=severity,
                description=f"Unusually high request rate detected: {recent_rate:.2f} requests/hour",
            ))
        
        return anomalies
    
    def _detect_time_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog],
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Detect time-based anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Check for unusual access times
        unusual_hour_count = 0
        for event in events:
            hour = str(event.timestamp.hour)
            if hour not in baseline.typical_access_times or baseline.typical_access_times[hour] < 5:
                unusual_hour_count += 1
        
        unusual_ratio = unusual_hour_count / len(events)
        
        if unusual_ratio > self.UNUSUAL_HOUR_THRESHOLD:
            risk_score = min(1.0, unusual_ratio * 2)
            severity = self._determine_severity(risk_score)
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="unusual_access_time",
                risk_score=risk_score,
                confidence=0.6,
                indicators=[f"Unusual hour access ratio: {unusual_ratio:.2%}"],
                severity=severity,
                description=f"Access during unusual hours: {unusual_ratio:.2%} of recent activity",
            ))
        
        return anomalies
    
    def _detect_endpoint_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog],
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Detect endpoint access anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Check for access to unusual endpoints
        unusual_endpoints = []
        for event in events:
            if event.request_path:
                normalized = self._normalize_endpoint(event.request_path)
                if normalized not in baseline.common_endpoints:
                    unusual_endpoints.append(event.request_path)
        
        if len(unusual_endpoints) > 5:  # Threshold for unusual endpoint access
            risk_score = min(1.0, len(unusual_endpoints) / 20.0)
            severity = self._determine_severity(risk_score)
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="unusual_endpoint_access",
                risk_score=risk_score,
                confidence=0.6,
                indicators=[f"Unusual endpoints accessed: {len(unusual_endpoints)}"],
                severity=severity,
                description=f"Access to {len(unusual_endpoints)} unusual endpoints",
            ))
        
        return anomalies
    
    def _detect_user_agent_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog],
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Detect user agent anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Check for new user agents
        recent_uas = set()
        for event in events:
            if event.user_agent:
                recent_uas.add(event.user_agent)
        
        new_uas = [ua for ua in recent_uas if ua not in baseline.common_user_agents]
        
        if len(new_uas) > 0:
            risk_score = min(1.0, len(new_uas) / 3.0)
            severity = self._determine_severity(risk_score)
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="user_agent_change",
                risk_score=risk_score,
                confidence=0.5,
                indicators=[f"New user agents: {len(new_uas)}"],
                severity=severity,
                description=f"Access from {len(new_uas)} new user agent(s)",
            ))
        
        return anomalies
    
    def _detect_failed_auth_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog]
    ) -> List[AnomalyDetection]:
        """Detect failed authentication anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Count failed authentication attempts
        failed_auths = [
            e for e in events
            if e.event_type == AuditEventType.AUTHENTICATION.value
            and e.outcome == AuditOutcome.FAILURE.value
        ]
        
        if len(failed_auths) >= 5:  # Threshold for failed auth anomaly
            risk_score = min(1.0, len(failed_auths) / 10.0)
            severity = EventSeverity.HIGH if len(failed_auths) >= 10 else EventSeverity.MEDIUM
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="failed_authentication",
                risk_score=risk_score,
                confidence=0.9,
                indicators=[f"Failed authentication attempts: {len(failed_auths)}"],
                severity=severity,
                description=f"Multiple failed authentication attempts: {len(failed_auths)}",
            ))
        
        return anomalies
    
    def _detect_privilege_anomaly(
        self,
        user_id: int,
        events: List[ComprehensiveAuditLog]
    ) -> List[AnomalyDetection]:
        """Detect privilege escalation anomalies"""
        anomalies = []
        
        if not events:
            return anomalies
        
        # Check for authorization violations
        auth_violations = [
            e for e in events
            if e.event_type == AuditEventType.AUTHORIZATION.value
            and e.outcome == AuditOutcome.DENIED.value
        ]
        
        if len(auth_violations) >= 3:
            risk_score = min(1.0, len(auth_violations) / 5.0)
            severity = EventSeverity.HIGH
            
            anomalies.append(AnomalyDetection(
                user_id=user_id,
                anomaly_type="privilege_escalation_attempt",
                risk_score=risk_score,
                confidence=0.8,
                indicators=[f"Authorization violations: {len(auth_violations)}"],
                severity=severity,
                description=f"Multiple authorization violations: {len(auth_violations)}",
            ))
        
        return anomalies
    
    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint by removing IDs"""
        import re
        # Replace UUIDs and numeric IDs with placeholders
        endpoint = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', endpoint)
        endpoint = re.sub(r'/\d+', '/{id}', endpoint)
        return endpoint
    
    def _determine_severity(self, risk_score: float) -> EventSeverity:
        """Determine severity based on risk score"""
        if risk_score >= self.ANOMALY_RISK_THRESHOLD_CRITICAL:
            return EventSeverity.CRITICAL
        elif risk_score >= self.ANOMALY_RISK_THRESHOLD_HIGH:
            return EventSeverity.HIGH
        elif risk_score >= self.ANOMALY_RISK_THRESHOLD_MEDIUM:
            return EventSeverity.MEDIUM
        elif risk_score >= self.ANOMALY_RISK_THRESHOLD_LOW:
            return EventSeverity.LOW
        else:
            return EventSeverity.INFORMATIONAL
    
    def should_trigger_alert(self, anomaly: AnomalyDetection) -> bool:
        """
        Determine if an anomaly should trigger an alert.
        
        Args:
            anomaly: Anomaly detection result
            
        Returns:
            True if alert should be triggered
        """
        # Trigger alerts for medium severity and above
        return anomaly.severity in [
            EventSeverity.MEDIUM,
            EventSeverity.HIGH,
            EventSeverity.CRITICAL,
        ]
