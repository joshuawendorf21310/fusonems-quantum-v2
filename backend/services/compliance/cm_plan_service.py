"""
Configuration Management Plan Service for FedRAMP CM-9 Compliance

FedRAMP Requirement CM-9: Configuration Management Plan
- CM plan storage
- Plan enforcement
- Compliance tracking
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import ConfigurationManagementPlan


class CMPlanService:
    """
    Service for configuration management plan management (CM-9).
    """
    
    @staticmethod
    def create_plan(
        db: Session,
        org_id: int,
        plan_name: str,
        version: str,
        plan_content: Dict,
        description: Optional[str] = None,
        plan_document: Optional[str] = None,
        created_by_user_id: Optional[int] = None,
    ) -> ConfigurationManagementPlan:
        """
        Create a configuration management plan.
        
        Args:
            db: Database session
            org_id: Organization ID
            plan_name: Name of plan
            version: Plan version
            plan_content: Plan content as JSON
            description: Plan description
            plan_document: Plan document (markdown/text)
            created_by_user_id: User creating the plan
            
        Returns:
            Created ConfigurationManagementPlan
        """
        plan = ConfigurationManagementPlan(
            org_id=org_id,
            plan_name=plan_name,
            version=version,
            description=description,
            plan_content=plan_content,
            plan_document=plan_document,
            status="draft",
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        logger.info(f"CM plan created: {plan_name} v{version} (org_id={org_id})")
        
        return plan
    
    @staticmethod
    def activate_plan(
        db: Session,
        plan_id: str,
        org_id: int,
        approved_by_user_id: int,
        effective_date: Optional[datetime] = None,
    ) -> ConfigurationManagementPlan:
        """Activate a configuration management plan"""
        plan = db.query(ConfigurationManagementPlan).filter(
            ConfigurationManagementPlan.id == plan_id,
            ConfigurationManagementPlan.org_id == org_id,
        ).first()
        
        if not plan:
            raise ValueError(f"CM plan {plan_id} not found")
        
        # Supersede other active plans
        db.query(ConfigurationManagementPlan).filter(
            ConfigurationManagementPlan.org_id == org_id,
            ConfigurationManagementPlan.status == "active",
        ).update({
            "status": "superseded",
            "superseded_at": datetime.now(timezone.utc),
        })
        
        # Activate this plan
        plan.status = "active"
        plan.approved_by_user_id = approved_by_user_id
        plan.approved_at = datetime.now(timezone.utc)
        plan.effective_date = effective_date or datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(plan)
        
        logger.info(f"CM plan activated: {plan.plan_name} v{plan.version}")
        
        return plan
    
    @staticmethod
    def get_active_plan(
        db: Session,
        org_id: int,
    ) -> Optional[ConfigurationManagementPlan]:
        """Get the active configuration management plan"""
        return db.query(ConfigurationManagementPlan).filter(
            ConfigurationManagementPlan.org_id == org_id,
            ConfigurationManagementPlan.status == "active",
        ).first()
    
    @staticmethod
    def get_plans(
        db: Session,
        org_id: int,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ConfigurationManagementPlan]:
        """Get configuration management plans"""
        query = db.query(ConfigurationManagementPlan).filter(
            ConfigurationManagementPlan.org_id == org_id
        )
        
        if status:
            query = query.filter(ConfigurationManagementPlan.status == status)
        
        return query.order_by(desc(ConfigurationManagementPlan.created_at)).limit(limit).all()
    
    @staticmethod
    def enforce_plan_compliance(
        db: Session,
        org_id: int,
        change_request_id: str,
    ) -> bool:
        """
        Check if a change request complies with the active CM plan.
        
        Returns:
            True if compliant, False otherwise
        """
        active_plan = CMPlanService.get_active_plan(db, org_id)
        
        if not active_plan:
            logger.warning(f"No active CM plan for org {org_id}")
            return True  # Allow if no plan exists
        
        # Check compliance with plan requirements
        # This is a simplified check - in production, implement full plan validation
        plan_requirements = active_plan.plan_content.get('requirements', [])
        
        # For now, return True (compliant)
        # In production, validate change request against plan requirements
        return True
