"""
SA-8: Security Engineering Principles Service

FedRAMP SA-8 compliance service for:
- Design principle enforcement
- Security review checkpoints
- Architecture validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SecurityDesignReview,
    SecurityCheckpoint,
    DesignPrinciple,
    ReviewStatus,
)


class SecurityEngineeringService:
    """Service for SA-8: Security Engineering Principles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_design_review(
        self,
        review_name: str,
        system_name: str,
        principles_applied: Optional[List[DesignPrinciple]] = None,
        system_id: Optional[str] = None,
        architecture_document: Optional[str] = None,
        threat_model: Optional[str] = None,
        security_controls: Optional[List[str]] = None,
        reviewed_by: Optional[str] = None,
        review_team: Optional[List[str]] = None,
    ) -> SecurityDesignReview:
        """Create a security design review"""
        principles_list = [p.value for p in principles_applied] if principles_applied else []
        principles_compliance = {p.value: "pending" for p in principles_applied} if principles_applied else {}
        
        review = SecurityDesignReview(
            review_name=review_name,
            system_name=system_name,
            system_id=system_id,
            principles_applied=principles_list,
            principles_compliance=principles_compliance,
            architecture_document=architecture_document,
            threat_model=threat_model,
            security_controls=security_controls,
            reviewed_by=reviewed_by,
            review_team=review_team,
            status=ReviewStatus.PENDING.value,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def update_principles_compliance(
        self,
        review_id: int,
        principle: DesignPrinciple,
        compliant: bool,
        notes: Optional[str] = None,
    ) -> SecurityDesignReview:
        """Update principle compliance status"""
        review = self.db.query(SecurityDesignReview).filter(
            SecurityDesignReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        compliance = review.principles_compliance or {}
        compliance[principle.value] = "compliant" if compliant else "non_compliant"
        review.principles_compliance = compliance
        
        if notes:
            review.notes = (review.notes or "") + f"\n{principle.value}: {notes}"
        
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def add_findings(
        self,
        review_id: int,
        findings: List[Dict[str, Any]],
    ) -> SecurityDesignReview:
        """Add findings to design review"""
        review = self.db.query(SecurityDesignReview).filter(
            SecurityDesignReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        existing_findings = review.findings or []
        existing_findings.extend(findings)
        review.findings = existing_findings
        
        # Update counts
        review.critical_findings = sum(1 for f in existing_findings if f.get("severity") == "critical")
        review.high_findings = sum(1 for f in existing_findings if f.get("severity") == "high")
        review.medium_findings = sum(1 for f in existing_findings if f.get("severity") == "medium")
        review.low_findings = sum(1 for f in existing_findings if f.get("severity") == "low")
        
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def approve_design_review(
        self,
        review_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None,
    ) -> SecurityDesignReview:
        """Approve a design review"""
        review = self.db.query(SecurityDesignReview).filter(
            SecurityDesignReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        review.approved = True
        review.approved_by = approved_by
        review.approval_date = datetime.utcnow()
        review.approval_notes = approval_notes
        review.status = ReviewStatus.APPROVED.value
        
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def create_checkpoint(
        self,
        security_design_review_id: int,
        checkpoint_name: str,
        checkpoint_type: str,
        requirements: Optional[List[str]] = None,
        checkpoint_description: Optional[str] = None,
    ) -> SecurityCheckpoint:
        """Create a security checkpoint"""
        checkpoint = SecurityCheckpoint(
            security_design_review_id=security_design_review_id,
            checkpoint_name=checkpoint_name,
            checkpoint_description=checkpoint_description,
            checkpoint_type=checkpoint_type,
            requirements=requirements,
            status=ReviewStatus.PENDING.value,
        )
        self.db.add(checkpoint)
        self.db.commit()
        self.db.refresh(checkpoint)
        return checkpoint
    
    def evaluate_checkpoint(
        self,
        checkpoint_id: int,
        requirements_met: List[str],
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> SecurityCheckpoint:
        """Evaluate a security checkpoint"""
        checkpoint = self.db.query(SecurityCheckpoint).filter(
            SecurityCheckpoint.id == checkpoint_id
        ).first()
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        checkpoint.requirements_met = requirements_met
        checkpoint.reviewed_by = reviewed_by
        checkpoint.review_date = datetime.utcnow()
        checkpoint.review_notes = review_notes
        
        # Check if all requirements are met
        all_requirements = checkpoint.requirements or []
        if set(requirements_met) >= set(all_requirements):
            checkpoint.status = ReviewStatus.APPROVED.value
        else:
            checkpoint.status = ReviewStatus.REQUIRES_REVISION.value
        
        self.db.commit()
        self.db.refresh(checkpoint)
        return checkpoint
    
    def list_reviews(
        self,
        system_name: Optional[str] = None,
        status: Optional[ReviewStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SecurityDesignReview], int]:
        """List security design reviews"""
        query = self.db.query(SecurityDesignReview)
        
        if system_name:
            query = query.filter(SecurityDesignReview.system_name == system_name)
        
        if status:
            query = query.filter(SecurityDesignReview.status == status.value)
        
        total = query.count()
        reviews = query.order_by(desc(SecurityDesignReview.review_date)).offset(offset).limit(limit).all()
        
        return reviews, total
    
    def get_review_summary(self, review_id: int) -> Dict[str, Any]:
        """Get comprehensive review summary"""
        review = self.db.query(SecurityDesignReview).filter(
            SecurityDesignReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        
        checkpoints = self.db.query(SecurityCheckpoint).filter(
            SecurityCheckpoint.security_design_review_id == review_id
        ).all()
        
        return {
            "review": review,
            "checkpoints": checkpoints,
            "checkpoint_summary": self._summarize_checkpoints(checkpoints),
            "principles_summary": self._summarize_principles(review),
        }
    
    def _summarize_checkpoints(self, checkpoints: List[SecurityCheckpoint]) -> Dict[str, Any]:
        """Summarize checkpoints"""
        return {
            "total": len(checkpoints),
            "approved": sum(1 for c in checkpoints if c.status == ReviewStatus.APPROVED.value),
            "pending": sum(1 for c in checkpoints if c.status == ReviewStatus.PENDING.value),
            "requires_revision": sum(1 for c in checkpoints if c.status == ReviewStatus.REQUIRES_REVISION.value),
        }
    
    def _summarize_principles(self, review: SecurityDesignReview) -> Dict[str, Any]:
        """Summarize principles compliance"""
        compliance = review.principles_compliance or {}
        return {
            "total": len(review.principles_applied or []),
            "compliant": sum(1 for v in compliance.values() if v == "compliant"),
            "non_compliant": sum(1 for v in compliance.values() if v == "non_compliant"),
            "pending": sum(1 for v in compliance.values() if v == "pending"),
        }
