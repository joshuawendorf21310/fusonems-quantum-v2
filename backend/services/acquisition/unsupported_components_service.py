"""
SA-22: Unsupported System Components Service

FedRAMP SA-22 compliance service for:
- EOL component tracking
- Replacement planning
- Risk assessment
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    UnsupportedComponent,
    ComponentStatus,
    ReplacementStatus,
)


class UnsupportedComponentsService:
    """Service for SA-22: Unsupported System Components"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_component(
        self,
        component_name: str,
        component_type: str,
        system_name: str,
        component_version: Optional[str] = None,
        component_vendor: Optional[str] = None,
        system_id: Optional[str] = None,
        eol_date: Optional[datetime] = None,
        eos_date: Optional[datetime] = None,
        eol_announced_date: Optional[datetime] = None,
    ) -> UnsupportedComponent:
        """Create an unsupported component record"""
        # Determine initial status based on dates
        status = ComponentStatus.SUPPORTED.value
        if eol_date and eol_date <= datetime.utcnow():
            status = ComponentStatus.END_OF_LIFE.value
        elif eos_date and eos_date <= datetime.utcnow():
            status = ComponentStatus.END_OF_SUPPORT.value
        
        component = UnsupportedComponent(
            component_name=component_name,
            component_type=component_type,
            component_version=component_version,
            component_vendor=component_vendor,
            system_name=system_name,
            system_id=system_id,
            eol_date=eol_date,
            eos_date=eos_date,
            eol_announced_date=eol_announced_date,
            status=status,
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def update_risk_assessment(
        self,
        component_id: int,
        risk_level: str,
        risk_assessment_notes: Optional[str] = None,
        known_vulnerabilities: Optional[int] = None,
        unpatched_vulnerabilities: Optional[int] = None,
        vulnerability_details: Optional[List[Dict[str, Any]]] = None,
    ) -> UnsupportedComponent:
        """Update risk assessment for component"""
        component = self.db.query(UnsupportedComponent).filter(
            UnsupportedComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.risk_level = risk_level
        component.risk_assessment_date = datetime.utcnow()
        component.risk_assessment_notes = risk_assessment_notes
        
        if known_vulnerabilities is not None:
            component.known_vulnerabilities = known_vulnerabilities
        
        if unpatched_vulnerabilities is not None:
            component.unpatched_vulnerabilities = unpatched_vulnerabilities
        
        if vulnerability_details:
            component.vulnerability_details = vulnerability_details
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def create_replacement_plan(
        self,
        component_id: int,
        replacement_component: str,
        replacement_plan: str,
        replacement_target_date: Optional[datetime] = None,
    ) -> UnsupportedComponent:
        """Create a replacement plan"""
        component = self.db.query(UnsupportedComponent).filter(
            UnsupportedComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.replacement_required = True
        component.replacement_status = ReplacementStatus.PLANNED.value
        component.replacement_component = replacement_component
        component.replacement_plan = replacement_plan
        component.replacement_target_date = replacement_target_date
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def update_replacement_status(
        self,
        component_id: int,
        replacement_status: ReplacementStatus,
        replacement_completed_date: Optional[datetime] = None,
    ) -> UnsupportedComponent:
        """Update replacement status"""
        component = self.db.query(UnsupportedComponent).filter(
            UnsupportedComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.replacement_status = replacement_status.value
        
        if replacement_status == ReplacementStatus.COMPLETED:
            component.replacement_completed_date = replacement_completed_date or datetime.utcnow()
            component.status = ComponentStatus.REPLACED.value
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def add_mitigation(
        self,
        component_id: int,
        mitigation_measures: str,
        mitigation_effectiveness: str,
    ) -> UnsupportedComponent:
        """Add mitigation measures"""
        component = self.db.query(UnsupportedComponent).filter(
            UnsupportedComponent.id == component_id
        ).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.mitigation_measures = mitigation_measures
        component.mitigation_effectiveness = mitigation_effectiveness
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def check_eol_components(self) -> List[UnsupportedComponent]:
        """Check for components that have reached EOL"""
        now = datetime.utcnow()
        eol_components = self.db.query(UnsupportedComponent).filter(
            and_(
                UnsupportedComponent.eol_date.isnot(None),
                UnsupportedComponent.eol_date <= now,
                UnsupportedComponent.status != ComponentStatus.REPLACED.value,
            )
        ).all()
        
        # Update status
        for component in eol_components:
            if component.status == ComponentStatus.SUPPORTED.value:
                component.status = ComponentStatus.END_OF_LIFE.value
        
        self.db.commit()
        return eol_components
    
    def list_components(
        self,
        system_name: Optional[str] = None,
        component_type: Optional[str] = None,
        status: Optional[ComponentStatus] = None,
        risk_level: Optional[str] = None,
        replacement_status: Optional[ReplacementStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[UnsupportedComponent], int]:
        """List unsupported components"""
        query = self.db.query(UnsupportedComponent)
        
        if system_name:
            query = query.filter(UnsupportedComponent.system_name == system_name)
        
        if component_type:
            query = query.filter(UnsupportedComponent.component_type == component_type)
        
        if status:
            query = query.filter(UnsupportedComponent.status == status.value)
        
        if risk_level:
            query = query.filter(UnsupportedComponent.risk_level == risk_level)
        
        if replacement_status:
            query = query.filter(UnsupportedComponent.replacement_status == replacement_status.value)
        
        total = query.count()
        components = query.order_by(desc(UnsupportedComponent.created_at)).offset(offset).limit(limit).all()
        
        return components, total
    
    def get_component_summary(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """Get component summary"""
        query = self.db.query(UnsupportedComponent)
        
        if system_name:
            query = query.filter(UnsupportedComponent.system_name == system_name)
        
        components = query.all()
        
        return {
            "total_components": len(components),
            "by_status": self._summarize_by_status(components),
            "by_risk": self._summarize_by_risk(components),
            "replacement_summary": self._summarize_replacements(components),
            "eol_soon": self._get_eol_soon(components),
        }
    
    def _summarize_by_status(self, components: List[UnsupportedComponent]) -> Dict[str, int]:
        """Summarize by status"""
        summary = {}
        for component in components:
            status = component.status
            summary[status] = summary.get(status, 0) + 1
        return summary
    
    def _summarize_by_risk(self, components: List[UnsupportedComponent]) -> Dict[str, int]:
        """Summarize by risk level"""
        summary = {}
        for component in components:
            risk = component.risk_level or "unknown"
            summary[risk] = summary.get(risk, 0) + 1
        return summary
    
    def _summarize_replacements(self, components: List[UnsupportedComponent]) -> Dict[str, Any]:
        """Summarize replacement status"""
        return {
            "replacement_required": sum(1 for c in components if c.replacement_required),
            "planned": sum(1 for c in components if c.replacement_status == ReplacementStatus.PLANNED.value),
            "in_progress": sum(1 for c in components if c.replacement_status == ReplacementStatus.IN_PROGRESS.value),
            "completed": sum(1 for c in components if c.replacement_status == ReplacementStatus.COMPLETED.value),
        }
    
    def _get_eol_soon(self, components: List[UnsupportedComponent], days: int = 90) -> int:
        """Get count of components reaching EOL soon"""
        cutoff = datetime.utcnow() + timedelta(days=days)
        return sum(
            1 for c in components
            if c.eol_date and c.eol_date <= cutoff and c.status != ComponentStatus.REPLACED.value
        )
