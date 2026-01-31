"""
SA-4: Acquisition Process Service

FedRAMP SA-4 compliance service for:
- Security requirements in contracts
- Vendor security assessment
- Contract compliance
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    AcquisitionContract,
    VendorSecurityAssessment,
    ContractComplianceReview,
    ContractStatus,
    VendorAssessmentStatus,
)


class AcquisitionProcessService:
    """Service for SA-4: Acquisition Process"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_contract(
        self,
        contract_number: str,
        contract_name: str,
        vendor_name: str,
        security_requirements: Optional[List[str]] = None,
        contract_description: Optional[str] = None,
        vendor_contact: Optional[str] = None,
        vendor_email: Optional[str] = None,
        contract_value: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AcquisitionContract:
        """Create a new acquisition contract"""
        contract = AcquisitionContract(
            contract_number=contract_number,
            contract_name=contract_name,
            contract_description=contract_description,
            vendor_name=vendor_name,
            vendor_contact=vendor_contact,
            vendor_email=vendor_email,
            contract_value=contract_value,
            start_date=start_date,
            end_date=end_date,
            security_requirements=security_requirements,
            security_requirements_met=False,
            status=ContractStatus.DRAFT.value,
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract
    
    def create_vendor_assessment(
        self,
        acquisition_contract_id: int,
        assessment_name: str,
        assessed_by: Optional[str] = None,
        security_controls_assessed: Optional[List[str]] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> VendorSecurityAssessment:
        """Create a vendor security assessment"""
        # Calculate findings counts
        critical = sum(1 for f in (findings or []) if f.get("severity") == "critical")
        high = sum(1 for f in (findings or []) if f.get("severity") == "high")
        medium = sum(1 for f in (findings or []) if f.get("severity") == "medium")
        low = sum(1 for f in (findings or []) if f.get("severity") == "low")
        
        # Calculate risk level
        risk_level = "low"
        if critical > 0 or high > 2:
            risk_level = "critical"
        elif high > 0:
            risk_level = "high"
        elif medium > 2:
            risk_level = "medium"
        
        assessment = VendorSecurityAssessment(
            acquisition_contract_id=acquisition_contract_id,
            assessment_name=assessment_name,
            assessed_by=assessed_by,
            security_controls_assessed=security_controls_assessed,
            findings=findings,
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            recommendations=recommendations,
            risk_level=risk_level,
            status=VendorAssessmentStatus.PENDING.value,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def approve_vendor_assessment(
        self,
        assessment_id: int,
        approved_by: str,
    ) -> VendorSecurityAssessment:
        """Approve a vendor security assessment"""
        assessment = self.db.query(VendorSecurityAssessment).filter(
            VendorSecurityAssessment.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        assessment.approved = True
        assessment.approved_by = approved_by
        assessment.approval_date = datetime.utcnow()
        assessment.status = VendorAssessmentStatus.COMPLETED.value
        
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def create_compliance_review(
        self,
        acquisition_contract_id: int,
        review_name: str,
        requirements_checked: Optional[List[str]] = None,
        reviewed_by: Optional[str] = None,
        non_compliance_findings: Optional[List[Dict[str, Any]]] = None,
    ) -> ContractComplianceReview:
        """Create a contract compliance review"""
        requirements_checked = requirements_checked or []
        compliant_count = len(requirements_checked) - len(non_compliance_findings or [])
        non_compliant_count = len(non_compliance_findings or [])
        compliance_percentage = (compliant_count / len(requirements_checked) * 100) if requirements_checked else 0
        
        review = ContractComplianceReview(
            acquisition_contract_id=acquisition_contract_id,
            review_name=review_name,
            reviewed_by=reviewed_by,
            requirements_checked=requirements_checked,
            requirements_compliant=compliant_count,
            requirements_non_compliant=non_compliant_count,
            compliance_percentage=compliance_percentage,
            non_compliance_findings=non_compliance_findings,
            remediation_required=non_compliant_count > 0,
            status="compliant" if non_compliant_count == 0 else "non_compliant",
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def update_contract_security_requirements(
        self,
        contract_id: int,
        security_requirements: List[str],
        security_requirements_met: bool = False,
        security_requirements_notes: Optional[str] = None,
    ) -> AcquisitionContract:
        """Update contract security requirements"""
        contract = self.db.query(AcquisitionContract).filter(
            AcquisitionContract.id == contract_id
        ).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract.security_requirements = security_requirements
        contract.security_requirements_met = security_requirements_met
        contract.security_requirements_notes = security_requirements_notes
        
        self.db.commit()
        self.db.refresh(contract)
        return contract
    
    def list_contracts(
        self,
        status: Optional[ContractStatus] = None,
        vendor_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AcquisitionContract], int]:
        """List acquisition contracts"""
        query = self.db.query(AcquisitionContract)
        
        if status:
            query = query.filter(AcquisitionContract.status == status.value)
        
        if vendor_name:
            query = query.filter(AcquisitionContract.vendor_name.ilike(f"%{vendor_name}%"))
        
        total = query.count()
        contracts = query.order_by(desc(AcquisitionContract.created_at)).offset(offset).limit(limit).all()
        
        return contracts, total
    
    def get_contract_summary(self, contract_id: int) -> Dict[str, Any]:
        """Get comprehensive contract summary"""
        contract = self.db.query(AcquisitionContract).filter(
            AcquisitionContract.id == contract_id
        ).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        assessments = self.db.query(VendorSecurityAssessment).filter(
            VendorSecurityAssessment.acquisition_contract_id == contract_id
        ).all()
        
        reviews = self.db.query(ContractComplianceReview).filter(
            ContractComplianceReview.acquisition_contract_id == contract_id
        ).order_by(desc(ContractComplianceReview.review_date)).all()
        
        return {
            "contract": contract,
            "assessments": assessments,
            "compliance_reviews": reviews,
            "latest_assessment": assessments[-1] if assessments else None,
            "latest_review": reviews[0] if reviews else None,
            "compliance_status": self._calculate_compliance_status(reviews),
        }
    
    def _calculate_compliance_status(self, reviews: List[ContractComplianceReview]) -> Dict[str, Any]:
        """Calculate compliance status from reviews"""
        if not reviews:
            return {"status": "unknown", "compliance_percentage": 0.0}
        
        latest_review = reviews[0]
        return {
            "status": latest_review.status,
            "compliance_percentage": latest_review.compliance_percentage,
            "last_review_date": latest_review.review_date.isoformat() if latest_review.review_date else None,
        }
