"""
SA-9: External Information System Services Service

FedRAMP SA-9 compliance service for:
- Third-party service tracking
- SLA management
- Security assessment
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    ExternalService,
    SLAMetric,
    ExternalServiceSecurityAssessment,
    ServiceType,
    ServiceStatus,
    SLAMetric as SLAMetricEnum,
    VendorAssessmentStatus,
)


class ExternalServicesService:
    """Service for SA-9: External Information System Services"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_external_service(
        self,
        service_name: str,
        service_type: ServiceType,
        provider_name: str,
        data_types_processed: Optional[List[str]] = None,
        service_description: Optional[str] = None,
        provider_contact: Optional[str] = None,
        provider_email: Optional[str] = None,
        service_url: Optional[str] = None,
        data_classification: Optional[str] = None,
        data_location: Optional[str] = None,
    ) -> ExternalService:
        """Create a new external service"""
        service = ExternalService(
            service_name=service_name,
            service_description=service_description,
            service_type=service_type.value,
            provider_name=provider_name,
            provider_contact=provider_contact,
            provider_email=provider_email,
            service_url=service_url,
            data_types_processed=data_types_processed,
            data_classification=data_classification,
            data_location=data_location,
            status=ServiceStatus.EVALUATION.value,
        )
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service
    
    def create_sla_metric(
        self,
        external_service_id: int,
        metric_name: str,
        metric_type: SLAMetricEnum,
        target_value: float,
        target_unit: Optional[str] = None,
        measurement_period: Optional[str] = None,
    ) -> SLAMetric:
        """Create an SLA metric"""
        metric = SLAMetric(
            external_service_id=external_service_id,
            metric_name=metric_name,
            metric_type=metric_type.value,
            target_value=target_value,
            target_unit=target_unit,
            measurement_period=measurement_period,
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    def update_sla_metric(
        self,
        metric_id: int,
        actual_value: float,
        last_measured_date: Optional[datetime] = None,
    ) -> SLAMetric:
        """Update SLA metric with actual performance"""
        metric = self.db.query(SLAMetric).filter(SLAMetric.id == metric_id).first()
        if not metric:
            raise ValueError(f"SLA metric {metric_id} not found")
        
        metric.actual_value = actual_value
        metric.last_measured_date = last_measured_date or datetime.utcnow()
        
        # Check if SLA is met
        metric.sla_met = actual_value >= metric.target_value
        
        if not metric.sla_met:
            metric.sla_violations = (metric.sla_violations or 0) + 1
        
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    def create_security_assessment(
        self,
        external_service_id: int,
        assessment_name: str,
        assessed_by: Optional[str] = None,
        security_controls_assessed: Optional[List[str]] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> ExternalServiceSecurityAssessment:
        """Create a security assessment for external service"""
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
        
        assessment = ExternalServiceSecurityAssessment(
            external_service_id=external_service_id,
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
        
        # Update service assessment status
        service = self.db.query(ExternalService).filter(
            ExternalService.id == external_service_id
        ).first()
        if service:
            service.security_assessment_completed = True
            service.security_assessment_date = datetime.utcnow()
            service.security_assessment_score = self._calculate_score(findings)
            service.security_risk_level = risk_level
        
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def approve_service(
        self,
        service_id: int,
        approved_by: str,
    ) -> ExternalService:
        """Approve an external service"""
        service = self.db.query(ExternalService).filter(
            ExternalService.id == service_id
        ).first()
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        if not service.security_assessment_completed:
            raise ValueError("Security assessment must be completed before approval")
        
        service.approved = True
        service.approved_by = approved_by
        service.approval_date = datetime.utcnow()
        service.status = ServiceStatus.APPROVED.value
        
        self.db.commit()
        self.db.refresh(service)
        return service
    
    def activate_service(
        self,
        service_id: int,
        service_start_date: Optional[datetime] = None,
    ) -> ExternalService:
        """Activate an external service"""
        service = self.db.query(ExternalService).filter(
            ExternalService.id == service_id
        ).first()
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        if not service.approved:
            raise ValueError("Service must be approved before activation")
        
        service.status = ServiceStatus.ACTIVE.value
        service.service_start_date = service_start_date or datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(service)
        return service
    
    def list_services(
        self,
        status: Optional[ServiceStatus] = None,
        service_type: Optional[ServiceType] = None,
        provider_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[ExternalService], int]:
        """List external services"""
        query = self.db.query(ExternalService)
        
        if status:
            query = query.filter(ExternalService.status == status.value)
        
        if service_type:
            query = query.filter(ExternalService.service_type == service_type.value)
        
        if provider_name:
            query = query.filter(ExternalService.provider_name.ilike(f"%{provider_name}%"))
        
        total = query.count()
        services = query.order_by(desc(ExternalService.created_at)).offset(offset).limit(limit).all()
        
        return services, total
    
    def get_service_summary(self, service_id: int) -> Dict[str, Any]:
        """Get comprehensive service summary"""
        service = self.db.query(ExternalService).filter(
            ExternalService.id == service_id
        ).first()
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        metrics = self.db.query(SLAMetric).filter(
            SLAMetric.external_service_id == service_id
        ).all()
        
        assessments = self.db.query(ExternalServiceSecurityAssessment).filter(
            ExternalServiceSecurityAssessment.external_service_id == service_id
        ).all()
        
        return {
            "service": service,
            "sla_metrics": metrics,
            "assessments": assessments,
            "sla_summary": self._summarize_sla(metrics),
            "latest_assessment": assessments[-1] if assessments else None,
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
    
    def _summarize_sla(self, metrics: List[SLAMetric]) -> Dict[str, Any]:
        """Summarize SLA metrics"""
        if not metrics:
            return {"total": 0, "met": 0, "violations": 0}
        
        return {
            "total": len(metrics),
            "met": sum(1 for m in metrics if m.sla_met),
            "violations": sum(m.sla_violations or 0 for m in metrics),
        }
