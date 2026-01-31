"""
SA-12: Supply Chain Risk Management Service

FedRAMP SA-12 compliance service for:
- Supplier security assessment
- Component provenance
- Third-party risk
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SupplyChainComponent,
    SupplierSecurityAssessment,
    ComponentType,
    SupplierRiskLevel,
    VendorAssessmentStatus,
)


class SupplyChainService:
    """Service for SA-12: Supply Chain Risk Management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_component(
        self,
        component_name: str,
        component_type: ComponentType,
        supplier_name: str,
        system_name: str,
        component_version: Optional[str] = None,
        component_description: Optional[str] = None,
        supplier_contact: Optional[str] = None,
        supplier_country: Optional[str] = None,
        system_id: Optional[str] = None,
        origin_country: Optional[str] = None,
        manufacturing_location: Optional[str] = None,
        supply_chain_path: Optional[List[Dict[str, Any]]] = None,
    ) -> SupplyChainComponent:
        """Create a supply chain component"""
        component = SupplyChainComponent(
            component_name=component_name,
            component_type=component_type.value,
            component_version=component_version,
            component_description=component_description,
            supplier_name=supplier_name,
            supplier_contact=supplier_contact,
            supplier_country=supplier_country,
            system_name=system_name,
            system_id=system_id,
            origin_country=origin_country,
            manufacturing_location=manufacturing_location,
            supply_chain_path=supply_chain_path,
            is_active=True,
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def create_supplier_assessment(
        self,
        supply_chain_component_id: int,
        assessment_name: str,
        assessed_by: Optional[str] = None,
        security_controls_assessed: Optional[List[str]] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
        third_party_risks: Optional[List[Dict[str, Any]]] = None,
    ) -> SupplierSecurityAssessment:
        """Create a supplier security assessment"""
        # Calculate findings counts
        critical = sum(1 for f in (findings or []) if f.get("severity") == "critical")
        high = sum(1 for f in (findings or []) if f.get("severity") == "high")
        medium = sum(1 for f in (findings or []) if f.get("severity") == "medium")
        low = sum(1 for f in (findings or []) if f.get("severity") == "low")
        
        # Calculate risk level
        risk_level = SupplierRiskLevel.LOW.value
        if critical > 0 or high > 2:
            risk_level = SupplierRiskLevel.CRITICAL.value
        elif high > 0:
            risk_level = SupplierRiskLevel.HIGH.value
        elif medium > 2:
            risk_level = SupplierRiskLevel.MEDIUM.value
        
        assessment = SupplierSecurityAssessment(
            supply_chain_component_id=supply_chain_component_id,
            assessment_name=assessment_name,
            assessed_by=assessed_by,
            security_controls_assessed=security_controls_assessed,
            findings=findings,
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            recommendations=recommendations,
            third_party_risks=third_party_risks,
            risk_level=risk_level,
            status=VendorAssessmentStatus.PENDING.value,
        )
        self.db.add(assessment)
        
        # Update component assessment status
        component = self.db.query(SupplyChainComponent).filter(
            SupplyChainComponent.id == supply_chain_component_id
        ).first()
        if component:
            component.security_assessment_completed = True
            component.security_assessment_date = datetime.utcnow()
            component.security_assessment_score = self._calculate_score(findings)
            component.risk_level = risk_level
        
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def update_component_risk(
        self,
        component_id: int,
        risk_level: SupplierRiskLevel,
        risk_assessment_notes: Optional[str] = None,
    ) -> SupplyChainComponent:
        """Update component risk assessment"""
        component = self.db.query(SupplyChainComponent).filter(
            SupplyChainComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.risk_level = risk_level.value
        component.risk_assessment_date = datetime.utcnow()
        component.risk_assessment_notes = risk_assessment_notes
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def approve_assessment(
        self,
        assessment_id: int,
        approved_by: str,
    ) -> SupplierSecurityAssessment:
        """Approve a supplier assessment"""
        assessment = self.db.query(SupplierSecurityAssessment).filter(
            SupplierSecurityAssessment.id == assessment_id
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
    
    def list_components(
        self,
        system_name: Optional[str] = None,
        component_type: Optional[ComponentType] = None,
        supplier_name: Optional[str] = None,
        risk_level: Optional[SupplierRiskLevel] = None,
        is_active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SupplyChainComponent], int]:
        """List supply chain components"""
        query = self.db.query(SupplyChainComponent)
        
        if system_name:
            query = query.filter(SupplyChainComponent.system_name == system_name)
        
        if component_type:
            query = query.filter(SupplyChainComponent.component_type == component_type.value)
        
        if supplier_name:
            query = query.filter(SupplyChainComponent.supplier_name.ilike(f"%{supplier_name}%"))
        
        if risk_level:
            query = query.filter(SupplyChainComponent.risk_level == risk_level.value)
        
        if is_active is not None:
            query = query.filter(SupplyChainComponent.is_active == is_active)
        
        total = query.count()
        components = query.order_by(desc(SupplyChainComponent.created_at)).offset(offset).limit(limit).all()
        
        return components, total
    
    def get_component_summary(self, component_id: int) -> Dict[str, Any]:
        """Get comprehensive component summary"""
        component = self.db.query(SupplyChainComponent).filter(
            SupplyChainComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        assessments = self.db.query(SupplierSecurityAssessment).filter(
            SupplierSecurityAssessment.supply_chain_component_id == component_id
        ).all()
        
        return {
            "component": component,
            "assessments": assessments,
            "latest_assessment": assessments[-1] if assessments else None,
            "risk_summary": self._calculate_risk_summary(component, assessments),
        }
    
    def get_supply_chain_summary(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """Get supply chain summary"""
        query = self.db.query(SupplyChainComponent)
        
        if system_name:
            query = query.filter(SupplyChainComponent.system_name == system_name)
        
        components = query.all()
        
        return {
            "total_components": len(components),
            "by_type": self._summarize_by_type(components),
            "by_risk": self._summarize_by_risk(components),
            "by_supplier": self._summarize_by_supplier(components),
            "assessments_pending": sum(1 for c in components if not c.security_assessment_completed),
        }
    
    def _calculate_score(self, findings: Optional[List[Dict[str, Any]]]) -> Optional[float]:
        """Calculate security assessment score"""
        if not findings:
            return 1.0
        
        total = len(findings)
        critical = sum(1 for f in findings if f.get("severity") == "critical")
        high = sum(1 for f in findings if f.get("severity") == "high")
        
        # Score decreases with findings
        score = 1.0 - (critical * 0.3 + high * 0.2 + (total - critical - high) * 0.05)
        return max(0.0, min(1.0, score))
    
    def _calculate_risk_summary(
        self,
        component: SupplyChainComponent,
        assessments: List[SupplierSecurityAssessment]
    ) -> Dict[str, Any]:
        """Calculate risk summary"""
        return {
            "current_risk_level": component.risk_level,
            "assessment_count": len(assessments),
            "latest_assessment_date": assessments[-1].assessment_date.isoformat() if assessments else None,
        }
    
    def _summarize_by_type(self, components: List[SupplyChainComponent]) -> Dict[str, int]:
        """Summarize by component type"""
        summary = {}
        for component in components:
            comp_type = component.component_type
            summary[comp_type] = summary.get(comp_type, 0) + 1
        return summary
    
    def _summarize_by_risk(self, components: List[SupplyChainComponent]) -> Dict[str, int]:
        """Summarize by risk level"""
        summary = {}
        for component in components:
            risk = component.risk_level or "unknown"
            summary[risk] = summary.get(risk, 0) + 1
        return summary
    
    def _summarize_by_supplier(self, components: List[SupplyChainComponent]) -> Dict[str, int]:
        """Summarize by supplier"""
        summary = {}
        for component in components:
            supplier = component.supplier_name
            summary[supplier] = summary.get(supplier, 0) + 1
        return summary
