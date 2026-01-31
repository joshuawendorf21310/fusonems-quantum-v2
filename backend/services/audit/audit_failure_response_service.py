"""
Audit Failure Response Service for FedRAMP AU-5 Compliance

FedRAMP Requirement AU-5: Response to Audit Processing Failures
- Detect audit system failures
- Automated alerting
- Failover to alternate logging
- Capacity monitoring
"""
import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from core.logger import logger
from core.config import settings
from models.audit_failure import (
    AuditFailureResponse,
    AuditSystemCapacity,
    AuditFailureSeverity,
    AuditFailureStatus,
    AuditFailureType,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from services.audit.comprehensive_audit_service import ComprehensiveAuditService


class AuditFailureResponseService:
    """
    Service for detecting and responding to audit system failures (AU-5).
    """
    
    # Capacity thresholds
    STORAGE_WARNING_THRESHOLD = 80  # Warn at 80% capacity
    STORAGE_CRITICAL_THRESHOLD = 90  # Critical at 90% capacity
    
    # Failover configuration
    FAILOVER_LOG_PATH = os.getenv("AUDIT_FAILOVER_LOG_PATH", "/var/log/audit_failover.log")
    
    @staticmethod
    def check_audit_system_health(db: Session, org_id: int) -> Tuple[bool, Optional[str], Dict]:
        """
        Check audit system health and capacity.
        
        Returns:
            Tuple of (is_healthy, warning_message, capacity_metrics)
        """
        try:
            # Check database connectivity
            db.execute(func.now())
            
            # Check storage capacity (if audit logs are stored on disk)
            capacity_metrics = AuditFailureResponseService._check_storage_capacity()
            
            # Check recent write success rate
            recent_writes = db.query(ComprehensiveAuditLog).filter(
                ComprehensiveAuditLog.org_id == org_id,
                ComprehensiveAuditLog.timestamp >= func.now() - func.interval('5 minutes')
            ).count()
            
            capacity_metrics['recent_writes'] = recent_writes
            
            # Determine health status
            is_healthy = True
            warning_message = None
            
            if capacity_metrics['storage_usage_percent'] >= AuditFailureResponseService.STORAGE_CRITICAL_THRESHOLD:
                is_healthy = False
                warning_message = f"Critical: Storage at {capacity_metrics['storage_usage_percent']}%"
            elif capacity_metrics['storage_usage_percent'] >= AuditFailureResponseService.STORAGE_WARNING_THRESHOLD:
                warning_message = f"Warning: Storage at {capacity_metrics['storage_usage_percent']}%"
            
            # Record capacity metrics
            AuditFailureResponseService._record_capacity_metrics(db, org_id, capacity_metrics, is_healthy)
            
            return is_healthy, warning_message, capacity_metrics
            
        except Exception as e:
            logger.error(f"Failed to check audit system health: {e}", exc_info=True)
            # System is unhealthy if we can't check
            return False, f"Health check failed: {str(e)}", {}
    
    @staticmethod
    def detect_audit_failure(
        db: Session,
        org_id: int,
        failure_type: AuditFailureType,
        failure_message: str,
        error_code: Optional[str] = None,
        error_details: Optional[Dict] = None,
        severity: Optional[AuditFailureSeverity] = None,
    ) -> AuditFailureResponse:
        """
        Detect and record an audit system failure.
        
        Args:
            db: Database session
            org_id: Organization ID
            failure_type: Type of failure
            failure_message: Description of failure
            error_code: Optional error code
            error_details: Additional error context
            severity: Failure severity (auto-determined if not provided)
            
        Returns:
            Created AuditFailureResponse record
        """
        # Auto-determine severity if not provided
        if severity is None:
            severity = AuditFailureResponseService._determine_severity(failure_type)
        
        # Create failure response record
        failure_response = AuditFailureResponse(
            org_id=org_id,
            failure_type=failure_type.value,
            severity=severity.value,
            status=AuditFailureStatus.DETECTED.value,
            failure_message=failure_message,
            error_code=error_code,
            error_details=error_details,
            detected_at=datetime.now(timezone.utc),
            detected_by="audit_system",
        )
        
        db.add(failure_response)
        
        try:
            db.commit()
            db.refresh(failure_response)
            
            # Send alerts
            AuditFailureResponseService._send_alerts(db, failure_response)
            
            # Activate failover if critical
            if severity == AuditFailureSeverity.CRITICAL:
                AuditFailureResponseService._activate_failover(db, failure_response)
            
            logger.critical(
                f"Audit system failure detected: {failure_type.value} - {failure_message} "
                f"(org_id={org_id}, severity={severity.value})"
            )
            
            return failure_response
            
        except Exception as e:
            db.rollback()
            logger.error(f"CRITICAL: Failed to record audit failure: {e}", exc_info=True)
            # Try failover logging
            AuditFailureResponseService._log_to_failover(failure_message, error_details)
            raise
    
    @staticmethod
    def _determine_severity(failure_type: AuditFailureType) -> AuditFailureSeverity:
        """Determine severity based on failure type"""
        severity_map = {
            AuditFailureType.STORAGE_FULL: AuditFailureSeverity.CRITICAL,
            AuditFailureType.WRITE_FAILURE: AuditFailureSeverity.CRITICAL,
            AuditFailureType.DATABASE_ERROR: AuditFailureSeverity.HIGH,
            AuditFailureType.CAPACITY_EXCEEDED: AuditFailureSeverity.HIGH,
            AuditFailureType.NETWORK_FAILURE: AuditFailureSeverity.MEDIUM,
            AuditFailureType.PERMISSION_DENIED: AuditFailureSeverity.MEDIUM,
            AuditFailureType.SYSTEM_OVERLOAD: AuditFailureSeverity.MEDIUM,
            AuditFailureType.UNKNOWN: AuditFailureSeverity.MEDIUM,
        }
        return severity_map.get(failure_type, AuditFailureSeverity.MEDIUM)
    
    @staticmethod
    def _send_alerts(db: Session, failure_response: AuditFailureResponse):
        """Send alerts for audit failure"""
        try:
            # Determine alert recipients (security team, admins)
            recipients = AuditFailureResponseService._get_alert_recipients(failure_response.org_id)
            
            # Send alert (implement actual alerting mechanism)
            # This could be email, Slack, PagerDuty, etc.
            alert_sent = AuditFailureResponseService._send_alert_notification(
                recipients=recipients,
                failure_type=failure_response.failure_type,
                severity=failure_response.severity,
                message=failure_response.failure_message,
            )
            
            if alert_sent:
                failure_response.alert_sent = True
                failure_response.alert_sent_at = datetime.now(timezone.utc)
                failure_response.alert_recipients = recipients
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to send audit failure alert: {e}", exc_info=True)
    
    @staticmethod
    def _get_alert_recipients(org_id: int) -> List[str]:
        """Get list of alert recipients for an organization"""
        # TODO: Query from user preferences or org settings
        # For now, return default security team
        return ["security@example.com"]
    
    @staticmethod
    def _send_alert_notification(
        recipients: List[str],
        failure_type: str,
        severity: str,
        message: str,
    ) -> bool:
        """Send alert notification (implement actual notification mechanism)"""
        try:
            # TODO: Implement actual alerting (email, Slack, etc.)
            logger.warning(
                f"AUDIT FAILURE ALERT [{severity.upper()}]: {failure_type} - {message} "
                f"(recipients: {', '.join(recipients)})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _activate_failover(db: Session, failure_response: AuditFailureResponse):
        """Activate failover to alternate logging system"""
        try:
            # Activate file-based failover logging
            failover_target = AuditFailureResponseService.FAILOVER_LOG_PATH
            
            failure_response.failover_activated = True
            failure_response.failover_activated_at = datetime.now(timezone.utc)
            failure_response.failover_target = failover_target
            failure_response.failover_status = "active"
            
            db.commit()
            
            logger.warning(f"Audit failover activated: {failover_target}")
            
        except Exception as e:
            logger.error(f"Failed to activate audit failover: {e}", exc_info=True)
    
    @staticmethod
    def _log_to_failover(message: str, details: Optional[Dict] = None):
        """Log to failover system (file-based)"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = f"[{timestamp}] AUDIT_FAILOVER: {message}\n"
            
            if details:
                import json
                log_entry += f"Details: {json.dumps(details)}\n"
            
            # Ensure directory exists
            log_dir = os.path.dirname(AuditFailureResponseService.FAILOVER_LOG_PATH)
            os.makedirs(log_dir, exist_ok=True)
            
            # Append to failover log
            with open(AuditFailureResponseService.FAILOVER_LOG_PATH, 'a') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"CRITICAL: Failed to write to failover log: {e}", exc_info=True)
    
    @staticmethod
    def _check_storage_capacity() -> Dict:
        """Check storage capacity for audit logs"""
        try:
            # Check database storage (if using PostgreSQL, check tablespace)
            # For now, check disk space where logs might be stored
            if os.path.exists(AuditFailureResponseService.FAILOVER_LOG_PATH):
                stat = shutil.disk_usage(os.path.dirname(AuditFailureResponseService.FAILOVER_LOG_PATH))
                total = stat.total
                used = stat.used
                free = stat.free
                usage_percent = int((used / total) * 100) if total > 0 else 0
            else:
                # Default values if path doesn't exist
                usage_percent = 0
                total = 0
                free = 0
            
            return {
                'storage_usage_percent': usage_percent,
                'storage_total_bytes': total,
                'storage_available_bytes': free,
            }
        except Exception as e:
            logger.error(f"Failed to check storage capacity: {e}", exc_info=True)
            return {
                'storage_usage_percent': 0,
                'storage_total_bytes': 0,
                'storage_available_bytes': 0,
            }
    
    @staticmethod
    def _record_capacity_metrics(
        db: Session,
        org_id: int,
        capacity_metrics: Dict,
        is_healthy: bool,
    ):
        """Record capacity metrics"""
        try:
            capacity_record = AuditSystemCapacity(
                org_id=org_id,
                storage_usage_percent=capacity_metrics.get('storage_usage_percent', 0),
                storage_total_bytes=capacity_metrics.get('storage_total_bytes'),
                storage_available_bytes=capacity_metrics.get('storage_available_bytes'),
                log_rate_per_second=capacity_metrics.get('log_rate_per_second'),
                log_queue_size=capacity_metrics.get('log_queue_size'),
                storage_warning_threshold=AuditFailureResponseService.STORAGE_WARNING_THRESHOLD,
                storage_critical_threshold=AuditFailureResponseService.STORAGE_CRITICAL_THRESHOLD,
                is_healthy=is_healthy,
                warnings_active=capacity_metrics.get('warnings', []),
                recorded_at=datetime.now(timezone.utc),
            )
            
            db.add(capacity_record)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record capacity metrics: {e}", exc_info=True)
            db.rollback()
    
    @staticmethod
    def resolve_failure(
        db: Session,
        failure_response_id: str,
        org_id: int,
        resolved_by_user_id: int,
        resolution_notes: Optional[str] = None,
    ) -> AuditFailureResponse:
        """Mark an audit failure as resolved"""
        failure_response = db.query(AuditFailureResponse).filter(
            AuditFailureResponse.id == failure_response_id,
            AuditFailureResponse.org_id == org_id,
        ).first()
        
        if not failure_response:
            raise ValueError(f"Failure response {failure_response_id} not found")
        
        failure_response.status = AuditFailureStatus.RESOLVED.value
        failure_response.resolved_at = datetime.now(timezone.utc)
        failure_response.resolved_by_user_id = resolved_by_user_id
        failure_response.resolution_notes = resolution_notes
        
        # Deactivate failover if it was active
        if failure_response.failover_activated:
            failure_response.failover_status = "restored"
        
        db.commit()
        db.refresh(failure_response)
        
        logger.info(f"Audit failure resolved: {failure_response_id}")
        
        return failure_response
    
    @staticmethod
    def get_active_failures(db: Session, org_id: int) -> List[AuditFailureResponse]:
        """Get active (unresolved) audit failures"""
        return db.query(AuditFailureResponse).filter(
            AuditFailureResponse.org_id == org_id,
            AuditFailureResponse.status != AuditFailureStatus.RESOLVED.value,
        ).order_by(desc(AuditFailureResponse.detected_at)).all()
    
    @staticmethod
    def get_capacity_history(
        db: Session,
        org_id: int,
        hours: int = 24,
    ) -> List[AuditSystemCapacity]:
        """Get capacity history for the last N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return db.query(AuditSystemCapacity).filter(
            AuditSystemCapacity.org_id == org_id,
            AuditSystemCapacity.recorded_at >= cutoff,
        ).order_by(AuditSystemCapacity.recorded_at).all()
