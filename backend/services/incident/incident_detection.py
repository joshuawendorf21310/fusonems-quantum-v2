"""
Automated Incident Detection Service for FedRAMP IR-5 Compliance

Monitors audit logs and automatically detects security incidents based on
pattern matching and anomaly detection:
- Multiple failed login attempts
- Unusual access patterns
- Privilege escalation attempts
- Data exfiltration indicators
- Other security-relevant patterns

IR-5 requires continuous monitoring and automated detection capabilities.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from core.logger import logger
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from models.incident import (
    SecurityIncident,
    IncidentSeverity,
    IncidentCategory,
)
from models.user import User
from .incident_service import IncidentService


class IncidentDetectionService:
    """Service for automated incident detection from audit logs"""

    # Detection thresholds
    FAILED_LOGIN_THRESHOLD = 5  # Failed logins within time window
    FAILED_LOGIN_WINDOW_MINUTES = 15
    
    UNUSUAL_ACCESS_THRESHOLD = 10  # Unusual access patterns
    UNUSUAL_ACCESS_WINDOW_MINUTES = 60
    
    PRIVILEGE_ESCALATION_THRESHOLD = 3  # Privilege escalation attempts
    PRIVILEGE_ESCALATION_WINDOW_MINUTES = 30

    @staticmethod
    def detect_failed_login_patterns(
        db: Session,
        org_id: int,
        time_window_minutes: int = None,
        threshold: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns of multiple failed login attempts.
        
        Returns list of detected incidents (dictionaries with detection details).
        """
        time_window_minutes = time_window_minutes or IncidentDetectionService.FAILED_LOGIN_WINDOW_MINUTES
        threshold = threshold or IncidentDetectionService.FAILED_LOGIN_THRESHOLD
        
        window_start = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Query for failed authentication attempts
        failed_logins = (
            db.query(ComprehensiveAuditLog)
            .filter(
                ComprehensiveAuditLog.org_id == org_id,
                ComprehensiveAuditLog.event_type == AuditEventType.AUTHENTICATION.value,
                ComprehensiveAuditLog.action == "login",
                ComprehensiveAuditLog.outcome.in_([AuditOutcome.FAILURE.value, AuditOutcome.DENIED.value]),
                ComprehensiveAuditLog.timestamp >= window_start,
            )
            .order_by(ComprehensiveAuditLog.timestamp)
            .all()
        )
        
        # Group by user_id and IP address
        user_ip_counts: Dict[tuple, List[ComprehensiveAuditLog]] = {}
        for log_entry in failed_logins:
            key = (log_entry.user_id, log_entry.ip_address)
            if key not in user_ip_counts:
                user_ip_counts[key] = []
            user_ip_counts[key].append(log_entry)
        
        # Detect patterns exceeding threshold
        detected_incidents = []
        for (user_id, ip_address), log_entries in user_ip_counts.items():
            if len(log_entries) >= threshold:
                user_email = log_entries[0].user_email
                first_attempt = min(log_entry.timestamp for log_entry in log_entries)
                last_attempt = max(log_entry.timestamp for log_entry in log_entries)
                
                detected_incidents.append({
                    "type": "failed_login_pattern",
                    "severity": IncidentSeverity.MODERATE if len(log_entries) < threshold * 2 else IncidentSeverity.HIGH,
                    "category": IncidentCategory.AUTHENTICATION,
                    "title": f"Multiple Failed Login Attempts - {user_email or 'Unknown User'}",
                    "description": (
                        f"Detected {len(log_entries)} failed login attempts "
                        f"from IP {ip_address} for user {user_email or f'ID:{user_id}'} "
                        f"within {time_window_minutes} minutes. "
                        f"First attempt: {first_attempt.isoformat()}, "
                        f"Last attempt: {last_attempt.isoformat()}."
                    ),
                    "affected_users": [user_id] if user_id else [],
                    "metadata": {
                        "failed_attempts": len(log_entries),
                        "ip_address": ip_address,
                        "user_id": user_id,
                        "user_email": user_email,
                        "time_window_minutes": time_window_minutes,
                        "first_attempt": first_attempt.isoformat(),
                        "last_attempt": last_attempt.isoformat(),
                        "log_entry_ids": [str(log_entry.id) for log_entry in log_entries],
                    },
                })
        
        return detected_incidents

    @staticmethod
    def detect_unusual_access_patterns(
        db: Session,
        org_id: int,
        time_window_minutes: int = None,
        threshold: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual access patterns (e.g., access from multiple IPs,
        unusual times, rapid resource access).
        """
        time_window_minutes = time_window_minutes or IncidentDetectionService.UNUSUAL_ACCESS_WINDOW_MINUTES
        threshold = threshold or IncidentDetectionService.UNUSUAL_ACCESS_THRESHOLD
        
        window_start = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Query for data access events
        access_events = (
            db.query(ComprehensiveAuditLog)
            .filter(
                ComprehensiveAuditLog.org_id == org_id,
                ComprehensiveAuditLog.event_type == AuditEventType.DATA_ACCESS.value,
                ComprehensiveAuditLog.outcome == AuditOutcome.SUCCESS.value,
                ComprehensiveAuditLog.timestamp >= window_start,
            )
            .order_by(ComprehensiveAuditLog.timestamp)
            .all()
        )
        
        # Group by user_id
        user_access: Dict[int, List[ComprehensiveAuditLog]] = {}
        for log_entry in access_events:
            if log_entry.user_id:
                if log_entry.user_id not in user_access:
                    user_access[log_entry.user_id] = []
                user_access[log_entry.user_id].append(log_entry)
        
        # Detect unusual patterns
        detected_incidents = []
        for user_id, log_entries in user_access.items():
            if len(log_entries) >= threshold:
                # Check for multiple IP addresses
                unique_ips = set(log_entry.ip_address for log_entry in log_entries if log_entry.ip_address)
                unique_resources = set(
                    f"{log_entry.resource_type}:{log_entry.resource_id}"
                    for log_entry in log_entries
                    if log_entry.resource_type and log_entry.resource_id
                )
                
                user_email = log_entries[0].user_email if log_entries else None
                
                # Flag if accessing from multiple IPs or many resources
                if len(unique_ips) > 3 or len(unique_resources) > threshold:
                    detected_incidents.append({
                        "type": "unusual_access_pattern",
                        "severity": IncidentSeverity.MODERATE,
                        "category": IncidentCategory.DATA_ACCESS,
                        "title": f"Unusual Access Pattern - {user_email or 'Unknown User'}",
                        "description": (
                            f"Detected unusual access pattern for user {user_email or f'ID:{user_id}'}. "
                            f"Total access events: {len(log_entries)}, "
                            f"Unique IP addresses: {len(unique_ips)}, "
                            f"Unique resources accessed: {len(unique_resources)}."
                        ),
                        "affected_users": [user_id],
                        "metadata": {
                            "access_count": len(log_entries),
                            "unique_ips": list(unique_ips),
                            "unique_resources": list(unique_resources),
                            "user_id": user_id,
                            "user_email": user_email,
                            "time_window_minutes": time_window_minutes,
                            "log_entry_ids": [str(log_entry.id) for log_entry in log_entries],
                        },
                    })
        
        return detected_incidents

    @staticmethod
    def detect_privilege_escalation_attempts(
        db: Session,
        org_id: int,
        time_window_minutes: int = None,
        threshold: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect privilege escalation attempts (e.g., unauthorized role changes,
        permission modifications).
        """
        time_window_minutes = time_window_minutes or IncidentDetectionService.PRIVILEGE_ESCALATION_WINDOW_MINUTES
        threshold = threshold or IncidentDetectionService.PRIVILEGE_ESCALATION_THRESHOLD
        
        window_start = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Query for authorization failures and role/permission changes
        escalation_attempts = (
            db.query(ComprehensiveAuditLog)
            .filter(
                ComprehensiveAuditLog.org_id == org_id,
                or_(
                    and_(
                        ComprehensiveAuditLog.event_type == AuditEventType.AUTHORIZATION.value,
                        ComprehensiveAuditLog.outcome.in_([AuditOutcome.DENIED.value, AuditOutcome.FAILURE.value]),
                    ),
                    and_(
                        ComprehensiveAuditLog.event_type == AuditEventType.CONFIGURATION_CHANGE.value,
                        ComprehensiveAuditLog.action.in_(["role_change", "permission_change", "privilege_change"]),
                    ),
                ),
                ComprehensiveAuditLog.timestamp >= window_start,
            )
            .order_by(ComprehensiveAuditLog.timestamp)
            .all()
        )
        
        # Group by user_id
        user_attempts: Dict[int, List[ComprehensiveAuditLog]] = {}
        for log_entry in escalation_attempts:
            if log_entry.user_id:
                if log_entry.user_id not in user_attempts:
                    user_attempts[log_entry.user_id] = []
                user_attempts[log_entry.user_id].append(log_entry)
        
        # Detect patterns exceeding threshold
        detected_incidents = []
        for user_id, log_entries in user_attempts.items():
            if len(log_entries) >= threshold:
                user_email = log_entries[0].user_email if log_entries else None
                
                detected_incidents.append({
                    "type": "privilege_escalation",
                    "severity": IncidentSeverity.HIGH,
                    "category": IncidentCategory.PRIVILEGE_ESCALATION,
                    "title": f"Privilege Escalation Attempts - {user_email or 'Unknown User'}",
                    "description": (
                        f"Detected {len(log_entries)} privilege escalation attempts "
                        f"for user {user_email or f'ID:{user_id}'} "
                        f"within {time_window_minutes} minutes."
                    ),
                    "affected_users": [user_id],
                    "metadata": {
                        "attempt_count": len(log_entries),
                        "user_id": user_id,
                        "user_email": user_email,
                        "time_window_minutes": time_window_minutes,
                        "log_entry_ids": [str(log_entry.id) for log_entry in log_entries],
                    },
                })
        
        return detected_incidents

    @staticmethod
    def detect_data_exfiltration_indicators(
        db: Session,
        org_id: int,
        time_window_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Detect potential data exfiltration indicators:
        - Large volume of data access
        - Bulk exports/downloads
        - Unusual data access patterns
        """
        window_start = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Query for bulk data operations
        bulk_operations = (
            db.query(ComprehensiveAuditLog)
            .filter(
                ComprehensiveAuditLog.org_id == org_id,
                ComprehensiveAuditLog.event_type == AuditEventType.DATA_ACCESS.value,
                ComprehensiveAuditLog.action.in_(["export", "download", "bulk_read", "batch_export"]),
                ComprehensiveAuditLog.outcome == AuditOutcome.SUCCESS.value,
                ComprehensiveAuditLog.timestamp >= window_start,
            )
            .order_by(ComprehensiveAuditLog.timestamp)
            .all()
        )
        
        # Group by user_id
        user_operations: Dict[int, List[ComprehensiveAuditLog]] = {}
        for log_entry in bulk_operations:
            if log_entry.user_id:
                if log_entry.user_id not in user_operations:
                    user_operations[user_id] = []
                user_operations[user_id].append(log_entry)
        
        # Detect suspicious patterns
        detected_incidents = []
        for user_id, log_entries in user_operations.items():
            if len(log_entries) >= 5:  # Threshold for bulk operations
                user_email = log_entries[0].user_email if log_entries else None
                
                detected_incidents.append({
                    "type": "data_exfiltration_indicator",
                    "severity": IncidentSeverity.HIGH,
                    "category": IncidentCategory.DATA_EXFILTRATION,
                    "title": f"Potential Data Exfiltration - {user_email or 'Unknown User'}",
                    "description": (
                        f"Detected {len(log_entries)} bulk data operations "
                        f"by user {user_email or f'ID:{user_id}'} "
                        f"within {time_window_minutes} minutes. "
                        f"This may indicate data exfiltration."
                    ),
                    "affected_users": [user_id],
                    "metadata": {
                        "operation_count": len(log_entries),
                        "user_id": user_id,
                        "user_email": user_email,
                        "time_window_minutes": time_window_minutes,
                        "log_entry_ids": [str(log_entry.id) for log_entry in log_entries],
                    },
                })
        
        return detected_incidents

    @staticmethod
    def run_detection_scan(
        db: Session,
        org_id: int,
        auto_create: bool = True,
    ) -> List[SecurityIncident]:
        """
        Run all detection patterns and optionally create incidents.
        
        Returns list of created incidents.
        """
        logger.info(f"Running incident detection scan for org_id={org_id}")
        
        all_detections = []
        
        # Run all detection methods
        try:
            all_detections.extend(
                IncidentDetectionService.detect_failed_login_patterns(db, org_id)
            )
        except Exception as e:
            logger.error(f"Error in failed login detection: {e}", exc_info=True)
        
        try:
            all_detections.extend(
                IncidentDetectionService.detect_unusual_access_patterns(db, org_id)
            )
        except Exception as e:
            logger.error(f"Error in unusual access detection: {e}", exc_info=True)
        
        try:
            all_detections.extend(
                IncidentDetectionService.detect_privilege_escalation_attempts(db, org_id)
            )
        except Exception as e:
            logger.error(f"Error in privilege escalation detection: {e}", exc_info=True)
        
        try:
            all_detections.extend(
                IncidentDetectionService.detect_data_exfiltration_indicators(db, org_id)
            )
        except Exception as e:
            logger.error(f"Error in data exfiltration detection: {e}", exc_info=True)
        
        created_incidents = []
        
        if auto_create:
            for detection in all_detections:
                try:
                    # Check if similar incident already exists (avoid duplicates)
                    existing = (
                        db.query(SecurityIncident)
                        .filter(
                            SecurityIncident.org_id == org_id,
                            SecurityIncident.status.in_([
                                IncidentStatus.NEW.value,
                                IncidentStatus.INVESTIGATING.value,
                            ]),
                            SecurityIncident.category == detection["category"].value,
                        )
                        .order_by(desc(SecurityIncident.created_at))
                        .first()
                    )
                    
                    # Only create if no recent similar incident exists
                    if not existing or (
                        existing.created_at < datetime.now(timezone.utc) - timedelta(hours=1)
                    ):
                        incident = IncidentService.create_incident(
                            db=db,
                            org_id=org_id,
                            title=detection["title"],
                            description=detection["description"],
                            severity=detection["severity"],
                            category=detection["category"],
                            detected_by_system=True,
                            detection_method="automated_pattern_detection",
                            affected_users=detection.get("affected_users"),
                            metadata=detection.get("metadata", {}),
                            classification="NON_PHI",  # Adjust based on actual data
                            training_mode=False,
                        )
                        created_incidents.append(incident)
                        logger.info(
                            f"Auto-created incident from detection: {incident.incident_number}, "
                            f"type={detection['type']}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error creating incident from detection: {e}",
                        exc_info=True,
                    )
        
        logger.info(
            f"Incident detection scan completed: {len(all_detections)} detections, "
            f"{len(created_incidents)} incidents created"
        )
        
        return created_incidents
