"""
Audit Reduction Service for FedRAMP AU-7 Compliance

FedRAMP Requirement AU-7: Audit Reduction and Report Generation
- Automated log analysis
- Pattern detection
- Report generation
- Query optimization
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

from core.logger import logger
from models.audit_reduction import (
    AuditReductionReport,
    AuditPattern,
    AuditQueryOptimization,
    ReportType,
    ReportStatus,
    PatternType,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class AuditReductionService:
    """
    Service for audit reduction and report generation (AU-7).
    """
    
    @staticmethod
    def generate_report(
        db: Session,
        org_id: int,
        report_name: str,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        query_filters: Optional[Dict] = None,
        created_by_user_id: Optional[int] = None,
        created_by_email: Optional[str] = None,
    ) -> AuditReductionReport:
        """
        Generate an audit reduction report.
        
        Args:
            db: Database session
            org_id: Organization ID
            report_name: Name of the report
            report_type: Type of report
            period_start: Start of report period
            period_end: End of report period
            query_filters: Optional filters to apply
            created_by_user_id: User creating the report
            created_by_email: User email (denormalized)
            
        Returns:
            Created AuditReductionReport
        """
        report = AuditReductionReport(
            org_id=org_id,
            report_name=report_name,
            report_type=report_type.value,
            period_start=period_start,
            period_end=period_end,
            status=ReportStatus.GENERATING.value,
            query_filters=query_filters,
            created_by_user_id=created_by_user_id,
            created_by_email=created_by_email,
            generation_started_at=datetime.now(timezone.utc),
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        try:
            # Generate report content
            start_time = time.time()
            report_content = AuditReductionService._generate_report_content(
                db, org_id, report_type, period_start, period_end, query_filters
            )
            generation_duration = int((time.time() - start_time) * 1000)
            
            # Update report with results
            report.status = ReportStatus.COMPLETED.value
            report.generation_completed_at = datetime.now(timezone.utc)
            report.generation_duration_seconds = generation_duration // 1000
            report.report_content = report_content
            report.summary_statistics = report_content.get('summary_statistics', {})
            report.detected_patterns = report_content.get('detected_patterns', [])
            report.findings = report_content.get('findings', [])
            report.recommendations = report_content.get('recommendations', [])
            report.events_analyzed = report_content.get('events_analyzed', 0)
            report.report_format = 'json'
            
            db.commit()
            db.refresh(report)
            
            logger.info(
                f"Generated audit report: {report_name} "
                f"(type={report_type.value}, events={report.events_analyzed}, "
                f"duration={generation_duration}ms)"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}", exc_info=True)
            report.status = ReportStatus.FAILED.value
            report.error_message = str(e)
            report.error_details = {'exception_type': type(e).__name__}
            db.commit()
            raise
    
    @staticmethod
    def _generate_report_content(
        db: Session,
        org_id: int,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        query_filters: Optional[Dict] = None,
    ) -> Dict:
        """Generate report content based on type"""
        # Build base query
        query = db.query(ComprehensiveAuditLog).filter(
            ComprehensiveAuditLog.org_id == org_id,
            ComprehensiveAuditLog.timestamp >= period_start,
            ComprehensiveAuditLog.timestamp <= period_end,
        )
        
        # Apply filters
        if query_filters:
            if 'event_type' in query_filters:
                query = query.filter(ComprehensiveAuditLog.event_type == query_filters['event_type'])
            if 'outcome' in query_filters:
                query = query.filter(ComprehensiveAuditLog.outcome == query_filters['outcome'])
            if 'user_id' in query_filters:
                query = query.filter(ComprehensiveAuditLog.user_id == query_filters['user_id'])
            if 'resource_type' in query_filters:
                query = query.filter(ComprehensiveAuditLog.resource_type == query_filters['resource_type'])
        
        # Execute query and get events
        events = query.all()
        events_analyzed = len(events)
        
        # Generate content based on report type
        if report_type == ReportType.SUMMARY:
            return AuditReductionService._generate_summary_report(events)
        elif report_type == ReportType.COMPLIANCE:
            return AuditReductionService._generate_compliance_report(events)
        elif report_type == ReportType.SECURITY_INCIDENT:
            return AuditReductionService._generate_security_incident_report(events)
        elif report_type == ReportType.USER_ACTIVITY:
            return AuditReductionService._generate_user_activity_report(events)
        elif report_type == ReportType.DATA_ACCESS:
            return AuditReductionService._generate_data_access_report(events)
        elif report_type == ReportType.CONFIGURATION_CHANGE:
            return AuditReductionService._generate_configuration_change_report(events)
        else:
            return AuditReductionService._generate_custom_report(events, query_filters)
    
    @staticmethod
    def _generate_summary_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate summary report"""
        summary_stats = {
            'total_events': len(events),
            'by_event_type': {},
            'by_outcome': {},
            'by_hour': {},
            'unique_users': len(set(e.user_id for e in events if e.user_id)),
            'unique_resources': len(set(e.resource_type for e in events)),
        }
        
        for event in events:
            # Count by event type
            summary_stats['by_event_type'][event.event_type] = \
                summary_stats['by_event_type'].get(event.event_type, 0) + 1
            
            # Count by outcome
            summary_stats['by_outcome'][event.outcome] = \
                summary_stats['by_outcome'].get(event.outcome, 0) + 1
            
            # Count by hour
            hour = event.timestamp.hour
            summary_stats['by_hour'][hour] = summary_stats['by_hour'].get(hour, 0) + 1
        
        # Detect patterns
        patterns = AuditReductionService._detect_patterns(events)
        
        # Generate findings
        findings = []
        if summary_stats['by_outcome'].get('failure', 0) > 0:
            findings.append({
                'type': 'high_failure_rate',
                'severity': 'medium',
                'description': f"Found {summary_stats['by_outcome'].get('failure', 0)} failed events",
            })
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': patterns,
            'findings': findings,
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_compliance_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate compliance-focused report"""
        compliance_events = [e for e in events if e.classification in ['PHI', 'PII']]
        
        summary_stats = {
            'total_events': len(events),
            'compliance_events': len(compliance_events),
            'phi_access': len([e for e in compliance_events if e.classification == 'PHI']),
            'pii_access': len([e for e in compliance_events if e.classification == 'PII']),
        }
        
        findings = []
        if summary_stats['phi_access'] > 0:
            findings.append({
                'type': 'phi_access_detected',
                'severity': 'high',
                'description': f"PHI access detected: {summary_stats['phi_access']} events",
            })
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': [],
            'findings': findings,
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_security_incident_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate security incident report"""
        security_events = [e for e in events if e.event_type == AuditEventType.SECURITY_EVENT.value]
        failed_auth = [e for e in events if e.event_type == AuditEventType.AUTHENTICATION.value and e.outcome == AuditOutcome.FAILURE.value]
        
        summary_stats = {
            'total_events': len(events),
            'security_events': len(security_events),
            'failed_authentications': len(failed_auth),
        }
        
        patterns = AuditReductionService._detect_security_patterns(events)
        
        findings = []
        if len(failed_auth) > 10:
            findings.append({
                'type': 'excessive_failed_auth',
                'severity': 'high',
                'description': f"Excessive failed authentication attempts: {len(failed_auth)}",
            })
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': patterns,
            'findings': findings,
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_user_activity_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate user activity report"""
        user_activity = {}
        for event in events:
            if event.user_id:
                user_id = str(event.user_id)
                if user_id not in user_activity:
                    user_activity[user_id] = {
                        'user_id': user_id,
                        'user_email': event.user_email,
                        'event_count': 0,
                        'actions': [],
                    }
                user_activity[user_id]['event_count'] += 1
                user_activity[user_id]['actions'].append(event.action)
        
        summary_stats = {
            'total_events': len(events),
            'unique_users': len(user_activity),
            'user_activity': list(user_activity.values())[:100],  # Limit to top 100
        }
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': [],
            'findings': [],
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_data_access_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate data access report"""
        access_events = [e for e in events if e.event_type == AuditEventType.DATA_ACCESS.value]
        
        summary_stats = {
            'total_events': len(events),
            'data_access_events': len(access_events),
            'by_resource_type': {},
        }
        
        for event in access_events:
            summary_stats['by_resource_type'][event.resource_type] = \
                summary_stats['by_resource_type'].get(event.resource_type, 0) + 1
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': [],
            'findings': [],
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_configuration_change_report(events: List[ComprehensiveAuditLog]) -> Dict:
        """Generate configuration change report"""
        config_events = [e for e in events if e.event_type == AuditEventType.CONFIGURATION_CHANGE.value]
        
        summary_stats = {
            'total_events': len(events),
            'configuration_changes': len(config_events),
        }
        
        return {
            'events_analyzed': len(events),
            'summary_statistics': summary_stats,
            'detected_patterns': [],
            'findings': [],
            'recommendations': [],
        }
    
    @staticmethod
    def _generate_custom_report(events: List[ComprehensiveAuditLog], filters: Optional[Dict]) -> Dict:
        """Generate custom report"""
        return {
            'events_analyzed': len(events),
            'summary_statistics': {'total_events': len(events)},
            'detected_patterns': [],
            'findings': [],
            'recommendations': [],
        }
    
    @staticmethod
    def _detect_patterns(events: List[ComprehensiveAuditLog]) -> List[Dict]:
        """Detect patterns in audit events"""
        patterns = []
        
        # Detect failed authentication pattern
        failed_auth = [e for e in events if e.event_type == AuditEventType.AUTHENTICATION.value and e.outcome == AuditOutcome.FAILURE.value]
        if len(failed_auth) > 5:
            patterns.append({
                'type': PatternType.FAILED_AUTHENTICATION.value,
                'name': 'Multiple Failed Authentication Attempts',
                'match_count': len(failed_auth),
                'severity': 'medium',
            })
        
        return patterns
    
    @staticmethod
    def _detect_security_patterns(events: List[ComprehensiveAuditLog]) -> List[Dict]:
        """Detect security-related patterns"""
        patterns = []
        
        # Group by IP address
        ip_activity = {}
        for event in events:
            if event.ip_address:
                ip_activity[event.ip_address] = ip_activity.get(event.ip_address, 0) + 1
        
        # Detect anomalous IP activity
        for ip, count in ip_activity.items():
            if count > 100:  # Threshold for anomalous activity
                patterns.append({
                    'type': PatternType.ANOMALOUS_ACCESS.value,
                    'name': f'Anomalous Activity from IP: {ip}',
                    'match_count': count,
                    'severity': 'high',
                })
        
        return patterns
    
    @staticmethod
    def detect_and_record_pattern(
        db: Session,
        org_id: int,
        pattern_type: PatternType,
        pattern_name: str,
        pattern_definition: Dict,
        matched_events: List[str],
        severity: str = 'medium',
        risk_score: Optional[int] = None,
    ) -> AuditPattern:
        """Detect and record a pattern"""
        pattern = AuditPattern(
            org_id=org_id,
            pattern_type=pattern_type.value,
            pattern_name=pattern_name,
            pattern_definition=pattern_definition,
            matched_events=matched_events,
            match_count=len(matched_events),
            severity=severity,
            risk_score=risk_score,
            detected_at=datetime.now(timezone.utc),
            detected_by='audit_reduction_service',
            is_active=True,
        )
        
        db.add(pattern)
        db.commit()
        db.refresh(pattern)
        
        logger.info(f"Detected audit pattern: {pattern_name} (matches={len(matched_events)})")
        
        return pattern
    
    @staticmethod
    def record_query_optimization(
        db: Session,
        org_id: int,
        query_type: str,
        execution_time_ms: int,
        events_scanned: Optional[int] = None,
        events_returned: Optional[int] = None,
        optimization_applied: Optional[Dict] = None,
    ) -> AuditQueryOptimization:
        """Record query optimization metrics"""
        optimization = AuditQueryOptimization(
            org_id=org_id,
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            events_scanned=events_scanned,
            events_returned=events_returned,
            optimization_applied=optimization_applied,
            recorded_at=datetime.now(timezone.utc),
        )
        
        db.add(optimization)
        db.commit()
        db.refresh(optimization)
        
        return optimization
    
    @staticmethod
    def get_reports(
        db: Session,
        org_id: int,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditReductionReport]:
        """Get audit reduction reports"""
        query = db.query(AuditReductionReport).filter(
            AuditReductionReport.org_id == org_id
        )
        
        if report_type:
            query = query.filter(AuditReductionReport.report_type == report_type)
        if status:
            query = query.filter(AuditReductionReport.status == status)
        
        return query.order_by(desc(AuditReductionReport.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_active_patterns(
        db: Session,
        org_id: int,
        pattern_type: Optional[str] = None,
    ) -> List[AuditPattern]:
        """Get active patterns"""
        query = db.query(AuditPattern).filter(
            AuditPattern.org_id == org_id,
            AuditPattern.is_active == True,
        )
        
        if pattern_type:
            query = query.filter(AuditPattern.pattern_type == pattern_type)
        
        return query.order_by(desc(AuditPattern.detected_at)).all()
