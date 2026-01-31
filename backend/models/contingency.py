"""
FedRAMP Contingency Planning (CP) Control Models

This module implements database models for FedRAMP CP controls:
- CP-2: Contingency Plan
- CP-3: Contingency Training
- CP-4: Contingency Plan Testing
- CP-6: Alternate Storage Site
- CP-7: Alternate Processing Site
- CP-9: Information System Backup
- CP-10: Information System Recovery
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
    Float,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base


# ============================================================================
# CP-2: Contingency Plan
# ============================================================================

class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"


class DistributionStatus(str, Enum):
    PENDING = "pending"
    DISTRIBUTED = "distributed"
    ACKNOWLEDGED = "acknowledged"


class ContingencyPlan(Base):
    """
    CP-2: Contingency Plan
    
    Stores contingency plans with versioning, distribution tracking,
    and annual review automation.
    """
    __tablename__ = "contingency_plans"
    __table_args__ = (
        Index('idx_cp_plan_org_status', 'org_id', 'status'),
        Index('idx_cp_plan_version', 'plan_id', 'version'),
        Index('idx_cp_plan_review_date', 'next_review_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plan identification
    plan_id = Column(String(100), nullable=False, index=True)  # Unique plan identifier
    version = Column(String(50), nullable=False)  # Version number (e.g., "1.0", "2.1")
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Plan content
    plan_content = Column(Text, nullable=False)  # Full plan text/content
    plan_document_path = Column(String(1000), nullable=True)  # Path to stored document
    
    # Status and lifecycle
    status = Column(String(50), nullable=False, default=PlanStatus.DRAFT.value, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Review tracking
    last_review_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=False, index=True)
    review_frequency_days = Column(Integer, default=365)  # Annual review default
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    distributions = relationship("PlanDistribution", back_populates="plan", cascade="all, delete-orphan")
    tests = relationship("ContingencyPlanTest", back_populates="plan", cascade="all, delete-orphan")


class PlanDistribution(Base):
    """
    CP-2: Plan Distribution Tracking
    
    Tracks distribution of contingency plans to stakeholders.
    """
    __tablename__ = "plan_distributions"
    __table_args__ = (
        Index('idx_cp_dist_plan_user', 'plan_id', 'user_id'),
        Index('idx_cp_dist_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("contingency_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Recipient information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=False)  # Denormalized for retention
    user_role = Column(String(100), nullable=True)
    
    # Distribution details
    distribution_method = Column(String(100), nullable=False)  # email, portal, physical, etc.
    distribution_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(String(50), nullable=False, default=DistributionStatus.PENDING.value, index=True)
    
    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledgment_ip_address = Column(String(45), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    plan = relationship("ContingencyPlan", back_populates="distributions")


# ============================================================================
# CP-3: Contingency Training
# ============================================================================

class TrainingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DrillStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContingencyTraining(Base):
    """
    CP-3: Contingency Training
    
    Manages contingency training schedules, completion tracking, and drills.
    """
    __tablename__ = "contingency_trainings"
    __table_args__ = (
        Index('idx_cp_train_org_status', 'org_id', 'status'),
        Index('idx_cp_train_scheduled', 'scheduled_date'),
        Index('idx_cp_train_user', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Training identification
    training_name = Column(String(500), nullable=False)
    training_type = Column(String(100), nullable=False)  # initial, refresher, drill, etc.
    description = Column(Text, nullable=True)
    
    # Schedule
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Participants
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=False)  # Denormalized
    user_role = Column(String(100), nullable=True)
    
    # Status and results
    status = Column(String(50), nullable=False, default=TrainingStatus.SCHEDULED.value, index=True)
    completion_percentage = Column(Float, nullable=True)  # 0-100
    score = Column(Float, nullable=True)  # Test score if applicable
    passed = Column(Boolean, nullable=True)
    
    # Training content
    training_content_path = Column(String(1000), nullable=True)
    training_materials = Column(JSON, nullable=True)  # Links, resources, etc.
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ContingencyDrill(Base):
    """
    CP-3: Contingency Drill
    
    Tracks execution of contingency drills and exercises.
    """
    __tablename__ = "contingency_drills"
    __table_args__ = (
        Index('idx_cp_drill_org_status', 'org_id', 'status'),
        Index('idx_cp_drill_scheduled', 'scheduled_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Drill identification
    drill_name = Column(String(500), nullable=False)
    drill_type = Column(String(100), nullable=False)  # tabletop, full_scale, functional, etc.
    scenario_description = Column(Text, nullable=True)
    
    # Schedule
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status and results
    status = Column(String(50), nullable=False, default=DrillStatus.SCHEDULED.value, index=True)
    participants_count = Column(Integer, nullable=True)
    
    # Results
    drill_results = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)  # List of action items from drill
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# CP-4: Contingency Plan Testing
# ============================================================================

class TestStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NOT_TESTED = "not_tested"


class ContingencyPlanTest(Base):
    """
    CP-4: Contingency Plan Testing
    
    Manages contingency plan testing schedules, results documentation,
    and issue tracking.
    """
    __tablename__ = "contingency_plan_tests"
    __table_args__ = (
        Index('idx_cp_test_plan_status', 'plan_id', 'status'),
        Index('idx_cp_test_scheduled', 'scheduled_date'),
        Index('idx_cp_test_result', 'test_result'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("contingency_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Test identification
    test_name = Column(String(500), nullable=False)
    test_type = Column(String(100), nullable=False)  # functional, full_scale, tabletop, etc.
    test_description = Column(Text, nullable=True)
    
    # Schedule
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status and results
    status = Column(String(50), nullable=False, default=TestStatus.SCHEDULED.value, index=True)
    test_result = Column(String(50), nullable=True, index=True)  # pass, fail, partial
    
    # Test documentation
    test_procedures = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)
    test_report_path = Column(String(1000), nullable=True)
    
    # Issue tracking
    issues_identified = Column(JSON, nullable=True)  # List of issues found
    remediation_plan = Column(Text, nullable=True)
    
    # Participants
    test_team = Column(JSON, nullable=True)  # List of user IDs/emails
    conducted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    plan = relationship("ContingencyPlan", back_populates="tests")


# ============================================================================
# CP-6: Alternate Storage Site
# ============================================================================

class StorageSiteStatus(str, Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class ReplicationStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    SYNCING = "syncing"


class AlternateStorageSite(Base):
    """
    CP-6: Alternate Storage Site
    
    Manages alternate storage site configuration, replication monitoring,
    and failover automation.
    """
    __tablename__ = "alternate_storage_sites"
    __table_args__ = (
        Index('idx_cp_storage_org_status', 'org_id', 'status'),
        Index('idx_cp_storage_primary', 'is_primary'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Site identification
    site_name = Column(String(255), nullable=False)
    site_location = Column(String(500), nullable=True)
    site_type = Column(String(100), nullable=False)  # hot, warm, cold, mobile
    is_primary = Column(Boolean, default=False, nullable=False, index=True)
    
    # Configuration
    storage_capacity_gb = Column(Float, nullable=True)
    storage_used_gb = Column(Float, nullable=True)
    storage_available_gb = Column(Float, nullable=True)
    
    # Connection details (encrypted in application layer)
    connection_endpoint = Column(String(500), nullable=True)
    connection_config = Column(JSON, nullable=True)  # Encrypted connection details
    
    # Status
    status = Column(String(50), nullable=False, default=StorageSiteStatus.STANDBY.value, index=True)
    replication_status = Column(String(50), nullable=True, index=True)
    
    # Replication monitoring
    last_replication_check = Column(DateTime(timezone=True), nullable=True)
    replication_lag_seconds = Column(Integer, nullable=True)
    replication_health_score = Column(Float, nullable=True)  # 0-100
    
    # Failover
    failover_capable = Column(Boolean, default=True, nullable=False)
    last_failover_test = Column(DateTime(timezone=True), nullable=True)
    failover_rto_minutes = Column(Integer, nullable=True)  # Recovery Time Objective
    failover_rpo_minutes = Column(Integer, nullable=True)  # Recovery Point Objective
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class StorageReplicationLog(Base):
    """
    CP-6: Storage Replication Log
    
    Logs replication events and status changes.
    """
    __tablename__ = "storage_replication_logs"
    __table_args__ = (
        Index('idx_cp_repl_storage_date', 'storage_site_id', 'created_at'),
        Index('idx_cp_repl_status', 'replication_status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    storage_site_id = Column(Integer, ForeignKey("alternate_storage_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Replication event
    replication_status = Column(String(50), nullable=False, index=True)
    replication_lag_seconds = Column(Integer, nullable=True)
    data_transferred_gb = Column(Float, nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # sync, check, failover, etc.
    event_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# ============================================================================
# CP-7: Alternate Processing Site
# ============================================================================

class ProcessingSiteStatus(str, Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    ACTIVATING = "activating"


class AlternateProcessingSite(Base):
    """
    CP-7: Alternate Processing Site
    
    Manages alternate processing site configuration, capacity monitoring,
    and activation procedures.
    """
    __tablename__ = "alternate_processing_sites"
    __table_args__ = (
        Index('idx_cp_proc_org_status', 'org_id', 'status'),
        Index('idx_cp_proc_primary', 'is_primary'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Site identification
    site_name = Column(String(255), nullable=False)
    site_location = Column(String(500), nullable=True)
    site_type = Column(String(100), nullable=False)  # hot, warm, cold, mobile
    is_primary = Column(Boolean, default=False, nullable=False, index=True)
    
    # Capacity monitoring
    compute_capacity_cpu_cores = Column(Integer, nullable=True)
    compute_capacity_ram_gb = Column(Integer, nullable=True)
    compute_utilization_percent = Column(Float, nullable=True)
    
    compute_available_cpu_cores = Column(Integer, nullable=True)
    compute_available_ram_gb = Column(Integer, nullable=True)
    
    # Connection details
    connection_endpoint = Column(String(500), nullable=True)
    connection_config = Column(JSON, nullable=True)  # Encrypted connection details
    
    # Status
    status = Column(String(50), nullable=False, default=ProcessingSiteStatus.STANDBY.value, index=True)
    health_status = Column(String(50), nullable=True)  # healthy, degraded, failed
    
    # Activation
    activation_capable = Column(Boolean, default=True, nullable=False)
    activation_rto_minutes = Column(Integer, nullable=True)  # Recovery Time Objective
    last_activation_test = Column(DateTime(timezone=True), nullable=True)
    activation_procedures = Column(Text, nullable=True)
    
    # Monitoring
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_score = Column(Float, nullable=True)  # 0-100
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProcessingSiteActivationLog(Base):
    """
    CP-7: Processing Site Activation Log
    
    Logs activation events and procedures.
    """
    __tablename__ = "processing_site_activation_logs"
    __table_args__ = (
        Index('idx_cp_act_proc_date', 'processing_site_id', 'created_at'),
        Index('idx_cp_act_type', 'activation_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    processing_site_id = Column(Integer, ForeignKey("alternate_processing_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activation event
    activation_type = Column(String(100), nullable=False, index=True)  # test, actual, drill
    activation_status = Column(String(50), nullable=False)  # initiated, in_progress, completed, failed
    activation_duration_minutes = Column(Integer, nullable=True)
    
    # Event details
    event_message = Column(Text, nullable=True)
    procedures_followed = Column(Text, nullable=True)
    issues_encountered = Column(Text, nullable=True)
    
    # Initiator
    initiated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# ============================================================================
# CP-9: Information System Backup
# ============================================================================

class BackupStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class SystemBackup(Base):
    """
    CP-9: Information System Backup
    
    Manages automated backup scheduling, backup verification,
    restore testing, and retention management.
    """
    __tablename__ = "system_backups"
    __table_args__ = (
        Index('idx_cp_backup_org_status', 'org_id', 'status'),
        Index('idx_cp_backup_scheduled', 'scheduled_time'),
        Index('idx_cp_backup_type', 'backup_type'),
        Index('idx_cp_backup_retention', 'retention_until'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Backup identification
    backup_name = Column(String(500), nullable=False)
    backup_type = Column(String(50), nullable=False, index=True)  # full, incremental, differential, snapshot
    system_component = Column(String(255), nullable=False)  # database, files, config, etc.
    
    # Schedule
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default=BackupStatus.SCHEDULED.value, index=True)
    
    # Backup details
    backup_size_bytes = Column(Integer, nullable=True)
    backup_location = Column(String(1000), nullable=False)  # Storage location/path
    backup_format = Column(String(100), nullable=True)  # tar, zip, sql, etc.
    compression_ratio = Column(Float, nullable=True)
    
    # Verification
    verification_status = Column(String(50), nullable=True)  # verified, failed, pending
    verification_time = Column(DateTime(timezone=True), nullable=True)
    verification_method = Column(String(255), nullable=True)  # checksum, restore_test, etc.
    verification_result = Column(Text, nullable=True)
    
    # Retention
    retention_days = Column(Integer, nullable=False, default=90)
    retention_until = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Restore testing
    last_restore_test = Column(DateTime(timezone=True), nullable=True)
    restore_test_status = Column(String(50), nullable=True)  # passed, failed, not_tested
    restore_test_result = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BackupSchedule(Base):
    """
    CP-9: Backup Schedule
    
    Defines automated backup schedules.
    """
    __tablename__ = "backup_schedules"
    __table_args__ = (
        Index('idx_cp_sched_org_active', 'org_id', 'active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Schedule identification
    schedule_name = Column(String(255), nullable=False)
    system_component = Column(String(255), nullable=False)
    backup_type = Column(String(50), nullable=False)
    
    # Schedule configuration
    schedule_cron = Column(String(100), nullable=True)  # Cron expression
    schedule_frequency = Column(String(100), nullable=False)  # daily, weekly, monthly, etc.
    schedule_time = Column(String(50), nullable=True)  # Time of day
    
    # Retention
    retention_days = Column(Integer, nullable=False, default=90)
    
    # Status
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# CP-10: Information System Recovery
# ============================================================================

class RecoveryStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecoveryType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    GRANULAR = "granular"  # File, database table, etc.


class SystemRecovery(Base):
    """
    CP-10: Information System Recovery
    
    Manages recovery procedures, RPO/RTO monitoring, and recovery testing.
    """
    __tablename__ = "system_recoveries"
    __table_args__ = (
        Index('idx_cp_recovery_org_status', 'org_id', 'status'),
        Index('idx_cp_recovery_started', 'started_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Recovery identification
    recovery_name = Column(String(500), nullable=False)
    recovery_type = Column(String(50), nullable=False)  # full, partial, granular
    system_component = Column(String(255), nullable=False)
    
    # Incident details
    incident_description = Column(Text, nullable=True)
    incident_type = Column(String(100), nullable=True)  # data_loss, corruption, outage, etc.
    
    # Recovery source
    backup_id = Column(Integer, ForeignKey("system_backups.id", ondelete="SET NULL"), nullable=True)
    recovery_source = Column(String(1000), nullable=False)  # Backup location or source
    
    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default=RecoveryStatus.NOT_STARTED.value, index=True)
    
    # RPO/RTO
    target_rpo_minutes = Column(Integer, nullable=True)  # Recovery Point Objective
    target_rto_minutes = Column(Integer, nullable=True)  # Recovery Time Objective
    actual_rpo_minutes = Column(Integer, nullable=True)
    actual_rto_minutes = Column(Integer, nullable=True)
    
    # Recovery procedures
    recovery_procedures = Column(Text, nullable=True)
    recovery_steps = Column(JSON, nullable=True)  # List of steps taken
    recovery_result = Column(Text, nullable=True)
    
    # Verification
    verification_status = Column(String(50), nullable=True)  # verified, failed, pending
    verification_time = Column(DateTime(timezone=True), nullable=True)
    verification_result = Column(Text, nullable=True)
    
    # Initiator
    initiated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RecoveryTest(Base):
    """
    CP-10: Recovery Test
    
    Tracks recovery testing procedures and results.
    """
    __tablename__ = "recovery_tests"
    __table_args__ = (
        Index('idx_cp_rtest_org_status', 'org_id', 'status'),
        Index('idx_cp_rtest_scheduled', 'scheduled_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Test identification
    test_name = Column(String(500), nullable=False)
    test_type = Column(String(100), nullable=False)  # full, partial, granular
    system_component = Column(String(255), nullable=False)
    
    # Schedule
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status and results
    status = Column(String(50), nullable=False, default=TestStatus.SCHEDULED.value, index=True)
    test_result = Column(String(50), nullable=True)  # pass, fail, partial
    
    # Test details
    test_procedures = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)
    test_report_path = Column(String(1000), nullable=True)
    
    # RPO/RTO validation
    target_rpo_minutes = Column(Integer, nullable=True)
    target_rto_minutes = Column(Integer, nullable=True)
    actual_rpo_minutes = Column(Integer, nullable=True)
    actual_rto_minutes = Column(Integer, nullable=True)
    rpo_met = Column(Boolean, nullable=True)
    rto_met = Column(Boolean, nullable=True)
    
    # Issues and improvements
    issues_identified = Column(JSON, nullable=True)
    improvements_needed = Column(Text, nullable=True)
    
    # Participants
    test_team = Column(JSON, nullable=True)
    conducted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    classification = Column(String(50), default="NON_PHI")
    training_mode = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
