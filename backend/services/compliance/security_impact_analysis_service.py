"""
Security Impact Analysis Service for FedRAMP CM-4 Compliance

FedRAMP Requirement CM-4: Security Impact Analysis
- Change impact assessment
- Security test requirements
- Approval based on impact
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import (
    SecurityImpactAnalysis,
    ImpactLevel,
    ApprovalStatus,
)
from models.configuration import ConfigurationChangeRequest


class SecurityImpactAnalysisService:
    """
    Service for security impact analysis (CM-4).
    """
    
    @staticmethod
    def create_impact_analysis(
        db: Session,
        org_id: int,
        change_request_id: str,
        impact_level: ImpactLevel,
        impact_description: str,
        affected_components: Optional[List[str]] = None,
        security_risks: Optional[List[Dict]] = None,
        mitigation_measures: Optional[List[Dict]] = None,
        security_test_required: bool = False,
        security_test_requirements: Optional[List[Dict]] = None,
        created_by_user_id: Optional[int] = None,
    ) -> SecurityImpactAnalysis:
        """
        Create a security impact analysis for a change request.
        
        Args:
            db: Database session
            org_id: Organization ID
            change_request_id: Change request ID
            impact_level: Impact level
            impact_description: Description of impact
            affected_components: List of affected components
            security_risks: Identified security risks
            mitigation_measures: Mitigation measures
            security_test_required: Whether security testing is required
            security_test_requirements: Required security tests
            created_by_user_id: User creating the analysis
            
        Returns:
            Created SecurityImpactAnalysis
        """
        # Verify change request exists
        change_request = db.query(ConfigurationChangeRequest).filter(
            ConfigurationChangeRequest.id == change_request_id,
            ConfigurationChangeRequest.org_id == org_id,
        ).first()
        
        if not change_request:
            raise ValueError(f"Change request {change_request_id} not found")
        
        analysis = SecurityImpactAnalysis(
            org_id=org_id,
            change_request_id=change_request_id,
            impact_level=impact_level.value,
            impact_description=impact_description,
            affected_components=affected_components,
            security_risks=security_risks,
            mitigation_measures=mitigation_measures,
            security_test_required=security_test_required,
            security_test_requirements=security_test_requirements,
            approval_status=ApprovalStatus.PENDING.value,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        logger.info(
            f"Security impact analysis created: {change_request_id} "
            f"(impact_level={impact_level.value})"
        )
        
        return analysis
    
    @staticmethod
    def approve_impact_analysis(
        db: Session,
        analysis_id: str,
        org_id: int,
        approved_by_user_id: int,
        approval_notes: Optional[str] = None,
    ) -> SecurityImpactAnalysis:
        """Approve a security impact analysis"""
        analysis = db.query(SecurityImpactAnalysis).filter(
            SecurityImpactAnalysis.id == analysis_id,
            SecurityImpactAnalysis.org_id == org_id,
        ).first()
        
        if not analysis:
            raise ValueError(f"Impact analysis {analysis_id} not found")
        
        analysis.approval_status = ApprovalStatus.APPROVED.value
        analysis.approved_by_user_id = approved_by_user_id
        analysis.approved_at = datetime.now(timezone.utc)
        analysis.approval_notes = approval_notes
        
        db.commit()
        db.refresh(analysis)
        
        logger.info(f"Security impact analysis approved: {analysis_id}")
        
        return analysis
    
    @staticmethod
    def reject_impact_analysis(
        db: Session,
        analysis_id: str,
        org_id: int,
        rejected_by_user_id: int,
        rejection_reason: str,
    ) -> SecurityImpactAnalysis:
        """Reject a security impact analysis"""
        analysis = db.query(SecurityImpactAnalysis).filter(
            SecurityImpactAnalysis.id == analysis_id,
            SecurityImpactAnalysis.org_id == org_id,
        ).first()
        
        if not analysis:
            raise ValueError(f"Impact analysis {analysis_id} not found")
        
        analysis.approval_status = ApprovalStatus.REJECTED.value
        analysis.approval_notes = rejection_reason
        
        db.commit()
        db.refresh(analysis)
        
        logger.warning(f"Security impact analysis rejected: {analysis_id} (reason: {rejection_reason})")
        
        return analysis
    
    @staticmethod
    def record_test_results(
        db: Session,
        analysis_id: str,
        org_id: int,
        test_results: List[Dict],
    ) -> SecurityImpactAnalysis:
        """Record security test results"""
        analysis = db.query(SecurityImpactAnalysis).filter(
            SecurityImpactAnalysis.id == analysis_id,
            SecurityImpactAnalysis.org_id == org_id,
        ).first()
        
        if not analysis:
            raise ValueError(f"Impact analysis {analysis_id} not found")
        
        analysis.security_test_results = test_results
        
        db.commit()
        db.refresh(analysis)
        
        return analysis
    
    @staticmethod
    def get_analysis_for_change_request(
        db: Session,
        change_request_id: str,
        org_id: int,
    ) -> Optional[SecurityImpactAnalysis]:
        """Get impact analysis for a change request"""
        return db.query(SecurityImpactAnalysis).filter(
            SecurityImpactAnalysis.change_request_id == change_request_id,
            SecurityImpactAnalysis.org_id == org_id,
        ).first()
