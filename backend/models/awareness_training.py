"""
Awareness & Training (AT) Models for FedRAMP Compliance

Implements:
- AT-2: Security Awareness Training
- AT-3: Role-Based Security Training
- AT-4: Security Training Records
- AT-5: Contacts with Security Groups
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Date, Enum as SQLEnum, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum
from core.database import Base


class TrainingStatus(str, Enum):
    """Training status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TrainingDeliveryMethod(str, Enum):
    """Training delivery method"""
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"
    SELF_STUDY = "self_study"


class CompetencyLevel(str, Enum):
    """Competency validation level"""
    NOT_ASSESSED = "not_assessed"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContactType(str, Enum):
    """Security group contact type"""
    MEMBERSHIP = "membership"
    CONFERENCE = "conference"
    TRAINING = "training"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"


# ============================================================================
# AT-2: Security Awareness Training
# ============================================================================

class SecurityAwarenessTraining(Base):
    """AT-2: Security Awareness Training"""
    __tablename__ = "security_awareness_trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Training module information
    module_code = Column(String, unique=True, nullable=False, index=True)
    module_name = Column(String, nullable=False)
    module_description = Column(Text, nullable=True)
    module_category = Column(String, nullable=False)  # phishing, password_security, data_protection, etc.
    
    # Training content
    delivery_method = Column(SQLEnum(TrainingDeliveryMethod), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    training_content_path = Column(String, nullable=True)  # Path to training materials
    
    # Requirements
    mandatory = Column(Boolean, default=True, index=True)
    required_frequency_months = Column(Integer, default=12)  # How often training must be completed
    passing_score_percentage = Column(Float, default=80.0)
    
    # Reminders
    reminder_days_before_due = Column(JSON, nullable=True)  # [30, 15, 7] days before due
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_awareness_training_org_active', 'org_id', 'active'),
    )


class SecurityAwarenessTrainingAssignment(Base):
    """AT-2: Security Awareness Training Assignments"""
    __tablename__ = "security_awareness_training_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    training_id = Column(Integer, ForeignKey("security_awareness_trainings.id"), nullable=False)
    
    # Assignment details
    assigned_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(TrainingStatus), default=TrainingStatus.NOT_STARTED, index=True)
    
    # Completion tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    score_percentage = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    
    # Attempts
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    
    # Reminders
    reminder_sent_30_days = Column(Boolean, default=False)
    reminder_sent_15_days = Column(Boolean, default=False)
    reminder_sent_7_days = Column(Boolean, default=False)
    reminder_sent_overdue = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_awareness_assignment_org_user', 'org_id', 'user_id'),
        Index('ix_awareness_assignment_due', 'due_date'),
        Index('ix_awareness_assignment_status', 'status'),
    )


# ============================================================================
# AT-3: Role-Based Security Training
# ============================================================================

class RoleBasedSecurityTraining(Base):
    """AT-3: Role-Based Security Training"""
    __tablename__ = "role_based_security_trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Training information
    training_code = Column(String, unique=True, nullable=False, index=True)
    training_name = Column(String, nullable=False)
    training_description = Column(Text, nullable=True)
    training_category = Column(String, nullable=False)  # admin, developer, operator, etc.
    
    # Role requirements
    required_role = Column(String, nullable=False, index=True)  # UserRole enum value
    required_roles = Column(JSON, nullable=True)  # Multiple roles if needed
    
    # Training content
    delivery_method = Column(SQLEnum(TrainingDeliveryMethod), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    training_content_path = Column(String, nullable=True)
    
    # Requirements
    mandatory = Column(Boolean, default=True)
    required_frequency_months = Column(Integer, default=12)
    passing_score_percentage = Column(Float, default=80.0)
    
    # Competency validation
    requires_competency_validation = Column(Boolean, default=False)
    competency_level_required = Column(SQLEnum(CompetencyLevel), nullable=True)
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_role_training_org_role', 'org_id', 'required_role'),
    )


class RoleBasedTrainingAssignment(Base):
    """AT-3: Role-Based Training Assignments"""
    __tablename__ = "role_based_training_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    training_id = Column(Integer, ForeignKey("role_based_security_trainings.id"), nullable=False)
    
    # Assignment details
    assigned_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(TrainingStatus), default=TrainingStatus.NOT_STARTED, index=True)
    
    # Completion tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    score_percentage = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    
    # Competency validation
    competency_assessed = Column(Boolean, default=False)
    competency_level_achieved = Column(SQLEnum(CompetencyLevel), nullable=True)
    competency_assessed_at = Column(DateTime, nullable=True)
    competency_assessed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Attempts
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_role_assignment_org_user', 'org_id', 'user_id'),
        Index('ix_role_assignment_due', 'due_date'),
        Index('ix_role_assignment_status', 'status'),
    )


# ============================================================================
# AT-4: Security Training Records
# ============================================================================

class SecurityTrainingRecord(Base):
    """AT-4: Security Training Records"""
    __tablename__ = "security_training_records"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Training information
    training_type = Column(String, nullable=False, index=True)  # awareness, role_based, external, etc.
    training_name = Column(String, nullable=False)
    training_provider = Column(String, nullable=True)  # Internal or external provider
    training_code = Column(String, nullable=True, index=True)
    
    # Training details
    training_date = Column(Date, nullable=False, index=True)
    completion_date = Column(Date, nullable=True)
    delivery_method = Column(SQLEnum(TrainingDeliveryMethod), nullable=False)
    duration_hours = Column(Float, nullable=False)
    
    # Completion status
    status = Column(SQLEnum(TrainingStatus), nullable=False, index=True)
    score_percentage = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    
    # Certificate tracking
    certificate_issued = Column(Boolean, default=False)
    certificate_number = Column(String, nullable=True, index=True)
    certificate_issue_date = Column(Date, nullable=True)
    certificate_expiration_date = Column(Date, nullable=True, index=True)
    certificate_document_path = Column(String, nullable=True)
    
    # Competency validation
    competency_level_achieved = Column(SQLEnum(CompetencyLevel), nullable=True)
    competency_validated = Column(Boolean, default=False)
    competency_validated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # External training
    external_training = Column(Boolean, default=False)
    external_provider_name = Column(String, nullable=True)
    external_training_id = Column(String, nullable=True)
    
    # CEU/CME credits
    ceu_credits = Column(Float, default=0.0)
    cme_credits = Column(Float, default=0.0)
    
    # Compliance tracking
    compliance_required = Column(Boolean, default=True)
    compliance_status = Column(String, nullable=True)  # compliant, non_compliant, pending
    
    # Additional information
    notes = Column(Text, nullable=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_training_record_org_user', 'org_id', 'user_id'),
        Index('ix_training_record_date', 'training_date'),
        Index('ix_training_record_certificate', 'certificate_expiration_date'),
    )


# ============================================================================
# AT-5: Contacts with Security Groups
# ============================================================================

class SecurityGroupContact(Base):
    """AT-5: Contacts with Security Groups"""
    __tablename__ = "security_group_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Security group information
    security_group_name = Column(String, nullable=False, index=True)
    security_group_type = Column(String, nullable=False)  # professional, industry, government, etc.
    security_group_website = Column(String, nullable=True)
    security_group_contact_email = Column(String, nullable=True)
    
    # Contact type
    contact_type = Column(SQLEnum(ContactType), nullable=False, index=True)
    
    # Event information (for conferences, training, workshops)
    event_name = Column(String, nullable=True)
    event_date = Column(Date, nullable=True, index=True)
    event_location = Column(String, nullable=True)
    event_duration_days = Column(Integer, nullable=True)
    
    # Membership information
    membership_status = Column(String, nullable=True)  # active, inactive, expired
    membership_start_date = Column(Date, nullable=True)
    membership_end_date = Column(Date, nullable=True, index=True)
    membership_level = Column(String, nullable=True)  # member, associate, student, etc.
    
    # Participation details
    participation_role = Column(String, nullable=True)  # attendee, presenter, organizer, etc.
    presentation_title = Column(String, nullable=True)
    presentation_date = Column(Date, nullable=True)
    
    # Knowledge sharing
    knowledge_shared = Column(Boolean, default=False)
    knowledge_shared_date = Column(Date, nullable=True)
    knowledge_shared_summary = Column(Text, nullable=True)
    knowledge_shared_with_team = Column(Boolean, default=False)
    
    # Benefits and outcomes
    benefits_received = Column(Text, nullable=True)
    outcomes_achieved = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_security_contact_org_user', 'org_id', 'user_id'),
        Index('ix_security_contact_group', 'security_group_name'),
        Index('ix_security_contact_type', 'contact_type'),
        Index('ix_security_contact_event', 'event_date'),
    )
