"""
Risk Assessment Models for FedRAMP RA-2, RA-3, RA-6 Compliance

This module provides models for:
- RA-2: Security Categorization (FIPS 199)
- RA-3: Risk Assessment
- RA-6: Technical Surveillance Countermeasures
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
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
# RA-2: Security Categorization (FIPS 199)
# ============================================================================

class ImpactLevel(str, Enum):
    """FIPS 199 Impact Levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SecurityObjective(str, Enum):
    """FIPS 199 Security Objectives"""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"


class SystemCategorization(Base):
    """
    System-level security categorization per FIPS 199.
    
    FedRAMP RA-2: Security categorization of information systems.
    """
    __tablename__ = "system_categorizations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # System Information
    system_name = Column(String(255), nullable=False, index=True)
    system_description = Column(Text, nullable=True)
    system_owner = Column(String(255), nullable=True)
    system_id = Column(String(128), nullable=True, unique=True, index=True)
    
    # FIPS 199 Categorization
    confidentiality_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    integrity_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    availability_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    
    # Overall System Impact Level (highest of the three)
    overall_impact_level = Column(
        String(32),
        nullable=False,
        index=True
    )
    
    # Categorization Details
    categorization_rationale = Column(Text, nullable=True)
    categorization_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    categorized_by = Column(String(255), nullable=True)
    
    # Review and Approval
    review_date = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    data_categorizations = relationship("DataCategorization", back_populates="system")
    
    __table_args__ = (
        Index("idx_system_cat_impact", "overall_impact_level", "is_active"),
    )


class DataCategorization(Base):
    """
    Data-level security categorization per FIPS 199.
    
    FedRAMP RA-2: Security categorization of information types.
    """
    __tablename__ = "data_categorizations"
    
    id = Column(Integer, primary_key=True, index=True)
    system_categorization_id = Column(
        Integer,
        ForeignKey("system_categorizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Data Information
    data_type = Column(String(255), nullable=False, index=True)  # e.g., "PHI", "PII", "Financial"
    data_description = Column(Text, nullable=True)
    data_classification = Column(String(100), nullable=True)  # e.g., "PHI", "NON_PHI", "PII"
    
    # FIPS 199 Categorization
    confidentiality_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    integrity_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    availability_impact = Column(
        String(32),
        nullable=False,
        default=ImpactLevel.LOW.value,
        index=True
    )
    
    # Overall Data Impact Level
    overall_impact_level = Column(
        String(32),
        nullable=False,
        index=True
    )
    
    # Categorization Details
    categorization_rationale = Column(Text, nullable=True)
    categorization_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    categorized_by = Column(String(255), nullable=True)
    
    # Volume and Sensitivity
    data_volume = Column(String(100), nullable=True)  # e.g., "high", "medium", "low"
    sensitivity_notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    system = relationship("SystemCategorization", back_populates="data_categorizations")
    
    __table_args__ = (
        Index("idx_data_cat_system", "system_categorization_id", "data_type"),
        Index("idx_data_cat_impact", "overall_impact_level", "is_active"),
    )


# ============================================================================
# RA-3: Risk Assessment
# ============================================================================

class RiskLevel(str, Enum):
    """Risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class LikelihoodLevel(str, Enum):
    """Likelihood levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class RiskImpactLevel(str, Enum):
    """Risk impact levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class ThreatCategory(str, Enum):
    """Threat categories"""
    MALICIOUS_INSIDER = "malicious_insider"
    EXTERNAL_ATTACKER = "external_attacker"
    NATURAL_DISASTER = "natural_disaster"
    SYSTEM_FAILURE = "system_failure"
    HUMAN_ERROR = "human_error"
    SUPPLY_CHAIN = "supply_chain"
    ADVANCED_PERSISTENT_THREAT = "apt"
    OTHER = "other"


class VulnerabilityCategory(str, Enum):
    """Vulnerability categories"""
    SOFTWARE = "software"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PHYSICAL = "physical"
    PROCESS = "process"
    PERSONNEL = "personnel"
    OTHER = "other"


class TreatmentStrategy(str, Enum):
    """Risk treatment strategies"""
    ACCEPT = "accept"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    AVOID = "avoid"


class RiskAssessment(Base):
    """
    Comprehensive risk assessment record.
    
    FedRAMP RA-3: Risk assessment process.
    """
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Assessment Information
    assessment_name = Column(String(255), nullable=False, index=True)
    assessment_description = Column(Text, nullable=True)
    assessment_type = Column(String(100), nullable=False)  # "initial", "periodic", "ad_hoc"
    
    # Scope
    scope_description = Column(Text, nullable=True)
    systems_in_scope = Column(JSON, nullable=True)  # List of system IDs
    data_types_in_scope = Column(JSON, nullable=True)  # List of data types
    
    # Assessment Details
    assessment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    assessed_by = Column(String(255), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    # Overall Risk Level
    overall_risk_level = Column(String(32), nullable=False, index=True)
    overall_risk_score = Column(Float, nullable=True)  # Calculated risk score
    
    # Summary
    executive_summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)  # List of key findings
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Status
    status = Column(String(32), nullable=False, default="draft", index=True)  # "draft", "in_review", "approved", "superseded"
    
    # Next Assessment
    next_assessment_due = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    risk_factors = relationship("RiskFactor", back_populates="assessment", cascade="all, delete-orphan")
    treatment_plans = relationship("TreatmentPlan", back_populates="assessment", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_risk_assessment_status_date", "status", "assessment_date"),
        Index("idx_risk_assessment_level", "overall_risk_level", "status"),
    )


class RiskFactor(Base):
    """
    Individual risk factor identified in a risk assessment.
    
    Represents a threat-vulnerability pair with associated risk.
    """
    __tablename__ = "risk_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_assessment_id = Column(
        Integer,
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Risk Identification
    risk_name = Column(String(255), nullable=False, index=True)
    risk_description = Column(Text, nullable=True)
    
    # Threat Information
    threat_category = Column(String(100), nullable=False, index=True)
    threat_description = Column(Text, nullable=True)
    threat_source = Column(String(255), nullable=True)
    threat_capability = Column(String(100), nullable=True)  # "low", "medium", "high", "very_high"
    
    # Vulnerability Information
    vulnerability_category = Column(String(100), nullable=False, index=True)
    vulnerability_description = Column(Text, nullable=True)
    vulnerability_id = Column(String(128), nullable=True)  # Reference to CVE or other vulnerability ID
    affected_systems = Column(JSON, nullable=True)  # List of affected system IDs
    
    # Risk Calculation
    likelihood = Column(String(32), nullable=False, index=True)
    likelihood_score = Column(Float, nullable=True)  # Numeric likelihood score
    impact = Column(String(32), nullable=False, index=True)
    impact_score = Column(Float, nullable=True)  # Numeric impact score
    risk_level = Column(String(32), nullable=False, index=True)
    risk_score = Column(Float, nullable=True)  # Calculated: likelihood × impact
    
    # Risk Details
    risk_scenario = Column(Text, nullable=True)  # Description of risk scenario
    potential_impact = Column(Text, nullable=True)  # Description of potential impact
    existing_controls = Column(JSON, nullable=True)  # List of existing controls
    control_effectiveness = Column(String(100), nullable=True)  # "effective", "partially_effective", "ineffective"
    
    # Status
    status = Column(String(32), nullable=False, default="open", index=True)  # "open", "mitigated", "accepted", "transferred", "avoided"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    assessment = relationship("RiskAssessment", back_populates="risk_factors")
    treatment_plans = relationship("TreatmentPlan", back_populates="risk_factor")
    
    __table_args__ = (
        Index("idx_risk_factor_assessment_status", "risk_assessment_id", "status"),
        Index("idx_risk_factor_level", "risk_level", "status"),
        Index("idx_risk_factor_threat_vuln", "threat_category", "vulnerability_category"),
    )


class TreatmentPlan(Base):
    """
    Risk treatment plan for addressing identified risks.
    
    FedRAMP RA-3: Risk treatment planning.
    """
    __tablename__ = "treatment_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_assessment_id = Column(
        Integer,
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    risk_factor_id = Column(
        Integer,
        ForeignKey("risk_factors.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Treatment Information
    plan_name = Column(String(255), nullable=False, index=True)
    plan_description = Column(Text, nullable=True)
    treatment_strategy = Column(String(32), nullable=False, index=True)
    
    # Treatment Details
    treatment_actions = Column(JSON, nullable=True)  # List of treatment actions
    responsible_party = Column(String(255), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Implementation Status
    implementation_status = Column(String(32), nullable=False, default="planned", index=True)  # "planned", "in_progress", "completed", "cancelled"
    implementation_progress = Column(Float, nullable=True, default=0.0)  # 0.0 to 1.0
    implementation_notes = Column(Text, nullable=True)
    
    # Effectiveness
    residual_risk_level = Column(String(32), nullable=True)
    residual_risk_score = Column(Float, nullable=True)
    effectiveness_assessment = Column(Text, nullable=True)
    
    # Cost and Resources
    estimated_cost = Column(Float, nullable=True)
    resources_required = Column(JSON, nullable=True)  # List of required resources
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assessment = relationship("RiskAssessment", back_populates="treatment_plans")
    risk_factor = relationship("RiskFactor", back_populates="treatment_plans")
    
    __table_args__ = (
        Index("idx_treatment_plan_assessment_status", "risk_assessment_id", "implementation_status"),
        Index("idx_treatment_plan_strategy", "treatment_strategy", "implementation_status"),
    )


# ============================================================================
# RA-6: Technical Surveillance Countermeasures
# ============================================================================

class SurveillanceType(str, Enum):
    """Types of surveillance events"""
    ELECTRONIC = "electronic"
    PHYSICAL = "physical"
    NETWORK = "network"
    COMMUNICATIONS = "communications"
    OTHER = "other"


class SurveillanceStatus(str, Enum):
    """Surveillance event status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"
    MITIGATED = "mitigated"


class CountermeasureType(str, Enum):
    """Types of countermeasures"""
    DETECTION = "detection"
    PREVENTION = "prevention"
    MONITORING = "monitoring"
    RESPONSE = "response"
    TRAINING = "training"
    OTHER = "other"


class SurveillanceEvent(Base):
    """
    Technical surveillance detection and countermeasure event.
    
    FedRAMP RA-6: Technical surveillance countermeasures.
    """
    __tablename__ = "surveillance_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event Information
    event_name = Column(String(255), nullable=False, index=True)
    event_description = Column(Text, nullable=True)
    surveillance_type = Column(String(100), nullable=False, index=True)
    
    # Detection Details
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    detected_by = Column(String(255), nullable=True)  # System or person
    detection_method = Column(String(255), nullable=True)  # How it was detected
    detection_source = Column(String(255), nullable=True)  # Source of detection
    
    # Location and Context
    location = Column(String(255), nullable=True)
    affected_systems = Column(JSON, nullable=True)  # List of affected system IDs
    affected_data = Column(JSON, nullable=True)  # List of affected data types
    
    # Threat Information
    threat_source = Column(String(255), nullable=True)
    threat_capability = Column(String(100), nullable=True)
    threat_intent = Column(String(100), nullable=True)
    
    # Impact Assessment
    potential_impact = Column(Text, nullable=True)
    data_exposed = Column(Boolean, nullable=False, default=False)
    systems_compromised = Column(Boolean, nullable=False, default=False)
    impact_level = Column(String(32), nullable=True)
    
    # Status and Response
    status = Column(String(32), nullable=False, default=SurveillanceStatus.DETECTED.value, index=True)
    response_actions = Column(JSON, nullable=True)  # List of response actions taken
    countermeasures_applied = Column(JSON, nullable=True)  # List of countermeasures applied
    
    # Investigation
    investigation_notes = Column(Text, nullable=True)
    investigated_by = Column(String(255), nullable=True)
    investigation_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    
    # Related Events
    related_events = Column(JSON, nullable=True)  # List of related event IDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index("idx_surveillance_type_status", "surveillance_type", "status"),
        Index("idx_surveillance_detected", "detected_at", "status"),
        Index("idx_surveillance_status", "status", "detected_at"),
    )
