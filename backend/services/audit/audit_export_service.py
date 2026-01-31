"""
Audit Export Service for Compliance Reporting

This service provides functionality to export audit logs for compliance
reporting, including:
- FedRAMP compliance reports
- Security incident investigations
- Access reviews
- Regulatory audits

Exports are provided in multiple formats (CSV, JSON) and can be filtered
by date range, user, event type, outcome, etc.
"""
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.comprehensive_audit_log import (
    ComprehensiveAuditLog,
    AuditEventType,
    AuditOutcome,
)


class AuditExportService:
    """Service for exporting audit logs for compliance reporting"""

    @staticmethod
    def query_audit_logs(
        db: Session,
        org_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        outcome: Optional[AuditOutcome] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 10000,
        offset: int = 0,
    ) -> List[ComprehensiveAuditLog]:
        """
        Query audit logs with various filters.
        
        Returns audit logs matching the specified criteria, ordered by timestamp descending.
        """
        query = db.query(ComprehensiveAuditLog)
        
        # Apply filters
        filters = []
        
        if org_id is not None:
            filters.append(ComprehensiveAuditLog.org_id == org_id)
        
        if user_id is not None:
            filters.append(ComprehensiveAuditLog.user_id == user_id)
        
        if user_email is not None:
            filters.append(ComprehensiveAuditLog.user_email == user_email)
        
        if event_type is not None:
            filters.append(ComprehensiveAuditLog.event_type == event_type.value)
        
        if outcome is not None:
            filters.append(ComprehensiveAuditLog.outcome == outcome.value)
        
        if resource_type is not None:
            filters.append(ComprehensiveAuditLog.resource_type == resource_type)
        
        if start_date is not None:
            filters.append(ComprehensiveAuditLog.timestamp >= start_date)
        
        if end_date is not None:
            filters.append(ComprehensiveAuditLog.timestamp <= end_date)
        
        if action is not None:
            filters.append(ComprehensiveAuditLog.action.like(f"%{action}%"))
        
        if ip_address is not None:
            filters.append(ComprehensiveAuditLog.ip_address == ip_address)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(ComprehensiveAuditLog.timestamp.desc())
        
        # Apply limit and offset
        query = query.limit(limit).offset(offset)
        
        return query.all()

    @staticmethod
    def count_audit_logs(
        db: Session,
        org_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        outcome: Optional[AuditOutcome] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """Count audit logs matching the specified criteria"""
        query = db.query(ComprehensiveAuditLog)
        
        # Apply same filters as query_audit_logs
        filters = []
        
        if org_id is not None:
            filters.append(ComprehensiveAuditLog.org_id == org_id)
        
        if user_id is not None:
            filters.append(ComprehensiveAuditLog.user_id == user_id)
        
        if user_email is not None:
            filters.append(ComprehensiveAuditLog.user_email == user_email)
        
        if event_type is not None:
            filters.append(ComprehensiveAuditLog.event_type == event_type.value)
        
        if outcome is not None:
            filters.append(ComprehensiveAuditLog.outcome == outcome.value)
        
        if resource_type is not None:
            filters.append(ComprehensiveAuditLog.resource_type == resource_type)
        
        if start_date is not None:
            filters.append(ComprehensiveAuditLog.timestamp >= start_date)
        
        if end_date is not None:
            filters.append(ComprehensiveAuditLog.timestamp <= end_date)
        
        if action is not None:
            filters.append(ComprehensiveAuditLog.action.like(f"%{action}%"))
        
        if ip_address is not None:
            filters.append(ComprehensiveAuditLog.ip_address == ip_address)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.count()

    @staticmethod
    def export_to_csv(
        db: Session,
        org_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> str:
        """
        Export audit logs to CSV format.
        
        Returns CSV string with all audit log fields.
        """
        logs = AuditExportService.query_audit_logs(
            db=db,
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            limit=100000,  # Large limit for exports
            **kwargs,
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID",
            "Timestamp",
            "Organization ID",
            "User ID",
            "User Email",
            "User Role",
            "Event Type",
            "Action",
            "Resource Type",
            "Resource ID",
            "Outcome",
            "IP Address",
            "User Agent",
            "Request Method",
            "Request Path",
            "Session ID",
            "Device ID",
            "Classification",
            "Training Mode",
            "Error Message",
            "Error Code",
            "Reason Code",
            "Decision ID",
        ])
        
        # Write data rows
        for log in logs:
            writer.writerow([
                str(log.id),
                log.timestamp.isoformat() if log.timestamp else "",
                log.org_id,
                log.user_id,
                log.user_email,
                log.user_role,
                log.event_type,
                log.action,
                log.resource_type,
                log.resource_id,
                log.outcome,
                log.ip_address,
                log.user_agent,
                log.request_method,
                log.request_path,
                log.session_id,
                log.device_id,
                log.classification,
                log.training_mode,
                log.error_message,
                log.error_code,
                log.reason_code,
                log.decision_id,
            ])
        
        return output.getvalue()

    @staticmethod
    def export_to_json(
        db: Session,
        org_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Export audit logs to JSON format.
        
        Returns list of dictionaries with audit log data.
        """
        import json
        
        logs = AuditExportService.query_audit_logs(
            db=db,
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            limit=100000,  # Large limit for exports
            **kwargs,
        )
        
        result = []
        for log in logs:
            result.append({
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "org_id": log.org_id,
                "user_id": log.user_id,
                "user_email": log.user_email,
                "user_role": log.user_role,
                "event_type": log.event_type,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "outcome": log.outcome,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "request_query": log.request_query,
                "session_id": log.session_id,
                "device_id": log.device_id,
                "device_fingerprint": log.device_fingerprint,
                "classification": log.classification,
                "training_mode": log.training_mode,
                "before_state": log.before_state,
                "after_state": log.after_state,
                "error_message": log.error_message,
                "error_code": log.error_code,
                "reason_code": log.reason_code,
                "decision_id": log.decision_id,
                "metadata": log.metadata,
            })
        
        return result

    @staticmethod
    def get_fedramp_compliance_report(
        db: Session,
        org_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Generate a FedRAMP compliance report.
        
        Returns summary statistics and key metrics for FedRAMP AU-2, AU-3, AU-9 compliance.
        """
        # Get all logs for the date range
        logs = AuditExportService.query_audit_logs(
            db=db,
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000000,  # Very large limit for compliance reports
        )
        
        # Calculate statistics
        total_events = len(logs)
        
        event_type_counts = {}
        outcome_counts = {}
        user_counts = {}
        ip_address_counts = {}
        
        authentication_events = []
        authorization_denials = []
        security_events = []
        
        for log in logs:
            # Count by event type
            event_type_counts[log.event_type] = event_type_counts.get(log.event_type, 0) + 1
            
            # Count by outcome
            outcome_counts[log.outcome] = outcome_counts.get(log.outcome, 0) + 1
            
            # Count by user
            if log.user_email:
                user_counts[log.user_email] = user_counts.get(log.user_email, 0) + 1
            
            # Count by IP address
            if log.ip_address:
                ip_address_counts[log.ip_address] = ip_address_counts.get(log.ip_address, 0) + 1
            
            # Collect authentication events
            if log.event_type == AuditEventType.AUTHENTICATION.value:
                authentication_events.append({
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "user_email": log.user_email,
                    "action": log.action,
                    "outcome": log.outcome,
                    "ip_address": log.ip_address,
                })
            
            # Collect authorization denials
            if log.event_type == AuditEventType.AUTHORIZATION.value and log.outcome == AuditOutcome.DENIED.value:
                authorization_denials.append({
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "user_email": log.user_email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "reason_code": log.reason_code,
                })
            
            # Collect security events
            if log.event_type == AuditEventType.SECURITY_EVENT.value:
                security_events.append({
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "user_email": log.user_email,
                    "action": log.action,
                    "outcome": log.outcome,
                    "error_message": log.error_message,
                })
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_events": total_events,
                "event_type_counts": event_type_counts,
                "outcome_counts": outcome_counts,
                "unique_users": len(user_counts),
                "unique_ip_addresses": len(ip_address_counts),
            },
            "authentication_events": {
                "total": len(authentication_events),
                "events": authentication_events[:100],  # Limit to first 100 for report
            },
            "authorization_denials": {
                "total": len(authorization_denials),
                "events": authorization_denials[:100],  # Limit to first 100 for report
            },
            "security_events": {
                "total": len(security_events),
                "events": security_events[:100],  # Limit to first 100 for report
            },
            "top_users": sorted(
                user_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20],  # Top 20 users
            "top_ip_addresses": sorted(
                ip_address_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20],  # Top 20 IP addresses
        }
