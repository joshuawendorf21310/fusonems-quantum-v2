"""
System Integrity (SI) Models for FedRAMP Compliance

This module contains models for all System Integrity controls:
- SI-2: Flaw Remediation
- SI-3: Malicious Code Protection
- SI-5: Security Alerts & Advisories
- SI-6: Security Functionality Verification
- SI-7: Software & Information Integrity
- SI-8: Spam Protection
- SI-12: Information Handling & Retention
- SI-13: Predictable Failure Prevention
- SI-16: Memory Protection
- SI-17: Fail-Safe Procedures
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
from sqlalchemy.orm import relationship

from core.database import Base


# ============================================================================
# SI-2: Flaw Remediation
# ============================================================================

class PatchStatus(str, Enum):
    """Status of a patch"""
    PENDING = "pending"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class PatchPriority(str, Enum):
    """Priority level for patches"""
    CRITICAL = "critical"  # Emergency patches
    HIGH = "high"  # Security patches
    MEDIUM = "medium"  # Important updates
    LOW = "low"  # Regular updates


class PatchRecord(Base):
    """
    Patch management record for SI-2 compliance.
    
    Tracks patches, updates, and remediation actions.
    """
    __tablename__ = "patch_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patch Information
    patch_id = Column(String(128), nullable=False, unique=True, index=True)
    cve_id = Column(String(32), nullable=True, index=True)  # Related CVE
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True, index=True)
    
    # Component Information
    component_type = Column(String(32), nullable=False, index=True)
    component_name = Column(String(256), nullable=False, index=True)
    current_version = Column(String(128), nullable=True)
    target_version = Column(String(128), nullable=False)
    
    # Patch Details
    patch_description = Column(Text, nullable=True)
    patch_url = Column(String(512), nullable=True)
    patch_notes = Column(Text, nullable=True)
    
    # Status Tracking
    status = Column(String(32), nullable=False, default=PatchStatus.PENDING.value, index=True)
    priority = Column(String(32), nullable=False, default=PatchPriority.MEDIUM.value, index=True)
    
    # Timeline
    discovered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_deployment_at = Column(DateTime(timezone=True), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Remediation Timeline Enforcement
    sla_due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    sla_breached = Column(Boolean, nullable=False, default=False, index=True)
    
    # Emergency Patching
    is_emergency = Column(Boolean, nullable=False, default=False, index=True)
    emergency_justification = Column(Text, nullable=True)
    emergency_approver = Column(String(256), nullable=True)
    
    # Deployment Information
    deployed_by = Column(String(256), nullable=True)
    deployment_method = Column(String(64), nullable=True)
    deployment_log = Column(Text, nullable=True)
    
    # Verification
    verified_by = Column(String(256), nullable=True)
    verification_method = Column(String(64), nullable=True)
    verification_result = Column(Text, nullable=True)
    
    # Rollback Information
    rollback_available = Column(Boolean, nullable=False, default=False)
    rollback_instructions = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    vulnerability = relationship("Vulnerability", foreign_keys=[vulnerability_id])
    
    __table_args__ = (
        Index("idx_patch_status_priority", "status", "priority"),
        Index("idx_patch_sla_due", "sla_due_date", "sla_breached"),
        Index("idx_patch_emergency", "is_emergency", "status"),
    )


# ============================================================================
# SI-3: Malicious Code Protection
# ============================================================================

class ScanStatus(str, Enum):
    """Status of a malware scan"""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    QUARANTINED = "quarantined"
    ERROR = "error"


class ThreatType(str, Enum):
    """Type of threat detected"""
    VIRUS = "virus"
    TROJAN = "trojan"
    WORM = "worm"
    RANSOMWARE = "ransomware"
    SPYWARE = "spyware"
    ADWARE = "adware"
    ROOTKIT = "rootkit"
    MALWARE = "malware"
    SUSPICIOUS = "suspicious"


class MalwareScan(Base):
    """
    Malware scan record for SI-3 compliance.
    
    Tracks file scans, threats detected, and quarantine actions.
    """
    __tablename__ = "malware_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Scan Information
    scan_id = Column(String(128), nullable=False, unique=True, index=True)
    scan_type = Column(String(32), nullable=False, index=True)  # "on_demand", "scheduled", "on_upload"
    
    # File Information
    file_path = Column(String(1024), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    file_size = Column(Integer, nullable=True)
    file_name = Column(String(512), nullable=True)
    file_type = Column(String(64), nullable=True)
    
    # Scan Results
    status = Column(String(32), nullable=False, default=ScanStatus.PENDING.value, index=True)
    threat_detected = Column(Boolean, nullable=False, default=False, index=True)
    threat_name = Column(String(256), nullable=True)
    threat_type = Column(String(32), nullable=True)
    threat_signature = Column(String(256), nullable=True)
    
    # Antivirus Information
    scanner_engine = Column(String(64), nullable=True)  # e.g., "ClamAV"
    scanner_version = Column(String(32), nullable=True)
    signature_version = Column(String(32), nullable=True)
    signature_date = Column(DateTime(timezone=True), nullable=True)
    
    # Quarantine Information
    quarantined = Column(Boolean, nullable=False, default=False, index=True)
    quarantine_path = Column(String(1024), nullable=True)
    quarantine_reason = Column(Text, nullable=True)
    quarantined_at = Column(DateTime(timezone=True), nullable=True)
    quarantined_by = Column(String(256), nullable=True)
    
    # Remediation
    remediated = Column(Boolean, nullable=False, default=False)
    remediation_action = Column(String(64), nullable=True)  # "quarantined", "deleted", "cleaned"
    remediated_at = Column(DateTime(timezone=True), nullable=True)
    remediated_by = Column(String(256), nullable=True)
    
    # Context
    user_id = Column(Integer, nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    upload_id = Column(String(128), nullable=True, index=True)
    
    # Scan Metadata
    scan_duration_ms = Column(Integer, nullable=True)
    scan_details = Column(JSON, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index("idx_malware_threat_status", "threat_detected", "status"),
        Index("idx_malware_quarantine", "quarantined", "quarantined_at"),
        Index("idx_malware_file_hash", "file_hash"),
    )


class SignatureUpdate(Base):
    """
    Antivirus signature update record.
    
    Tracks signature database updates for malware protection.
    """
    __tablename__ = "signature_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Update Information
    update_id = Column(String(128), nullable=False, unique=True, index=True)
    scanner_engine = Column(String(64), nullable=False, index=True)
    signature_version = Column(String(32), nullable=False)
    
    # Update Details
    update_type = Column(String(32), nullable=False)  # "full", "incremental"
    update_size_bytes = Column(Integer, nullable=True)
    update_url = Column(String(512), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default="pending")  # "pending", "downloading", "installed", "failed"
    installed = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timeline
    published_at = Column(DateTime(timezone=True), nullable=True)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())


# ============================================================================
# SI-5: Security Alerts & Advisories
# ============================================================================

class AlertSeverity(str, Enum):
    """Severity of security alert"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AlertStatus(str, Enum):
    """Status of alert processing"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class SecurityAlert(Base):
    """
    Security alert/advisory record for SI-5 compliance.
    
    Tracks security alerts from CISA/US-CERT and other sources.
    """
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert Information
    alert_id = Column(String(128), nullable=False, unique=True, index=True)
    source = Column(String(64), nullable=False, index=True)  # "CISA", "US-CERT", "NIST", "vendor"
    source_alert_id = Column(String(128), nullable=True, index=True)
    
    # Alert Details
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Classification
    severity = Column(String(32), nullable=False, default=AlertSeverity.MEDIUM.value, index=True)
    category = Column(String(64), nullable=True, index=True)  # "vulnerability", "threat", "advisory"
    
    # Affected Systems
    affected_components = Column(JSON, nullable=True)  # List of affected components
    affected_versions = Column(JSON, nullable=True)
    cve_ids = Column(JSON, nullable=True)  # Related CVEs
    
    # Alert Metadata
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status Tracking
    status = Column(String(32), nullable=False, default=AlertStatus.NEW.value, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(256), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(256), nullable=True)
    
    # Response Actions
    response_actions = Column(JSON, nullable=True)  # List of recommended actions
    response_taken = Column(JSON, nullable=True)  # Actions actually taken
    response_notes = Column(Text, nullable=True)
    
    # Distribution
    distributed_to = Column(JSON, nullable=True)  # List of recipients/roles
    distribution_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # References
    references = Column(JSON, nullable=True)  # URLs, documents, etc.
    raw_data = Column(JSON, nullable=True)  # Original alert data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_alert_severity_status", "severity", "status"),
        Index("idx_alert_source_published", "source", "published_at"),
        Index("idx_alert_status_created", "status", "created_at"),
    )


# ============================================================================
# SI-6: Security Functionality Verification
# ============================================================================

class VerificationStatus(str, Enum):
    """Status of security functionality verification"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class SecurityFunctionalityTest(Base):
    """
    Security functionality verification test record for SI-6 compliance.
    
    Tracks automated security testing and function validation.
    """
    __tablename__ = "security_functionality_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Test Information
    test_id = Column(String(128), nullable=False, unique=True, index=True)
    test_name = Column(String(256), nullable=False, index=True)
    test_category = Column(String(64), nullable=False, index=True)  # "authentication", "encryption", "access_control", etc.
    
    # Test Configuration
    test_type = Column(String(32), nullable=False)  # "automated", "manual", "integration"
    test_frequency = Column(String(32), nullable=True)  # "daily", "weekly", "monthly", "on_demand"
    
    # Test Results
    status = Column(String(32), nullable=False, default=VerificationStatus.PENDING.value, index=True)
    passed = Column(Boolean, nullable=True, index=True)
    result_message = Column(Text, nullable=True)
    
    # Test Execution
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Test Details
    test_output = Column(JSON, nullable=True)
    test_logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Verification
    verified_by = Column(String(256), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Related Information
    related_components = Column(JSON, nullable=True)
    related_vulnerabilities = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_test_category_status", "test_category", "status"),
        Index("idx_test_status_created", "status", "created_at"),
        Index("idx_test_passed", "passed", "created_at"),
    )


# ============================================================================
# SI-7: Software & Information Integrity
# ============================================================================

class IntegrityStatus(str, Enum):
    """Status of integrity verification"""
    VERIFIED = "verified"
    FAILED = "failed"
    PENDING = "pending"
    ERROR = "error"


class IntegrityCheckType(str, Enum):
    """Type of integrity check"""
    CODE_SIGNING = "code_signing"
    CHECKSUM = "checksum"
    HASH_VERIFICATION = "hash_verification"
    TAMPER_DETECTION = "tamper_detection"


class IntegrityVerification(Base):
    """
    Software and information integrity verification record for SI-7 compliance.
    
    Tracks code signing, checksums, and tamper detection.
    """
    __tablename__ = "integrity_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Verification Information
    verification_id = Column(String(128), nullable=False, unique=True, index=True)
    check_type = Column(String(32), nullable=False, index=True)
    
    # Target Information
    target_type = Column(String(64), nullable=False, index=True)  # "software", "file", "package", "image"
    target_name = Column(String(512), nullable=False)
    target_path = Column(String(1024), nullable=True)
    target_version = Column(String(128), nullable=True)
    
    # Integrity Checks
    expected_hash = Column(String(64), nullable=True)  # SHA-256
    actual_hash = Column(String(64), nullable=True)
    hash_match = Column(Boolean, nullable=True, index=True)
    
    # Code Signing
    signed = Column(Boolean, nullable=True)
    signer = Column(String(256), nullable=True)
    signature_valid = Column(Boolean, nullable=True, index=True)
    certificate_chain = Column(JSON, nullable=True)
    certificate_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Tamper Detection
    tamper_detected = Column(Boolean, nullable=False, default=False, index=True)
    tamper_details = Column(Text, nullable=True)
    tamper_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Verification Results
    status = Column(String(32), nullable=False, default=IntegrityStatus.PENDING.value, index=True)
    verification_passed = Column(Boolean, nullable=True, index=True)
    verification_message = Column(Text, nullable=True)
    
    # Baseline Information
    baseline_id = Column(String(128), nullable=True, index=True)
    baseline_hash = Column(String(64), nullable=True)
    baseline_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification Details
    verification_method = Column(String(64), nullable=True)
    verification_tool = Column(String(128), nullable=True)
    verification_output = Column(JSON, nullable=True)
    
    # Timestamps
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_integrity_status_type", "status", "check_type"),
        Index("idx_integrity_tamper", "tamper_detected", "verified_at"),
        Index("idx_integrity_hash_match", "hash_match", "status"),
    )


# ============================================================================
# SI-8: Spam Protection
# ============================================================================

class SpamClassification(str, Enum):
    """Spam classification"""
    SPAM = "spam"
    HAM = "ham"  # Not spam
    SUSPICIOUS = "suspicious"
    PHISHING = "phishing"
    MALWARE = "malware"


class SpamFilterResult(Base):
    """
    Spam protection filter result for SI-8 compliance.
    
    Tracks email filtering and spam detection.
    """
    __tablename__ = "spam_filter_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Message Information
    message_id = Column(String(256), nullable=False, unique=True, index=True)
    message_subject = Column(String(512), nullable=True)
    sender_email = Column(String(256), nullable=True, index=True)
    recipient_email = Column(String(256), nullable=True, index=True)
    
    # Filtering Results
    classification = Column(String(32), nullable=False, index=True)
    spam_score = Column(Integer, nullable=True)  # 0-100
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    
    # Filter Details
    filter_engine = Column(String(64), nullable=True)  # e.g., "SpamAssassin", "custom"
    filter_rules_matched = Column(JSON, nullable=True)  # List of matched rules
    filter_action = Column(String(32), nullable=True)  # "quarantine", "reject", "mark", "allow"
    
    # Content Analysis
    content_scanned = Column(Boolean, nullable=False, default=False)
    links_checked = Column(Boolean, nullable=False, default=False)
    attachments_scanned = Column(Boolean, nullable=False, default=False)
    
    # Threat Detection
    phishing_detected = Column(Boolean, nullable=False, default=False, index=True)
    malware_detected = Column(Boolean, nullable=False, default=False, index=True)
    threat_details = Column(JSON, nullable=True)
    
    # Action Taken
    action_taken = Column(String(32), nullable=True)  # "quarantined", "deleted", "delivered", "flagged"
    action_taken_at = Column(DateTime(timezone=True), nullable=True)
    
    # User Context
    user_id = Column(Integer, nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index("idx_spam_classification_score", "classification", "spam_score"),
        Index("idx_spam_phishing", "phishing_detected", "created_at"),
        Index("idx_spam_sender", "sender_email", "classification"),
    )


# ============================================================================
# SI-12: Information Handling & Retention
# ============================================================================

class RetentionPolicyStatus(str, Enum):
    """Status of retention policy"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class LegalHoldStatus(str, Enum):
    """Status of legal hold"""
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class InformationRetentionPolicy(Base):
    """
    Information retention policy for SI-12 compliance.
    
    Defines retention periods and automated purging rules.
    """
    __tablename__ = "information_retention_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Policy Information
    policy_id = Column(String(128), nullable=False, unique=True, index=True)
    policy_name = Column(String(256), nullable=False)
    policy_description = Column(Text, nullable=True)
    
    # Scope
    data_type = Column(String(64), nullable=False, index=True)  # "audit_log", "user_data", "epcr", "billing", etc.
    data_category = Column(String(64), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Retention Rules
    retention_period_days = Column(Integer, nullable=False)
    retention_period_months = Column(Integer, nullable=True)
    retention_period_years = Column(Integer, nullable=True)
    
    # Purge Configuration
    auto_purge_enabled = Column(Boolean, nullable=False, default=True, index=True)
    purge_schedule = Column(String(64), nullable=True)  # "daily", "weekly", "monthly"
    purge_time = Column(String(8), nullable=True)  # "HH:MM" format
    
    # Legal Hold
    legal_hold_enabled = Column(Boolean, nullable=False, default=False)
    legal_hold_override = Column(Boolean, nullable=False, default=False)  # Override purge for legal holds
    
    # Status
    status = Column(String(32), nullable=False, default=RetentionPolicyStatus.ACTIVE.value, index=True)
    
    # Compliance
    compliance_requirements = Column(JSON, nullable=True)  # List of compliance requirements (HIPAA, etc.)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_retention_data_type_status", "data_type", "status"),
        Index("idx_retention_auto_purge", "auto_purge_enabled", "status"),
    )


class LegalHold(Base):
    """
    Legal hold record for SI-12 compliance.
    
    Prevents data purging during legal proceedings.
    """
    __tablename__ = "legal_holds"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Hold Information
    hold_id = Column(String(128), nullable=False, unique=True, index=True)
    case_name = Column(String(256), nullable=False)
    case_number = Column(String(128), nullable=True)
    case_description = Column(Text, nullable=True)
    
    # Scope
    data_types = Column(JSON, nullable=False)  # List of data types covered
    organization_id = Column(Integer, nullable=True, index=True)
    user_ids = Column(JSON, nullable=True)  # Specific users if applicable
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(32), nullable=False, default=LegalHoldStatus.ACTIVE.value, index=True)
    
    # Legal Information
    legal_counsel = Column(String(256), nullable=True)
    court_order_number = Column(String(128), nullable=True)
    court_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Management
    created_by = Column(String(256), nullable=False)
    released_by = Column(String(256), nullable=True)
    release_reason = Column(Text, nullable=True)
    
    # Timeline
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_legal_hold_status", "status", "created_at"),
        Index("idx_legal_hold_org", "organization_id", "status"),
    )


class DataPurgeRecord(Base):
    """
    Data purge execution record for SI-12 compliance.
    
    Tracks automated and manual data purging operations.
    """
    __tablename__ = "data_purge_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Purge Information
    purge_id = Column(String(128), nullable=False, unique=True, index=True)
    policy_id = Column(String(128), ForeignKey("information_retention_policies.policy_id"), nullable=True, index=True)
    
    # Purge Details
    purge_type = Column(String(32), nullable=False)  # "automated", "manual", "legal_release"
    data_type = Column(String(64), nullable=False, index=True)
    data_category = Column(String(64), nullable=True)
    
    # Scope
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Execution
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results
    records_purged = Column(Integer, nullable=True)
    records_skipped = Column(Integer, nullable=True)  # Skipped due to legal hold
    purge_successful = Column(Boolean, nullable=True, index=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Executed By
    executed_by = Column(String(256), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index("idx_purge_data_type_created", "data_type", "created_at"),
        Index("idx_purge_successful", "purge_successful", "completed_at"),
    )


# ============================================================================
# SI-13: Predictable Failure Prevention
# ============================================================================

class FailureType(str, Enum):
    """Type of predictable failure"""
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    STORAGE = "storage"
    DATABASE = "database"
    SERVICE = "service"


class FailurePreventionAction(Base):
    """
    Predictable failure prevention action for SI-13 compliance.
    
    Tracks failure prevention measures and redundancy.
    """
    __tablename__ = "failure_prevention_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action Information
    action_id = Column(String(128), nullable=False, unique=True, index=True)
    action_name = Column(String(256), nullable=False)
    action_description = Column(Text, nullable=True)
    
    # Failure Context
    failure_type = Column(String(32), nullable=False, index=True)
    component_name = Column(String(256), nullable=False, index=True)
    component_type = Column(String(64), nullable=True)
    
    # Prevention Measures
    prevention_type = Column(String(32), nullable=False)  # "redundancy", "backup", "monitoring", "maintenance"
    redundancy_level = Column(Integer, nullable=True)  # Number of redundant components
    backup_frequency = Column(String(32), nullable=True)
    
    # Status
    active = Column(Boolean, nullable=False, default=True, index=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    next_verification_due = Column(DateTime(timezone=True), nullable=True)
    
    # Effectiveness
    failures_prevented = Column(Integer, nullable=False, default=0)
    last_failure_prevented_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_failure_type_component", "failure_type", "component_name"),
        Index("idx_failure_active", "active", "last_verified_at"),
    )


# ============================================================================
# SI-16: Memory Protection
# ============================================================================

class MemoryProtectionStatus(str, Enum):
    """Status of memory protection"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class MemoryProtectionConfig(Base):
    """
    Memory protection configuration for SI-16 compliance.
    
    Tracks memory protection settings and enforcement.
    """
    __tablename__ = "memory_protection_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration Information
    config_id = Column(String(128), nullable=False, unique=True, index=True)
    system_name = Column(String(256), nullable=False, index=True)
    system_type = Column(String(64), nullable=False)  # "server", "container", "application"
    
    # Protection Features
    aslr_enabled = Column(Boolean, nullable=False, default=True)  # Address Space Layout Randomization
    dep_enabled = Column(Boolean, nullable=False, default=True)  # Data Execution Prevention
    stack_protection = Column(Boolean, nullable=False, default=True)
    heap_protection = Column(Boolean, nullable=False, default=True)
    memory_isolation = Column(Boolean, nullable=False, default=True)
    
    # Status
    status = Column(String(32), nullable=False, default=MemoryProtectionStatus.ENABLED.value, index=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification
    verification_passed = Column(Boolean, nullable=True)
    verification_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_memory_system_status", "system_name", "status"),
        Index("idx_memory_status_verified", "status", "last_verified_at"),
    )


# ============================================================================
# SI-17: Fail-Safe Procedures
# ============================================================================

class FailSafeStatus(str, Enum):
    """Status of fail-safe procedure"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    RESOLVED = "resolved"
    DISABLED = "disabled"


class FailSafeProcedure(Base):
    """
    Fail-safe procedure record for SI-17 compliance.
    
    Tracks fail-safe mechanisms and procedures.
    """
    __tablename__ = "fail_safe_procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Procedure Information
    procedure_id = Column(String(128), nullable=False, unique=True, index=True)
    procedure_name = Column(String(256), nullable=False)
    procedure_description = Column(Text, nullable=True)
    
    # Trigger Conditions
    trigger_type = Column(String(32), nullable=False)  # "failure", "error", "threshold", "manual"
    trigger_conditions = Column(JSON, nullable=False)  # Conditions that trigger fail-safe
    threshold_value = Column(String(128), nullable=True)
    
    # Fail-Safe Actions
    action_type = Column(String(32), nullable=False)  # "shutdown", "isolate", "rollback", "alert", "degrade"
    action_description = Column(Text, nullable=False)
    action_script = Column(Text, nullable=True)  # Automated action script
    
    # Status
    status = Column(String(32), nullable=False, default=FailSafeStatus.ACTIVE.value, index=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    
    # Execution History
    times_triggered = Column(Integer, nullable=False, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Effectiveness
    action_successful = Column(Boolean, nullable=True)
    resolution_time_seconds = Column(Integer, nullable=True)
    
    # Related Components
    component_name = Column(String(256), nullable=True, index=True)
    system_name = Column(String(256), nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_failsafe_status_enabled", "status", "enabled"),
        Index("idx_failsafe_component", "component_name", "status"),
        Index("idx_failsafe_triggered", "last_triggered_at"),
    )
