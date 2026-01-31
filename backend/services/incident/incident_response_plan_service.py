"""
IR-8: Incident Response Plan Service for FedRAMP Compliance

Provides comprehensive incident response plan management:
- Plan storage and versioning
- Plan distribution tracking
- Plan review automation
- Plan updates tracking
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.logger import logger
from models.incident import (
    IncidentResponsePlan,
    PlanDistribution,
    PlanStatus,
)
from models.user import User
from utils.audit import record_audit


class IncidentResponsePlanService:
    """Service for managing incident response plans per FedRAMP IR-8 requirements"""

    @staticmethod
    def create_plan(
        db: Session,
        org_id: int,
        name: str,
        plan_content: str,
        version: str = "1.0",
        description: Optional[str] = None,
        plan_document_url: Optional[str] = None,
        review_frequency_days: int = 365,
        created_by_user_id: Optional[int] = None,
        request=None,
    ) -> IncidentResponsePlan:
        """Create a new incident response plan"""
        plan = IncidentResponsePlan(
            org_id=org_id,
            name=name,
            version=version,
            description=description,
            plan_content=plan_content,
            plan_document_url=plan_document_url,
            review_frequency_days=review_frequency_days,
            status=PlanStatus.DRAFT.value,
            is_active=False,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # Audit log
        if request and created_by_user_id:
            try:
                user = db.query(User).filter(User.id == created_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_response_plan_created",
                        resource="incident_response_plan",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR8_PLAN_CREATED",
                        after_state={
                            "plan_id": str(plan.id),
                            "name": name,
                            "version": version,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for plan creation: {e}", exc_info=True)
        
        logger.info(f"Incident response plan created: {name}, version={version}")
        return plan

    @staticmethod
    def approve_plan(
        db: Session,
        plan_id: UUID,
        approved_by_user_id: int,
        effective_date: Optional[datetime] = None,
        request=None,
    ) -> IncidentResponsePlan:
        """Approve and activate an incident response plan"""
        plan = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.id == plan_id,
        ).first()
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        # Deactivate other active plans for the same org
        db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.org_id == plan.org_id,
            IncidentResponsePlan.id != plan_id,
            IncidentResponsePlan.is_active == True,
        ).update({"is_active": False})
        
        # Activate this plan
        plan.status = PlanStatus.ACTIVE.value
        plan.is_active = True
        plan.approved_by_user_id = approved_by_user_id
        plan.approved_at = datetime.now(timezone.utc)
        plan.effective_date = effective_date or datetime.now(timezone.utc)
        
        # Set next review date
        if plan.review_frequency_days > 0:
            plan.next_review_date = plan.effective_date + timedelta(days=plan.review_frequency_days)
        
        db.commit()
        db.refresh(plan)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == approved_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_response_plan_approved",
                        resource="incident_response_plan",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR8_PLAN_APPROVED",
                        before_state={"status": PlanStatus.DRAFT.value, "is_active": False},
                        after_state={"status": PlanStatus.ACTIVE.value, "is_active": True},
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for plan approval: {e}", exc_info=True)
        
        logger.info(f"Incident response plan approved: plan_id={plan_id}")
        return plan

    @staticmethod
    def create_new_version(
        db: Session,
        org_id: int,
        base_plan_id: UUID,
        new_version: str,
        plan_content: str,
        description: Optional[str] = None,
        created_by_user_id: Optional[int] = None,
        request=None,
    ) -> IncidentResponsePlan:
        """Create a new version of an existing plan"""
        base_plan = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.id == base_plan_id,
            IncidentResponsePlan.org_id == org_id,
        ).first()
        
        if not base_plan:
            raise ValueError(f"Base plan not found: {base_plan_id}")
        
        new_plan = IncidentResponsePlan(
            org_id=org_id,
            name=base_plan.name,
            version=new_version,
            description=description or base_plan.description,
            plan_content=plan_content,
            plan_document_url=base_plan.plan_document_url,
            review_frequency_days=base_plan.review_frequency_days,
            status=PlanStatus.DRAFT.value,
            is_active=False,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        # Audit log
        if request and created_by_user_id:
            try:
                user = db.query(User).filter(User.id == created_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_response_plan_version_created",
                        resource="incident_response_plan",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR8_PLAN_VERSION_CREATED",
                        after_state={
                            "new_plan_id": str(new_plan.id),
                            "base_plan_id": str(base_plan_id),
                            "new_version": new_version,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for version creation: {e}", exc_info=True)
        
        logger.info(f"New plan version created: base={base_plan_id}, version={new_version}")
        return new_plan

    @staticmethod
    def distribute_plan(
        db: Session,
        plan_id: UUID,
        user_ids: List[int],
        distribution_method: str = "portal",
        distributed_by_user_id: Optional[int] = None,
        request=None,
    ) -> List[PlanDistribution]:
        """Distribute plan to users"""
        plan = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.id == plan_id,
        ).first()
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        distributions = []
        for user_id in user_ids:
            # Check if already distributed
            existing = db.query(PlanDistribution).filter(
                PlanDistribution.plan_id == plan_id,
                PlanDistribution.user_id == user_id,
            ).first()
            
            if existing:
                distributions.append(existing)
                continue
            
            distribution = PlanDistribution(
                org_id=plan.org_id,
                plan_id=plan_id,
                user_id=user_id,
                distribution_method=distribution_method,
                distributed_by_user_id=distributed_by_user_id,
            )
            
            db.add(distribution)
            distributions.append(distribution)
        
        db.commit()
        
        # Refresh all
        for dist in distributions:
            db.refresh(dist)
        
        # Audit log
        if request and distributed_by_user_id:
            try:
                user = db.query(User).filter(User.id == distributed_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_response_plan_distributed",
                        resource="plan_distribution",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR8_PLAN_DISTRIBUTED",
                        after_state={
                            "plan_id": str(plan_id),
                            "user_count": len(user_ids),
                            "distribution_method": distribution_method,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for distribution: {e}", exc_info=True)
        
        logger.info(f"Plan distributed: plan_id={plan_id}, users={len(user_ids)}")
        return distributions

    @staticmethod
    def acknowledge_plan(
        db: Session,
        distribution_id: UUID,
        user_id: int,
        ip_address: Optional[str] = None,
        request=None,
    ) -> PlanDistribution:
        """Acknowledge receipt of plan"""
        distribution = db.query(PlanDistribution).filter(
            PlanDistribution.id == distribution_id,
            PlanDistribution.user_id == user_id,
        ).first()
        
        if not distribution:
            raise ValueError(f"Distribution not found: {distribution_id}")
        
        distribution.acknowledged_at = datetime.now(timezone.utc)
        if ip_address:
            distribution.acknowledgment_ip_address = ip_address
        
        db.commit()
        db.refresh(distribution)
        
        logger.info(f"Plan acknowledged: distribution_id={distribution_id}, user_id={user_id}")
        return distribution

    @staticmethod
    def review_plan(
        db: Session,
        plan_id: UUID,
        reviewed_by_user_id: int,
        review_notes: Optional[str] = None,
        request=None,
    ) -> IncidentResponsePlan:
        """Mark plan as reviewed"""
        plan = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.id == plan_id,
        ).first()
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        plan.last_reviewed_at = datetime.now(timezone.utc)
        
        # Update next review date
        if plan.review_frequency_days > 0:
            plan.next_review_date = plan.last_reviewed_at + timedelta(days=plan.review_frequency_days)
        
        # If plan was under review, mark as active
        if plan.status == PlanStatus.UNDER_REVIEW.value:
            plan.status = PlanStatus.ACTIVE.value
        
        db.commit()
        db.refresh(plan)
        
        # Audit log
        if request:
            try:
                user = db.query(User).filter(User.id == reviewed_by_user_id).first()
                if user:
                    record_audit(
                        db=db,
                        request=request,
                        user=user,
                        action="incident_response_plan_reviewed",
                        resource="incident_response_plan",
                        outcome="Success",
                        classification="NON_PHI",
                        reason_code="IR8_PLAN_REVIEWED",
                        after_state={
                            "plan_id": str(plan_id),
                            "next_review_date": plan.next_review_date.isoformat() if plan.next_review_date else None,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to record audit for plan review: {e}", exc_info=True)
        
        logger.info(f"Plan reviewed: plan_id={plan_id}")
        return plan

    @staticmethod
    def get_plans_due_for_review(
        db: Session,
        org_id: int,
    ) -> List[IncidentResponsePlan]:
        """Get plans that are due for review"""
        now = datetime.now(timezone.utc)
        
        plans = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.org_id == org_id,
            IncidentResponsePlan.is_active == True,
            IncidentResponsePlan.next_review_date <= now,
        ).all()
        
        return plans

    @staticmethod
    def get_distribution_status(
        db: Session,
        plan_id: UUID,
    ) -> Dict[str, Any]:
        """Get plan distribution status"""
        plan = db.query(IncidentResponsePlan).filter(
            IncidentResponsePlan.id == plan_id,
        ).first()
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        distributions = db.query(PlanDistribution).filter(
            PlanDistribution.plan_id == plan_id,
        ).all()
        
        total_distributed = len(distributions)
        acknowledged = sum(1 for d in distributions if d.acknowledged_at)
        not_acknowledged = total_distributed - acknowledged
        
        return {
            "plan_id": str(plan_id),
            "plan_name": plan.name,
            "plan_version": plan.version,
            "total_distributed": total_distributed,
            "acknowledged": acknowledged,
            "not_acknowledged": not_acknowledged,
            "acknowledgment_rate": (
                (acknowledged / total_distributed * 100)
                if total_distributed > 0 else 0
            ),
            "distributions": [
                {
                    "distribution_id": str(d.id),
                    "user_id": d.user_id,
                    "distributed_at": d.distributed_at.isoformat(),
                    "acknowledged_at": d.acknowledged_at.isoformat() if d.acknowledged_at else None,
                }
                for d in distributions
            ],
        }
