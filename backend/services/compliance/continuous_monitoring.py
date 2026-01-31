"""
Continuous Monitoring Service
FedRAMP Continuous Monitoring (ConMon) Requirements

Implements ongoing security assessment and compliance monitoring
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.logger import logger
from models.comprehensive_audit_log import ComprehensiveAuditLog
from models.mfa import MFAAttempt
from models.account_lockout import AccountLockout
from models.user import User


class ContinuousMonitoringService:
    """
    FedRAMP Continuous Monitoring Service
    Tracks compliance posture in real-time
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_security_dashboard(self, org_id: Optional[int] = None) -> Dict:
        """
        Generate FedRAMP continuous monitoring dashboard
        
        Returns real-time security metrics required for ConMon reporting
        """
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Build query filters
        filters = []
        if org_id:
            filters.append(ComprehensiveAuditLog.org_id == org_id)
        
        # Authentication Events (IA-2)
        auth_events_24h = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "authentication",
            ComprehensiveAuditLog.timestamp >= last_24h,
            *filters
        ).scalar() or 0
        
        auth_failures_24h = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "authentication",
            ComprehensiveAuditLog.outcome == "failure",
            ComprehensiveAuditLog.timestamp >= last_24h,
            *filters
        ).scalar() or 0
        
        # Account Lockouts (AC-7)
        active_lockouts = self.db.query(func.count(AccountLockout.id)).filter(
            AccountLockout.locked_until > now,
            *([AccountLockout.org_id == org_id] if org_id else [])
        ).scalar() or 0
        
        # MFA Verification (IA-2(1))
        if org_id:
            mfa_attempts_24h = self.db.query(func.count(MFAAttempt.id)).filter(
                MFAAttempt.attempted_at >= last_24h
            ).scalar() or 0
            
            mfa_failures_24h = self.db.query(func.count(MFAAttempt.id)).filter(
                MFAAttempt.attempted_at >= last_24h,
                MFAAttempt.success == False
            ).scalar() or 0
        else:
            mfa_attempts_24h = 0
            mfa_failures_24h = 0
        
        # Authorization Events (AC-3)
        authz_denials_24h = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "authorization",
            ComprehensiveAuditLog.outcome == "denied",
            ComprehensiveAuditLog.timestamp >= last_24h,
            *filters
        ).scalar() or 0
        
        # Data Access Events (AU-2)
        data_access_24h = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "data_access",
            ComprehensiveAuditLog.timestamp >= last_24h,
            *filters
        ).scalar() or 0
        
        # Configuration Changes (CM-3)
        config_changes_7d = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "configuration_change",
            ComprehensiveAuditLog.timestamp >= last_7d,
            *filters
        ).scalar() or 0
        
        # Security Events (SI-4)
        security_events_7d = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.event_type == "security_event",
            ComprehensiveAuditLog.timestamp >= last_7d,
            *filters
        ).scalar() or 0
        
        # Active Users (AC-2)
        active_users_30d = self.db.query(func.count(func.distinct(ComprehensiveAuditLog.user_id))).filter(
            ComprehensiveAuditLog.timestamp >= last_30d,
            *filters
        ).scalar() or 0
        
        return {
            "timestamp": now.isoformat(),
            "period": "24_hours",
            "authentication": {
                "total_attempts": auth_events_24h,
                "failed_attempts": auth_failures_24h,
                "success_rate": round((auth_events_24h - auth_failures_24h) / auth_events_24h * 100, 2) if auth_events_24h > 0 else 100,
                "active_lockouts": active_lockouts
            },
            "mfa": {
                "total_verifications": mfa_attempts_24h,
                "failed_verifications": mfa_failures_24h,
                "success_rate": round((mfa_attempts_24h - mfa_failures_24h) / mfa_attempts_24h * 100, 2) if mfa_attempts_24h > 0 else 100
            },
            "authorization": {
                "denials_24h": authz_denials_24h
            },
            "data_access": {
                "total_access_events": data_access_24h
            },
            "configuration": {
                "changes_7d": config_changes_7d
            },
            "security": {
                "security_events_7d": security_events_7d
            },
            "users": {
                "active_users_30d": active_users_30d
            }
        }
    
    def generate_conmon_report(self, start_date: datetime, end_date: datetime, org_id: Optional[int] = None) -> Dict:
        """
        Generate FedRAMP Continuous Monitoring Monthly Report
        
        Required monthly for FedRAMP ConMon
        """
        filters = []
        if org_id:
            filters.append(ComprehensiveAuditLog.org_id == org_id)
        
        # Authentication metrics
        auth_metrics = self._get_auth_metrics(start_date, end_date, filters)
        
        # Authorization metrics
        authz_metrics = self._get_authz_metrics(start_date, end_date, filters)
        
        # Security events
        security_metrics = self._get_security_metrics(start_date, end_date, filters)
        
        # Configuration changes
        config_metrics = self._get_config_metrics(start_date, end_date, filters)
        
        # Incidents (if incident model available)
        incident_metrics = self._get_incident_metrics(start_date, end_date, org_id)
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "authentication_security": auth_metrics,
            "authorization_security": authz_metrics,
            "security_events": security_metrics,
            "configuration_management": config_metrics,
            "incident_response": incident_metrics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "compliance_status": "COMPLIANT"  # TODO: Calculate based on findings
        }
    
    def _get_auth_metrics(self, start: datetime, end: datetime, filters: List) -> Dict:
        """Get authentication metrics for period"""
        base_query = self.db.query(ComprehensiveAuditLog).filter(
            ComprehensiveAuditLog.event_type == "authentication",
            ComprehensiveAuditLog.timestamp >= start,
            ComprehensiveAuditLog.timestamp <= end,
            *filters
        )
        
        total = base_query.count()
        failures = base_query.filter(ComprehensiveAuditLog.outcome == "failure").count()
        
        return {
            "total_attempts": total,
            "successful": total - failures,
            "failed": failures,
            "success_rate_percent": round((total - failures) / total * 100, 2) if total > 0 else 100
        }
    
    def _get_authz_metrics(self, start: datetime, end: datetime, filters: List) -> Dict:
        """Get authorization metrics"""
        base_query = self.db.query(ComprehensiveAuditLog).filter(
            ComprehensiveAuditLog.event_type == "authorization",
            ComprehensiveAuditLog.timestamp >= start,
            ComprehensiveAuditLog.timestamp <= end,
            *filters
        )
        
        denials = base_query.filter(ComprehensiveAuditLog.outcome == "denied").count()
        
        return {
            "total_checks": base_query.count(),
            "denials": denials
        }
    
    def _get_security_metrics(self, start: datetime, end: datetime, filters: List) -> Dict:
        """Get security event metrics"""
        security_events = self.db.query(ComprehensiveAuditLog).filter(
            ComprehensiveAuditLog.event_type == "security_event",
            ComprehensiveAuditLog.timestamp >= start,
            ComprehensiveAuditLog.timestamp <= end,
            *filters
        ).count()
        
        return {
            "total_security_events": security_events
        }
    
    def _get_config_metrics(self, start: datetime, end: datetime, filters: List) -> Dict:
        """Get configuration change metrics"""
        config_changes = self.db.query(ComprehensiveAuditLog).filter(
            ComprehensiveAuditLog.event_type == "configuration_change",
            ComprehensiveAuditLog.timestamp >= start,
            ComprehensiveAuditLog.timestamp <= end,
            *filters
        ).count()
        
        return {
            "configuration_changes": config_changes
        }
    
    def _get_incident_metrics(self, start: datetime, end: datetime, org_id: Optional[int]) -> Dict:
        """Get incident response metrics"""
        try:
            from models.incident import SecurityIncident
            
            query = self.db.query(SecurityIncident).filter(
                SecurityIncident.reported_at >= start,
                SecurityIncident.reported_at <= end
            )
            
            if org_id:
                query = query.filter(SecurityIncident.org_id == org_id)
            
            total_incidents = query.count()
            
            return {
                "total_incidents": total_incidents,
                "by_severity": {
                    "critical": query.filter(SecurityIncident.classification == "CRITICAL").count(),
                    "high": query.filter(SecurityIncident.classification == "HIGH").count(),
                    "moderate": query.filter(SecurityIncident.classification == "MODERATE").count(),
                    "low": query.filter(SecurityIncident.classification == "LOW").count(),
                },
                "by_status": {
                    "new": query.filter(SecurityIncident.status == "NEW").count(),
                    "investigating": query.filter(SecurityIncident.status == "INVESTIGATING").count(),
                    "resolved": query.filter(SecurityIncident.status == "RESOLVED").count(),
                }
            }
        except ImportError:
            return {"total_incidents": 0, "note": "Incident model not available"}
    
    def check_compliance_posture(self) -> Dict:
        """
        Check overall FedRAMP compliance posture
        
        Returns metrics indicating compliance status
        """
        now = datetime.now(timezone.utc)
        
        # Check MFA enrollment for privileged users
        from models.mfa import MFADevice
        admin_users = self.db.query(User).filter(
            User.role.in_(["admin", "founder"])
        ).count()
        
        admin_with_mfa = self.db.query(func.count(func.distinct(MFADevice.user_id))).filter(
            MFADevice.is_active == True
        ).join(User).filter(
            User.role.in_(["admin", "founder"])
        ).scalar() or 0
        
        mfa_compliance = (admin_with_mfa / admin_users * 100) if admin_users > 0 else 100
        
        # Check session management
        # TODO: Add session checks
        
        # Check audit log health
        recent_audits = self.db.query(func.count(ComprehensiveAuditLog.id)).filter(
            ComprehensiveAuditLog.timestamp >= now - timedelta(hours=1)
        ).scalar() or 0
        
        audit_health = "healthy" if recent_audits > 0 else "no_recent_activity"
        
        return {
            "timestamp": now.isoformat(),
            "overall_status": "COMPLIANT" if mfa_compliance >= 100 else "PARTIAL",
            "mfa_compliance": {
                "privileged_users_with_mfa_percent": round(mfa_compliance, 2),
                "total_privileged_users": admin_users,
                "enrolled_count": admin_with_mfa,
                "status": "COMPLIANT" if mfa_compliance >= 100 else "NON_COMPLIANT"
            },
            "audit_system": {
                "status": audit_health,
                "recent_events_count": recent_audits
            },
            "recommendations": self._generate_recommendations(mfa_compliance)
        }
    
    def _generate_recommendations(self, mfa_compliance: float) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if mfa_compliance < 100:
            recommendations.append(
                f"MFA enrollment required for {100 - mfa_compliance:.0f}% of privileged users (IA-2(1))"
            )
        
        # Add more recommendations based on other metrics
        
        return recommendations
    
    def generate_conmon_strategy_document(self) -> Dict:
        """
        CA-7: Generate Continuous Monitoring Strategy document
        
        Documents the continuous monitoring strategy and approach.
        """
        now = datetime.now(timezone.utc)
        
        strategy = {
            "document_type": "Continuous Monitoring Strategy",
            "version": "1.0",
            "generated_at": now.isoformat(),
            "strategy_overview": {
                "purpose": "This document describes the continuous monitoring strategy for maintaining ongoing awareness of information security, vulnerabilities, and threats to support organizational risk management decisions.",
                "scope": "Applies to all information systems within the organization's authorization boundary.",
                "objectives": [
                    "Maintain ongoing awareness of security posture",
                    "Detect security vulnerabilities and threats",
                    "Assess security control effectiveness",
                    "Support risk management decisions",
                    "Enable timely response to security events"
                ]
            },
            "monitoring_approach": {
                "frequency": {
                    "real_time": "Security events, authentication failures, unauthorized access attempts",
                    "daily": "System logs, audit logs, configuration changes",
                    "weekly": "Vulnerability scans, security control assessments",
                    "monthly": "Comprehensive security reports, compliance status",
                    "quarterly": "Risk assessments, control effectiveness reviews",
                    "annually": "Full security assessment, reauthorization"
                },
                "monitoring_tools": [
                    "Automated security monitoring systems",
                    "Vulnerability scanning tools",
                    "Security information and event management (SIEM)",
                    "Configuration management tools",
                    "Audit log analysis tools"
                ],
                "metrics_tracked": [
                    "Authentication success/failure rates",
                    "Account lockout events",
                    "MFA enrollment and usage",
                    "Authorization denials",
                    "Security events and incidents",
                    "Configuration changes",
                    "Vulnerability counts by severity",
                    "POA&M item status and progress",
                    "Control test results"
                ]
            },
            "reporting_requirements": {
                "monthly_reports": {
                    "frequency": "Monthly",
                    "recipients": ["System Owner", "Authorizing Official", "Information System Security Officer"],
                    "content": [
                        "Security event summary",
                        "Vulnerability status",
                        "POA&M progress",
                        "Control effectiveness",
                        "Compliance status"
                    ]
                },
                "quarterly_reports": {
                    "frequency": "Quarterly",
                    "recipients": ["Senior Management", "Authorizing Official"],
                    "content": [
                        "Risk assessment updates",
                        "Trend analysis",
                        "Control effectiveness summary",
                        "Recommendations"
                    ]
                },
                "annual_reports": {
                    "frequency": "Annual",
                    "recipients": ["Authorizing Official", "Senior Management"],
                    "content": [
                        "Comprehensive security assessment",
                        "Annual risk assessment",
                        "Reauthorization recommendation"
                    ]
                }
            },
            "escalation_procedures": {
                "critical_findings": "Immediate notification to System Owner and Authorizing Official",
                "high_findings": "Notification within 24 hours",
                "security_incidents": "Immediate notification per incident response procedures",
                "compliance_deviations": "Notification within 48 hours"
            },
            "roles_and_responsibilities": {
                "system_owner": "Overall responsibility for system security and continuous monitoring",
                "isso": "Day-to-day monitoring activities and reporting",
                "authorizing_official": "Review and decision-making based on monitoring results",
                "security_team": "Technical monitoring and analysis"
            }
        }
        
        return strategy
