"""
CP-2: Contingency Plan Service

Manages contingency plan storage, versioning, distribution tracking,
and annual review automation.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.contingency import (
    ContingencyPlan,
    PlanDistribution,
    PlanStatus,
    DistributionStatus,
)
from utils.logger import logger


class ContingencyPlanService:
    """Service for managing contingency plans (CP-2)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    def create_plan(
        self,
        plan_id: str,
        version: str,
        title: str,
        plan_content: str,
        description: Optional[str] = None,
        plan_document_path: Optional[str] = None,
        review_frequency_days: int = 365,
        created_by_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContingencyPlan:
        """Create a new contingency plan version"""
        # Calculate next review date
        next_review_date = datetime.utcnow() + timedelta(days=review_frequency_days)
        
        plan = ContingencyPlan(
            org_id=self.org_id,
            plan_id=plan_id,
            version=version,
            title=title,
            description=description,
            plan_content=plan_content,
            plan_document_path=plan_document_path,
            status=PlanStatus.DRAFT.value,
            created_by_user_id=created_by_user_id,
            next_review_date=next_review_date,
            review_frequency_days=review_frequency_days,
            metadata=metadata or {},
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Created contingency plan {plan_id} v{version} for org {self.org_id}")
        return plan
    
    def get_plan(self, plan_id: int) -> Optional[ContingencyPlan]:
        """Get a contingency plan by ID"""
        return self.db.query(ContingencyPlan).filter(
            and_(
                ContingencyPlan.id == plan_id,
                ContingencyPlan.org_id == self.org_id,
            )
        ).first()
    
    def get_plan_by_plan_id(self, plan_id: str, version: Optional[str] = None) -> Optional[ContingencyPlan]:
        """Get a contingency plan by plan_id and optionally version"""
        query = self.db.query(ContingencyPlan).filter(
            and_(
                ContingencyPlan.plan_id == plan_id,
                ContingencyPlan.org_id == self.org_id,
            )
        )
        
        if version:
            query = query.filter(ContingencyPlan.version == version)
        else:
            # Get latest version
            query = query.order_by(desc(ContingencyPlan.version))
        
        return query.first()
    
    def list_plans(
        self,
        status: Optional[str] = None,
        plan_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContingencyPlan]:
        """List contingency plans with optional filters"""
        query = self.db.query(ContingencyPlan).filter(
            ContingencyPlan.org_id == self.org_id
        )
        
        if status:
            query = query.filter(ContingencyPlan.status == status)
        
        if plan_id:
            query = query.filter(ContingencyPlan.plan_id == plan_id)
        
        return query.order_by(desc(ContingencyPlan.created_at)).offset(offset).limit(limit).all()
    
    def update_plan(
        self,
        plan_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        plan_content: Optional[str] = None,
        plan_document_path: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ContingencyPlan]:
        """Update a contingency plan"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        if title is not None:
            plan.title = title
        if description is not None:
            plan.description = description
        if plan_content is not None:
            plan.plan_content = plan_content
        if plan_document_path is not None:
            plan.plan_document_path = plan_document_path
        if status is not None:
            plan.status = status
        if metadata is not None:
            plan.metadata = {**(plan.metadata or {}), **metadata}
        
        plan.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Updated contingency plan {plan.id}")
        return plan
    
    def approve_plan(
        self,
        plan_id: int,
        approved_by_user_id: int,
    ) -> Optional[ContingencyPlan]:
        """Approve a contingency plan"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        plan.status = PlanStatus.ACTIVE.value
        plan.approved_by_user_id = approved_by_user_id
        plan.approved_at = datetime.utcnow()
        plan.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Approved contingency plan {plan.id}")
        return plan
    
    def archive_plan(self, plan_id: int) -> Optional[ContingencyPlan]:
        """Archive a contingency plan"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        plan.status = PlanStatus.ARCHIVED.value
        plan.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Archived contingency plan {plan.id}")
        return plan
    
    def review_plan(
        self,
        plan_id: int,
        reviewed_by_user_id: Optional[int] = None,
    ) -> Optional[ContingencyPlan]:
        """Mark a plan as reviewed and update next review date"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        plan.last_review_date = datetime.utcnow()
        plan.next_review_date = datetime.utcnow() + timedelta(days=plan.review_frequency_days)
        plan.status = PlanStatus.ACTIVE.value
        plan.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Reviewed contingency plan {plan.id}, next review: {plan.next_review_date}")
        return plan
    
    def get_plans_due_for_review(self, days_ahead: int = 30) -> List[ContingencyPlan]:
        """Get plans that are due for review within the specified days"""
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(ContingencyPlan).filter(
            and_(
                ContingencyPlan.org_id == self.org_id,
                ContingencyPlan.status == PlanStatus.ACTIVE.value,
                ContingencyPlan.next_review_date <= cutoff_date,
            )
        ).order_by(ContingencyPlan.next_review_date).all()
    
    # Distribution methods
    
    def distribute_plan(
        self,
        plan_id: int,
        user_email: str,
        user_role: Optional[str] = None,
        distribution_method: str = "email",
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PlanDistribution:
        """Distribute a contingency plan to a user"""
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        distribution = PlanDistribution(
            plan_id=plan_id,
            org_id=self.org_id,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            distribution_method=distribution_method,
            status=DistributionStatus.PENDING.value,
            metadata=metadata or {},
        )
        
        self.db.add(distribution)
        self.db.commit()
        self.db.refresh(distribution)
        
        logger.info(f"Distributed plan {plan_id} to {user_email}")
        return distribution
    
    def acknowledge_distribution(
        self,
        distribution_id: int,
        ip_address: Optional[str] = None,
    ) -> Optional[PlanDistribution]:
        """Acknowledge receipt of a distributed plan"""
        distribution = self.db.query(PlanDistribution).filter(
            and_(
                PlanDistribution.id == distribution_id,
                PlanDistribution.org_id == self.org_id,
            )
        ).first()
        
        if not distribution:
            return None
        
        distribution.status = DistributionStatus.ACKNOWLEDGED.value
        distribution.acknowledged_at = datetime.utcnow()
        if ip_address:
            distribution.acknowledgment_ip_address = ip_address
        
        self.db.commit()
        self.db.refresh(distribution)
        
        logger.info(f"Acknowledged distribution {distribution_id}")
        return distribution
    
    def get_distributions(
        self,
        plan_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[PlanDistribution]:
        """Get plan distributions"""
        query = self.db.query(PlanDistribution).filter(
            PlanDistribution.org_id == self.org_id
        )
        
        if plan_id:
            query = query.filter(PlanDistribution.plan_id == plan_id)
        
        if status:
            query = query.filter(PlanDistribution.status == status)
        
        return query.order_by(desc(PlanDistribution.created_at)).all()
