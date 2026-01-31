"""
Audit Reduction Models for FedRAMP AU-7 Compliance

FedRAMP Requirement AU-7: Audit Reduction and Report Generation
- Automated log analysis
- Pattern detection
- Report generation
- Query optimization
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class ReportType(str, Enum):
    """Type of audit reduction report"""
    SUMMARY = "summary"
    COMPLIANCE = "compliance"
    SECURITY_INCIDENT = "security_incident"
    USER_ACTIVITY = "user_activity"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Status of audit reduction report"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class PatternType(str, Enum):
    """Type of pattern detected in audit logs"""
    ANOMALOUS_ACCESS = "anomalous_access"
    FAILED_AUTHENTICATION = "failed_authentication"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    CUSTOM = "custom"


class AuditReductionReport(Base):
    """
    Audit reduction and report generation records (AU-7).
    
    Stores generated audit reports and analysis results.
    """
    __tablename__ = "audit_reduction_reports"
    __table_args__ = (
        Index('idx_report_org_type', 'org_id', 'report_type'),
        Index('idx_report_status', 'status'),
        Index('idx_report_created', 'created_at'),
        Index('idx_report_period', 'period_start', 'period_end'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Report identification
    report_name = Column(String(255), nullable=False)
    report_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=True)
    
    # Report period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=ReportStatus.PENDING.value,
        index=True,
    )
    
    # Query parameters
    query_filters = Column(JSON, nullable=True)  # Filters applied to audit logs
    query_parameters = Column(JSON, nullable=True)  # Additional query parameters
    
    # Report results
    summary_statistics = Column(JSON, nullable=True)  # Summary stats
    detected_patterns = Column(JSON, nullable=True)  # Patterns detected
    findings = Column(JSON, nullable=True)  # Key findings
    recommendations = Column(JSON, nullable=True)  # Recommendations
    
    # Generated content
    report_content = Column(JSON, nullable=True)  # Full report data
    report_format = Column(String(50), nullable=True)  # json, csv, pdf, html
    
    # Generation metadata
    events_analyzed = Column(Integer, nullable=True)  # Number of events analyzed
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)
    generation_duration_seconds = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Created by
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_email = Column(String(255), nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<AuditReductionReport(id={self.id}, "
            f"report_name={self.report_name}, "
            f"report_type={self.report_type}, "
            f"status={self.status})>"
        )


class AuditPattern(Base):
    """
    Detected patterns in audit logs (AU-7).
    
    Stores patterns detected during audit log analysis.
    """
    __tablename__ = "audit_patterns"
    __table_args__ = (
        Index('idx_pattern_org_type', 'org_id', 'pattern_type'),
        Index('idx_pattern_detected', 'detected_at'),
        Index('idx_pattern_severity', 'severity'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Pattern identification
    pattern_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    pattern_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pattern details
    pattern_definition = Column(JSON, nullable=False)  # Pattern matching rules
    matched_events = Column(JSON, nullable=True)  # Event IDs that matched
    match_count = Column(Integer, nullable=False, default=0)
    
    # Severity and risk
    severity = Column(String(50), nullable=False)  # low, medium, high, critical
    risk_score = Column(Integer, nullable=True)  # 0-100
    
    # Detection
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    detected_by = Column(String(255), nullable=True)  # Analysis system/algorithm
    
    # Time range
    first_occurrence = Column(DateTime(timezone=True), nullable=True)
    last_occurrence = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<AuditPattern(id={self.id}, "
            f"pattern_type={self.pattern_type}, "
            f"pattern_name={self.pattern_name}, "
            f"match_count={self.match_count})>"
        )


class AuditQueryOptimization(Base):
    """
    Audit query optimization records (AU-7).
    
    Tracks query performance and optimization strategies.
    """
    __tablename__ = "audit_query_optimizations"
    __table_args__ = (
        Index('idx_query_opt_org', 'org_id'),
        Index('idx_query_opt_timestamp', 'recorded_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Organization scope
    org_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Query details
    query_type = Column(String(100), nullable=False)  # report_generation, pattern_detection, etc.
    query_parameters = Column(JSON, nullable=True)
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=False)
    events_scanned = Column(Integer, nullable=True)
    events_returned = Column(Integer, nullable=True)
    index_used = Column(Boolean, default=False, nullable=False)
    
    # Optimization
    optimization_applied = Column(JSON, nullable=True)  # Optimizations applied
    performance_improvement_percent = Column(Integer, nullable=True)
    
    # Timestamp
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (
            f"<AuditQueryOptimization(id={self.id}, "
            f"query_type={self.query_type}, "
            f"execution_time_ms={self.execution_time_ms})>"
        )
