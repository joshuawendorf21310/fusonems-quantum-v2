"""
Security Categorization Service for FedRAMP RA-2 Compliance

This service provides:
- FIPS 199 security categorization
- System-level categorization
- Data-level categorization
- Impact level determination
- Categorization review and approval workflow

FedRAMP RA-2: Security categorization of information systems.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.risk_assessment import (
    SystemCategorization,
    DataCategorization,
    ImpactLevel,
    SecurityObjective,
)
from utils.logger import logger


class SecurityCategorizationService:
    """
    Service for managing security categorizations per FIPS 199.
    
    FIPS 199 defines three security objectives:
    - Confidentiality: Preserving authorized restrictions on information access
    - Integrity: Guarding against improper information modification
    - Availability: Ensuring timely and reliable access to information
    
    Each objective is categorized as LOW, MODERATE, or HIGH impact.
    The overall system impact level is the highest of the three.
    """
    
    # FIPS 199 Impact Level Definitions
    IMPACT_DEFINITIONS = {
        ImpactLevel.LOW: {
            SecurityObjective.CONFIDENTIALITY: "The unauthorized disclosure of information could be expected to have a limited adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.INTEGRITY: "The unauthorized modification or destruction of information could be expected to have a limited adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.AVAILABILITY: "The disruption of access to or use of information or an information system could be expected to have a limited adverse effect on organizational operations, organizational assets, or individuals.",
        },
        ImpactLevel.MODERATE: {
            SecurityObjective.CONFIDENTIALITY: "The unauthorized disclosure of information could be expected to have a serious adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.INTEGRITY: "The unauthorized modification or destruction of information could be expected to have a serious adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.AVAILABILITY: "The disruption of access to or use of information or an information system could be expected to have a serious adverse effect on organizational operations, organizational assets, or individuals.",
        },
        ImpactLevel.HIGH: {
            SecurityObjective.CONFIDENTIALITY: "The unauthorized disclosure of information could be expected to have a severe or catastrophic adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.INTEGRITY: "The unauthorized modification or destruction of information could be expected to have a severe or catastrophic adverse effect on organizational operations, organizational assets, or individuals.",
            SecurityObjective.AVAILABILITY: "The disruption of access to or use of information or an information system could be expected to have a severe or catastrophic adverse effect on organizational operations, organizational assets, or individuals.",
        },
    }
    
    def __init__(self, db: Session):
        """
        Initialize security categorization service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def calculate_overall_impact_level(
        self,
        confidentiality: ImpactLevel,
        integrity: ImpactLevel,
        availability: ImpactLevel
    ) -> ImpactLevel:
        """
        Calculate overall system impact level per FIPS 199.
        
        The overall impact level is the highest of the three security objectives.
        
        Args:
            confidentiality: Confidentiality impact level
            integrity: Integrity impact level
            availability: Availability impact level
            
        Returns:
            Overall impact level
        """
        # Convert to numeric values for comparison
        level_values = {
            ImpactLevel.LOW: 1,
            ImpactLevel.MODERATE: 2,
            ImpactLevel.HIGH: 3,
        }
        
        max_level = max(
            level_values.get(confidentiality, 1),
            level_values.get(integrity, 1),
            level_values.get(availability, 1)
        )
        
        # Convert back to enum
        for level, value in level_values.items():
            if value == max_level:
                return level
        
        return ImpactLevel.LOW
    
    def create_system_categorization(
        self,
        system_name: str,
        confidentiality_impact: ImpactLevel,
        integrity_impact: ImpactLevel,
        availability_impact: ImpactLevel,
        system_description: Optional[str] = None,
        system_owner: Optional[str] = None,
        system_id: Optional[str] = None,
        categorization_rationale: Optional[str] = None,
        categorized_by: Optional[str] = None,
    ) -> SystemCategorization:
        """
        Create a new system categorization.
        
        Args:
            system_name: Name of the system
            confidentiality_impact: Confidentiality impact level
            integrity_impact: Integrity impact level
            availability_impact: Availability impact level
            system_description: Description of the system
            system_owner: Owner of the system
            system_id: Unique system identifier
            categorization_rationale: Rationale for categorization
            categorized_by: Person who performed categorization
            
        Returns:
            Created SystemCategorization record
        """
        # Calculate overall impact level
        overall_impact = self.calculate_overall_impact_level(
            confidentiality_impact,
            integrity_impact,
            availability_impact
        )
        
        categorization = SystemCategorization(
            system_name=system_name,
            system_description=system_description,
            system_owner=system_owner,
            system_id=system_id,
            confidentiality_impact=confidentiality_impact.value,
            integrity_impact=integrity_impact.value,
            availability_impact=availability_impact.value,
            overall_impact_level=overall_impact.value,
            categorization_rationale=categorization_rationale,
            categorized_by=categorized_by,
            categorization_date=datetime.utcnow(),
        )
        
        self.db.add(categorization)
        self.db.commit()
        self.db.refresh(categorization)
        
        logger.info(
            f"Created system categorization: {system_name}",
            extra={
                "system_categorization_id": categorization.id,
                "overall_impact_level": overall_impact.value,
                "event_type": "security.categorization.system.created",
            }
        )
        
        return categorization
    
    def update_system_categorization(
        self,
        categorization_id: int,
        confidentiality_impact: Optional[ImpactLevel] = None,
        integrity_impact: Optional[ImpactLevel] = None,
        availability_impact: Optional[ImpactLevel] = None,
        system_name: Optional[str] = None,
        system_description: Optional[str] = None,
        categorization_rationale: Optional[str] = None,
    ) -> Optional[SystemCategorization]:
        """
        Update an existing system categorization.
        
        Args:
            categorization_id: ID of the categorization to update
            confidentiality_impact: New confidentiality impact level
            integrity_impact: New integrity impact level
            availability_impact: New availability impact level
            system_name: New system name
            system_description: New system description
            categorization_rationale: New rationale
            
        Returns:
            Updated SystemCategorization or None if not found
        """
        categorization = self.db.query(SystemCategorization).filter(
            SystemCategorization.id == categorization_id
        ).first()
        
        if not categorization:
            return None
        
        # Update fields
        if system_name:
            categorization.system_name = system_name
        if system_description is not None:
            categorization.system_description = system_description
        if categorization_rationale is not None:
            categorization.categorization_rationale = categorization_rationale
        
        # Update impact levels if provided
        needs_recalculation = False
        if confidentiality_impact:
            categorization.confidentiality_impact = confidentiality_impact.value
            needs_recalculation = True
        if integrity_impact:
            categorization.integrity_impact = integrity_impact.value
            needs_recalculation = True
        if availability_impact:
            categorization.availability_impact = availability_impact.value
            needs_recalculation = True
        
        # Recalculate overall impact level if any impact level changed
        if needs_recalculation:
            overall_impact = self.calculate_overall_impact_level(
                ImpactLevel(categorization.confidentiality_impact),
                ImpactLevel(categorization.integrity_impact),
                ImpactLevel(categorization.availability_impact)
            )
            categorization.overall_impact_level = overall_impact.value
        
        categorization.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(categorization)
        
        logger.info(
            f"Updated system categorization: {categorization.system_name}",
            extra={
                "system_categorization_id": categorization.id,
                "event_type": "security.categorization.system.updated",
            }
        )
        
        return categorization
    
    def create_data_categorization(
        self,
        system_categorization_id: int,
        data_type: str,
        confidentiality_impact: ImpactLevel,
        integrity_impact: ImpactLevel,
        availability_impact: ImpactLevel,
        data_description: Optional[str] = None,
        data_classification: Optional[str] = None,
        categorization_rationale: Optional[str] = None,
        categorized_by: Optional[str] = None,
        data_volume: Optional[str] = None,
        sensitivity_notes: Optional[str] = None,
    ) -> DataCategorization:
        """
        Create a new data categorization.
        
        Args:
            system_categorization_id: ID of the parent system categorization
            data_type: Type of data (e.g., "PHI", "PII", "Financial")
            confidentiality_impact: Confidentiality impact level
            integrity_impact: Integrity impact level
            availability_impact: Availability impact level
            data_description: Description of the data
            data_classification: Classification of the data
            categorization_rationale: Rationale for categorization
            categorized_by: Person who performed categorization
            data_volume: Volume of data
            sensitivity_notes: Notes on data sensitivity
            
        Returns:
            Created DataCategorization record
        """
        # Calculate overall impact level
        overall_impact = self.calculate_overall_impact_level(
            confidentiality_impact,
            integrity_impact,
            availability_impact
        )
        
        categorization = DataCategorization(
            system_categorization_id=system_categorization_id,
            data_type=data_type,
            data_description=data_description,
            data_classification=data_classification,
            confidentiality_impact=confidentiality_impact.value,
            integrity_impact=integrity_impact.value,
            availability_impact=availability_impact.value,
            overall_impact_level=overall_impact.value,
            categorization_rationale=categorization_rationale,
            categorized_by=categorized_by,
            data_volume=data_volume,
            sensitivity_notes=sensitivity_notes,
            categorization_date=datetime.utcnow(),
        )
        
        self.db.add(categorization)
        self.db.commit()
        self.db.refresh(categorization)
        
        logger.info(
            f"Created data categorization: {data_type}",
            extra={
                "data_categorization_id": categorization.id,
                "system_categorization_id": system_categorization_id,
                "overall_impact_level": overall_impact.value,
                "event_type": "security.categorization.data.created",
            }
        )
        
        return categorization
    
    def get_system_categorization(self, categorization_id: int) -> Optional[SystemCategorization]:
        """
        Get system categorization by ID.
        
        Args:
            categorization_id: ID of the categorization
            
        Returns:
            SystemCategorization or None if not found
        """
        return self.db.query(SystemCategorization).filter(
            SystemCategorization.id == categorization_id
        ).first()
    
    def list_system_categorizations(
        self,
        is_active: Optional[bool] = True,
        overall_impact_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[SystemCategorization], int]:
        """
        List system categorizations with filters.
        
        Args:
            is_active: Filter by active status
            overall_impact_level: Filter by overall impact level
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (categorizations list, total count)
        """
        query = self.db.query(SystemCategorization)
        
        if is_active is not None:
            query = query.filter(SystemCategorization.is_active == is_active)
        
        if overall_impact_level:
            query = query.filter(SystemCategorization.overall_impact_level == overall_impact_level)
        
        total = query.count()
        categorizations = query.order_by(
            SystemCategorization.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return categorizations, total
    
    def get_data_categorizations(
        self,
        system_categorization_id: int,
        is_active: Optional[bool] = True
    ) -> List[DataCategorization]:
        """
        Get data categorizations for a system.
        
        Args:
            system_categorization_id: ID of the system categorization
            is_active: Filter by active status
            
        Returns:
            List of DataCategorization records
        """
        query = self.db.query(DataCategorization).filter(
            DataCategorization.system_categorization_id == system_categorization_id
        )
        
        if is_active is not None:
            query = query.filter(DataCategorization.is_active == is_active)
        
        return query.order_by(DataCategorization.created_at.desc()).all()
    
    def review_system_categorization(
        self,
        categorization_id: int,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> Optional[SystemCategorization]:
        """
        Mark a system categorization as reviewed.
        
        Args:
            categorization_id: ID of the categorization
            reviewed_by: Person who reviewed
            review_notes: Review notes
            
        Returns:
            Updated SystemCategorization or None if not found
        """
        categorization = self.get_system_categorization(categorization_id)
        if not categorization:
            return None
        
        categorization.review_date = datetime.utcnow()
        categorization.reviewed_by = reviewed_by
        if review_notes:
            categorization.categorization_rationale = (
                (categorization.categorization_rationale or "") + "\n\nReview Notes: " + review_notes
            )
        
        self.db.commit()
        self.db.refresh(categorization)
        
        return categorization
    
    def approve_system_categorization(
        self,
        categorization_id: int,
        approved_by: str
    ) -> Optional[SystemCategorization]:
        """
        Approve a system categorization.
        
        Args:
            categorization_id: ID of the categorization
            approved_by: Person who approved
            
        Returns:
            Updated SystemCategorization or None if not found
        """
        categorization = self.get_system_categorization(categorization_id)
        if not categorization:
            return None
        
        categorization.approval_date = datetime.utcnow()
        categorization.approved_by = approved_by
        
        self.db.commit()
        self.db.refresh(categorization)
        
        logger.info(
            f"Approved system categorization: {categorization.system_name}",
            extra={
                "system_categorization_id": categorization.id,
                "approved_by": approved_by,
                "event_type": "security.categorization.system.approved",
            }
        )
        
        return categorization
    
    def generate_categorization_report(self) -> Dict:
        """
        Generate FIPS 199 categorization compliance report.
        
        Returns:
            Dictionary with categorization report data
        """
        # Get all active system categorizations
        systems, total_systems = self.list_system_categorizations(is_active=True, limit=1000)
        
        # Count by impact level
        by_impact_level = {}
        for level in ImpactLevel:
            count = sum(1 for s in systems if s.overall_impact_level == level.value)
            by_impact_level[level.value] = count
        
        # Get data categorizations
        total_data_types = 0
        data_by_impact_level = {}
        for system in systems:
            data_cats = self.get_data_categorizations(system.id, is_active=True)
            total_data_types += len(data_cats)
            for data_cat in data_cats:
                level = data_cat.overall_impact_level
                data_by_impact_level[level] = data_by_impact_level.get(level, 0) + 1
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "total_systems": total_systems,
            "systems_by_impact_level": by_impact_level,
            "total_data_types": total_data_types,
            "data_by_impact_level": data_by_impact_level,
            "compliance_status": "compliant" if total_systems > 0 else "needs_categorization",
        }
