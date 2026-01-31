"""
Personnel Security (PS) Models for FedRAMP Compliance

Implements:
- PS-2: Position Risk Designation
- PS-3: Personnel Screening
- PS-4: Personnel Termination
- PS-5: Personnel Transfer
- PS-6: Access Agreements
- PS-7: Third-Party Personnel Security
- PS-8: Personnel Sanctions
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Date, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum
from core.database import Base


class PositionRiskLevel(str, Enum):
    """Position risk levels per FedRAMP PS-2"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ScreeningStatus(str, Enum):
    """Screening status per FedRAMP PS-3"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TerminationStatus(str, Enum):
    """Termination workflow status per FedRAMP PS-4"""
    INITIATED = "initiated"
    ACCESS_REVOKED = "access_revoked"
    EXIT_INTERVIEW_COMPLETED = "exit_interview_completed"
    ASSETS_RETURNED = "assets_returned"
    COMPLETED = "completed"


class TransferStatus(str, Enum):
    """Transfer workflow status per FedRAMP PS-5"""
    INITIATED = "initiated"
    ACCESS_ADJUSTED = "access_adjusted"
    ROLE_UPDATED = "role_updated"
    COMPLETED = "completed"


class AgreementStatus(str, Enum):
    """Access agreement status per FedRAMP PS-6"""
    PENDING = "pending"
    SIGNED = "signed"
    EXPIRED = "expired"
    RENEWED = "renewed"


class ThirdPartyStatus(str, Enum):
    """Third-party personnel status per FedRAMP PS-7"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class SanctionStatus(str, Enum):
    """Sanction status per FedRAMP PS-8"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    APPEALED = "appealed"
    CLOSED = "closed"


# ============================================================================
# PS-2: Position Risk Designation
# ============================================================================

class PositionRiskDesignation(Base):
    """PS-2: Position Risk Designation"""
    __tablename__ = "position_risk_designations"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    position_title = Column(String, nullable=False, index=True)
    position_id = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, nullable=False)
    
    risk_level = Column(SQLEnum(PositionRiskLevel), nullable=False, index=True)
    risk_justification = Column(Text, nullable=False)
    
    # Review tracking
    last_review_date = Column(Date, nullable=False)
    next_review_date = Column(Date, nullable=False, index=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Additional metadata
    requires_clearance = Column(Boolean, default=False)
    clearance_level = Column(String, nullable=True)
    special_requirements = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_position_risk_org_position', 'org_id', 'position_id'),
    )


# ============================================================================
# PS-3: Personnel Screening
# ============================================================================

class PersonnelScreening(Base):
    """PS-3: Personnel Screening"""
    __tablename__ = "personnel_screenings"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    position_risk_id = Column(Integer, ForeignKey("position_risk_designations.id"), nullable=False)
    
    screening_type = Column(String, nullable=False)  # initial, periodic, rescreening
    status = Column(SQLEnum(ScreeningStatus), default=ScreeningStatus.PENDING, index=True)
    
    # Screening requirements
    background_check_required = Column(Boolean, default=True)
    background_check_completed = Column(Boolean, default=False)
    background_check_date = Column(Date, nullable=True)
    background_check_result = Column(String, nullable=True)
    
    credit_check_required = Column(Boolean, default=False)
    credit_check_completed = Column(Boolean, default=False)
    credit_check_date = Column(Date, nullable=True)
    
    drug_test_required = Column(Boolean, default=False)
    drug_test_completed = Column(Boolean, default=False)
    drug_test_date = Column(Date, nullable=True)
    drug_test_result = Column(String, nullable=True)
    
    reference_check_required = Column(Boolean, default=True)
    reference_check_completed = Column(Boolean, default=False)
    reference_check_date = Column(Date, nullable=True)
    
    # Dates
    screening_initiated_date = Column(Date, nullable=False)
    screening_completed_date = Column(Date, nullable=True)
    screening_expiration_date = Column(Date, nullable=True, index=True)
    
    # Rescreening
    rescreening_required = Column(Boolean, default=True)
    rescreening_frequency_months = Column(Integer, default=36)
    next_rescreening_date = Column(Date, nullable=True, index=True)
    
    # Results and notes
    screening_result = Column(Text, nullable=True)
    screening_notes = Column(Text, nullable=True)
    screening_officer_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_screening_org_user', 'org_id', 'user_id'),
        Index('ix_screening_expiration', 'screening_expiration_date'),
    )


# ============================================================================
# PS-4: Personnel Termination
# ============================================================================

class PersonnelTermination(Base):
    """PS-4: Personnel Termination"""
    __tablename__ = "personnel_terminations"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    termination_date = Column(Date, nullable=False, index=True)
    termination_reason = Column(String, nullable=False)  # resignation, termination, retirement, etc.
    termination_type = Column(String, nullable=False)  # voluntary, involuntary, retirement
    
    status = Column(SQLEnum(TerminationStatus), default=TerminationStatus.INITIATED, index=True)
    
    # Access revocation
    access_revoked_at = Column(DateTime, nullable=True)
    access_revoked_by_user_id = Column(Integer, ForeignKey("users.id"))
    systems_access_revoked = Column(JSON, nullable=True)  # List of systems
    
    # Exit interview
    exit_interview_required = Column(Boolean, default=True)
    exit_interview_completed = Column(Boolean, default=False)
    exit_interview_date = Column(Date, nullable=True)
    exit_interview_notes = Column(Text, nullable=True)
    exit_interview_conducted_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Asset return
    assets_returned = Column(Boolean, default=False)
    assets_returned_date = Column(Date, nullable=True)
    assets_list = Column(JSON, nullable=True)  # List of assets to return
    assets_returned_list = Column(JSON, nullable=True)  # List of assets returned
    
    # Additional information
    final_paycheck_processed = Column(Boolean, default=False)
    benefits_terminated = Column(Boolean, default=False)
    cobra_notification_sent = Column(Boolean, default=False)
    
    termination_initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    termination_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_termination_org_user', 'org_id', 'user_id'),
        Index('ix_termination_date', 'termination_date'),
    )


# ============================================================================
# PS-5: Personnel Transfer
# ============================================================================

class PersonnelTransfer(Base):
    """PS-5: Personnel Transfer"""
    __tablename__ = "personnel_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    transfer_date = Column(Date, nullable=False, index=True)
    transfer_reason = Column(String, nullable=False)
    
    # From position
    from_position_id = Column(Integer, ForeignKey("position_risk_designations.id"), nullable=True)
    from_department = Column(String, nullable=True)
    from_role = Column(String, nullable=True)
    
    # To position
    to_position_id = Column(Integer, ForeignKey("position_risk_designations.id"), nullable=False)
    to_department = Column(String, nullable=False)
    to_role = Column(String, nullable=False)
    
    status = Column(SQLEnum(TransferStatus), default=TransferStatus.INITIATED, index=True)
    
    # Access adjustments
    access_adjusted_at = Column(DateTime, nullable=True)
    access_adjusted_by_user_id = Column(Integer, ForeignKey("users.id"))
    access_changes = Column(JSON, nullable=True)  # List of access changes
    
    # Role changes
    role_updated_at = Column(DateTime, nullable=True)
    role_updated_by_user_id = Column(Integer, ForeignKey("users.id"))
    role_changes = Column(JSON, nullable=True)  # List of role changes
    
    # Additional information
    requires_new_screening = Column(Boolean, default=False)
    new_screening_id = Column(Integer, ForeignKey("personnel_screenings.id"), nullable=True)
    
    transfer_initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transfer_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_transfer_org_user', 'org_id', 'user_id'),
        Index('ix_transfer_date', 'transfer_date'),
    )


# ============================================================================
# PS-6: Access Agreements
# ============================================================================

class AccessAgreement(Base):
    """PS-6: Access Agreements"""
    __tablename__ = "access_agreements"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    agreement_type = Column(String, nullable=False, index=True)  # NDA, confidentiality, acceptable_use, etc.
    agreement_title = Column(String, nullable=False)
    agreement_version = Column(String, nullable=False)
    
    status = Column(SQLEnum(AgreementStatus), default=AgreementStatus.PENDING, index=True)
    
    # Signature tracking
    signed_at = Column(DateTime, nullable=True)
    signed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signature_method = Column(String, nullable=True)  # electronic, physical, digital
    
    # Renewal tracking
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True, index=True)
    requires_renewal = Column(Boolean, default=True)
    renewal_frequency_months = Column(Integer, default=12)
    next_renewal_date = Column(Date, nullable=True, index=True)
    
    # Document tracking
    agreement_document_path = Column(String, nullable=True)
    signed_document_path = Column(String, nullable=True)
    
    # Additional information
    agreement_content_hash = Column(String, nullable=True)  # For integrity verification
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_agreement_org_user', 'org_id', 'user_id'),
        Index('ix_agreement_expiration', 'expiration_date'),
        Index('ix_agreement_renewal', 'next_renewal_date'),
    )


# ============================================================================
# PS-7: Third-Party Personnel Security
# ============================================================================

class ThirdPartyPersonnel(Base):
    """PS-7: Third-Party Personnel Security"""
    __tablename__ = "third_party_personnel"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Third-party information
    vendor_name = Column(String, nullable=False, index=True)
    vendor_contact_name = Column(String, nullable=False)
    vendor_contact_email = Column(String, nullable=False)
    vendor_contact_phone = Column(String, nullable=True)
    
    # Personnel information
    personnel_name = Column(String, nullable=False)
    personnel_email = Column(String, nullable=False, index=True)
    personnel_phone = Column(String, nullable=True)
    personnel_role = Column(String, nullable=False)
    
    # Contract information
    contract_number = Column(String, nullable=True, index=True)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date, nullable=True, index=True)
    
    # Security requirements
    security_clearance_required = Column(Boolean, default=False)
    security_clearance_level = Column(String, nullable=True)
    security_clearance_verified = Column(Boolean, default=False)
    
    background_check_required = Column(Boolean, default=True)
    background_check_completed = Column(Boolean, default=False)
    background_check_date = Column(Date, nullable=True)
    
    nda_required = Column(Boolean, default=True)
    nda_signed = Column(Boolean, default=False)
    nda_signed_date = Column(Date, nullable=True)
    
    # Access and status
    system_access_granted = Column(Boolean, default=False)
    systems_accessed = Column(JSON, nullable=True)  # List of systems
    access_granted_date = Column(Date, nullable=True)
    access_revoked_date = Column(Date, nullable=True)
    
    status = Column(SQLEnum(ThirdPartyStatus), default=ThirdPartyStatus.ACTIVE, index=True)
    
    # Compliance tracking
    compliance_verified = Column(Boolean, default=False)
    compliance_verified_date = Column(Date, nullable=True)
    compliance_verified_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Additional information
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_third_party_org_vendor', 'org_id', 'vendor_name'),
        Index('ix_third_party_contract', 'contract_end_date'),
    )


# ============================================================================
# PS-8: Personnel Sanctions
# ============================================================================

class PersonnelSanction(Base):
    """PS-8: Personnel Sanctions"""
    __tablename__ = "personnel_sanctions"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    violation_type = Column(String, nullable=False, index=True)  # security_violation, policy_violation, etc.
    violation_description = Column(Text, nullable=False)
    violation_date = Column(Date, nullable=False, index=True)
    
    sanction_type = Column(String, nullable=False)  # warning, suspension, termination, etc.
    sanction_severity = Column(String, nullable=False)  # low, medium, high, critical
    
    status = Column(SQLEnum(SanctionStatus), default=SanctionStatus.ACTIVE, index=True)
    
    # Sanction details
    sanction_start_date = Column(Date, nullable=False)
    sanction_end_date = Column(Date, nullable=True)
    sanction_conditions = Column(Text, nullable=True)
    
    # Remediation
    remediation_required = Column(Boolean, default=True)
    remediation_plan = Column(Text, nullable=True)
    remediation_completed = Column(Boolean, default=False)
    remediation_completed_date = Column(Date, nullable=True)
    
    # Appeal
    appeal_filed = Column(Boolean, default=False)
    appeal_date = Column(Date, nullable=True)
    appeal_decision = Column(String, nullable=True)
    appeal_decision_date = Column(Date, nullable=True)
    
    # Documentation
    incident_report_path = Column(String, nullable=True)
    supporting_documents = Column(JSON, nullable=True)  # List of document paths
    
    # Personnel involved
    reported_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sanctioned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_sanction_org_user', 'org_id', 'user_id'),
        Index('ix_sanction_violation_date', 'violation_date'),
        Index('ix_sanction_status', 'status'),
    )
