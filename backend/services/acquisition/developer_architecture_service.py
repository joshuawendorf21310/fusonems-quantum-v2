"""
SA-17: Developer Security Architecture Service

FedRAMP SA-17 compliance service for:
- Architecture review
- Security design patterns
- Threat modeling
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    DeveloperArchitecture,
    SecurityDesignPattern,
    ArchitectureReviewStatus,
)


class DeveloperArchitectureService:
    """Service for SA-17: Developer Security Architecture"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_architecture(
        self,
        architecture_name: str,
        system_name: str,
        system_id: Optional[str] = None,
        architecture_description: Optional[str] = None,
        architecture_document: Optional[str] = None,
        security_patterns_used: Optional[List[SecurityDesignPattern]] = None,
        pattern_implementation: Optional[Dict[str, Any]] = None,
        threat_model: Optional[str] = None,
        threats_identified: Optional[List[Dict[str, Any]]] = None,
        mitigations: Optional[List[Dict[str, Any]]] = None,
        security_controls: Optional[List[str]] = None,
        control_implementation: Optional[Dict[str, Any]] = None,
        reviewed_by: Optional[str] = None,
        review_team: Optional[List[str]] = None,
    ) -> DeveloperArchitecture:
        """Create a developer architecture"""
        patterns_list = [p.value for p in security_patterns_used] if security_patterns_used else []
        
        architecture = DeveloperArchitecture(
            architecture_name=architecture_name,
            system_name=system_name,
            system_id=system_id,
            architecture_description=architecture_description,
            architecture_document=architecture_document,
            security_patterns_used=patterns_list,
            pattern_implementation=pattern_implementation,
            threat_model=threat_model,
            threats_identified=threats_identified,
            mitigations=mitigations,
            security_controls=security_controls,
            control_implementation=control_implementation,
            reviewed_by=reviewed_by,
            review_team=review_team,
            status=ArchitectureReviewStatus.PENDING.value,
        )
        self.db.add(architecture)
        self.db.commit()
        self.db.refresh(architecture)
        return architecture
    
    def add_findings(
        self,
        architecture_id: int,
        findings: List[Dict[str, Any]],
    ) -> DeveloperArchitecture:
        """Add findings to architecture review"""
        architecture = self.db.query(DeveloperArchitecture).filter(
            DeveloperArchitecture.id == architecture_id
        ).first()
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")
        
        existing_findings = architecture.findings or []
        existing_findings.extend(findings)
        architecture.findings = existing_findings
        
        # Update counts
        architecture.critical_findings = sum(1 for f in existing_findings if f.get("severity") == "critical")
        architecture.high_findings = sum(1 for f in existing_findings if f.get("severity") == "high")
        architecture.medium_findings = sum(1 for f in existing_findings if f.get("severity") == "medium")
        architecture.low_findings = sum(1 for f in existing_findings if f.get("severity") == "low")
        
        self.db.commit()
        self.db.refresh(architecture)
        return architecture
    
    def add_recommendations(
        self,
        architecture_id: int,
        recommendations: List[str],
    ) -> DeveloperArchitecture:
        """Add recommendations to architecture review"""
        architecture = self.db.query(DeveloperArchitecture).filter(
            DeveloperArchitecture.id == architecture_id
        ).first()
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")
        
        existing_recommendations = architecture.recommendations or []
        existing_recommendations.extend(recommendations)
        architecture.recommendations = existing_recommendations
        
        self.db.commit()
        self.db.refresh(architecture)
        return architecture
    
    def approve_architecture(
        self,
        architecture_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None,
    ) -> DeveloperArchitecture:
        """Approve an architecture"""
        architecture = self.db.query(DeveloperArchitecture).filter(
            DeveloperArchitecture.id == architecture_id
        ).first()
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")
        
        architecture.approved = True
        architecture.approved_by = approved_by
        architecture.approval_date = datetime.utcnow()
        architecture.approval_notes = approval_notes
        architecture.status = ArchitectureReviewStatus.APPROVED.value
        
        self.db.commit()
        self.db.refresh(architecture)
        return architecture
    
    def reject_architecture(
        self,
        architecture_id: int,
        notes: Optional[str] = None,
    ) -> DeveloperArchitecture:
        """Reject an architecture"""
        architecture = self.db.query(DeveloperArchitecture).filter(
            DeveloperArchitecture.id == architecture_id
        ).first()
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")
        
        architecture.status = ArchitectureReviewStatus.REJECTED.value
        if notes:
            architecture.notes = (architecture.notes or "") + f"\nRejection: {notes}"
        
        self.db.commit()
        self.db.refresh(architecture)
        return architecture
    
    def list_architectures(
        self,
        system_name: Optional[str] = None,
        status: Optional[ArchitectureReviewStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DeveloperArchitecture], int]:
        """List developer architectures"""
        query = self.db.query(DeveloperArchitecture)
        
        if system_name:
            query = query.filter(DeveloperArchitecture.system_name == system_name)
        
        if status:
            query = query.filter(DeveloperArchitecture.status == status.value)
        
        total = query.count()
        architectures = query.order_by(desc(DeveloperArchitecture.review_date)).offset(offset).limit(limit).all()
        
        return architectures, total
    
    def get_architecture_summary(self, architecture_id: int) -> Dict[str, Any]:
        """Get comprehensive architecture summary"""
        architecture = self.db.query(DeveloperArchitecture).filter(
            DeveloperArchitecture.id == architecture_id
        ).first()
        if not architecture:
            raise ValueError(f"Architecture {architecture_id} not found")
        
        return {
            "architecture": architecture,
            "patterns_summary": self._summarize_patterns(architecture),
            "threats_summary": self._summarize_threats(architecture),
            "findings_summary": self._summarize_findings(architecture),
        }
    
    def _summarize_patterns(self, architecture: DeveloperArchitecture) -> Dict[str, Any]:
        """Summarize security patterns"""
        patterns = architecture.security_patterns_used or []
        return {
            "total_patterns": len(patterns),
            "patterns": patterns,
        }
    
    def _summarize_threats(self, architecture: DeveloperArchitecture) -> Dict[str, Any]:
        """Summarize threats"""
        threats = architecture.threats_identified or []
        mitigations = architecture.mitigations or []
        return {
            "total_threats": len(threats),
            "total_mitigations": len(mitigations),
            "unmitigated_threats": len(threats) - len(mitigations),
        }
    
    def _summarize_findings(self, architecture: DeveloperArchitecture) -> Dict[str, Any]:
        """Summarize findings"""
        return {
            "total": len(architecture.findings or []),
            "critical": architecture.critical_findings,
            "high": architecture.high_findings,
            "medium": architecture.medium_findings,
            "low": architecture.low_findings,
        }
