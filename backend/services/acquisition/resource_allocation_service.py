"""
SA-2: Allocation of Resources Service

FedRAMP SA-2 compliance service for:
- Budget tracking for security
- Resource planning
- Cost analysis
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SecurityBudget,
    ResourcePlan,
    CostAnalysis,
    BudgetCategory,
    ResourceStatus,
)


class ResourceAllocationService:
    """Service for SA-2: Allocation of Resources"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_budget(
        self,
        budget_name: str,
        budget_category: BudgetCategory,
        fiscal_year: int,
        allocated_amount: float,
        budget_description: Optional[str] = None,
        planned_start_date: Optional[datetime] = None,
        planned_end_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> SecurityBudget:
        """Create a new security budget"""
        budget = SecurityBudget(
            budget_name=budget_name,
            budget_description=budget_description,
            budget_category=budget_category.value,
            fiscal_year=fiscal_year,
            allocated_amount=allocated_amount,
            spent_amount=0.0,
            remaining_amount=allocated_amount,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            status=ResourceStatus.PLANNED.value,
            notes=notes,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget
    
    def update_budget(
        self,
        budget_id: int,
        allocated_amount: Optional[float] = None,
        spent_amount: Optional[float] = None,
        status: Optional[ResourceStatus] = None,
        **kwargs
    ) -> SecurityBudget:
        """Update a security budget"""
        budget = self.db.query(SecurityBudget).filter(SecurityBudget.id == budget_id).first()
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")
        
        if allocated_amount is not None:
            budget.allocated_amount = allocated_amount
            budget.remaining_amount = allocated_amount - budget.spent_amount
        
        if spent_amount is not None:
            budget.spent_amount = spent_amount
            budget.remaining_amount = budget.allocated_amount - spent_amount
        
        if status:
            budget.status = status.value
        
        for key, value in kwargs.items():
            if hasattr(budget, key):
                setattr(budget, key, value)
        
        self.db.commit()
        self.db.refresh(budget)
        return budget
    
    def create_resource_plan(
        self,
        security_budget_id: int,
        plan_name: str,
        resource_type: str,
        resource_name: str,
        quantity: int,
        unit_cost: float,
        plan_description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ResourcePlan:
        """Create a resource plan"""
        total_cost = quantity * unit_cost
        
        plan = ResourcePlan(
            security_budget_id=security_budget_id,
            plan_name=plan_name,
            plan_description=plan_description,
            resource_type=resource_type,
            resource_name=resource_name,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            start_date=start_date,
            end_date=end_date,
            status=ResourceStatus.PLANNED.value,
        )
        self.db.add(plan)
        
        # Update budget spent amount
        budget = self.db.query(SecurityBudget).filter(SecurityBudget.id == security_budget_id).first()
        if budget:
            budget.spent_amount += total_cost
            budget.remaining_amount = budget.allocated_amount - budget.spent_amount
        
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def create_cost_analysis(
        self,
        security_budget_id: int,
        analysis_name: str,
        direct_costs: float,
        indirect_costs: float,
        analyzed_by: Optional[str] = None,
        expected_benefits: Optional[str] = None,
        roi_estimate: Optional[float] = None,
        alternatives_considered: Optional[List[Dict[str, Any]]] = None,
        selected_option_rationale: Optional[str] = None,
    ) -> CostAnalysis:
        """Create a cost analysis"""
        total_costs = direct_costs + indirect_costs
        
        analysis = CostAnalysis(
            security_budget_id=security_budget_id,
            analysis_name=analysis_name,
            analyzed_by=analyzed_by,
            direct_costs=direct_costs,
            indirect_costs=indirect_costs,
            total_costs=total_costs,
            expected_benefits=expected_benefits,
            roi_estimate=roi_estimate,
            alternatives_considered=alternatives_considered,
            selected_option_rationale=selected_option_rationale,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def list_budgets(
        self,
        fiscal_year: Optional[int] = None,
        budget_category: Optional[BudgetCategory] = None,
        status: Optional[ResourceStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SecurityBudget], int]:
        """List security budgets"""
        query = self.db.query(SecurityBudget)
        
        if fiscal_year:
            query = query.filter(SecurityBudget.fiscal_year == fiscal_year)
        
        if budget_category:
            query = query.filter(SecurityBudget.budget_category == budget_category.value)
        
        if status:
            query = query.filter(SecurityBudget.status == status.value)
        
        total = query.count()
        budgets = query.order_by(desc(SecurityBudget.created_at)).offset(offset).limit(limit).all()
        
        return budgets, total
    
    def get_budget_summary(self, fiscal_year: Optional[int] = None) -> Dict[str, Any]:
        """Get budget summary statistics"""
        query = self.db.query(SecurityBudget)
        
        if fiscal_year:
            query = query.filter(SecurityBudget.fiscal_year == fiscal_year)
        
        budgets = query.all()
        
        total_allocated = sum(b.allocated_amount for b in budgets)
        total_spent = sum(b.spent_amount for b in budgets)
        total_remaining = sum(b.remaining_amount for b in budgets)
        
        return {
            "total_budgets": len(budgets),
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "utilization_percentage": (total_spent / total_allocated * 100) if total_allocated > 0 else 0,
            "by_category": self._summarize_by_category(budgets),
            "by_status": self._summarize_by_status(budgets),
        }
    
    def _summarize_by_category(self, budgets: List[SecurityBudget]) -> Dict[str, Any]:
        """Summarize budgets by category"""
        summary = {}
        for budget in budgets:
            category = budget.budget_category
            if category not in summary:
                summary[category] = {
                    "count": 0,
                    "allocated": 0.0,
                    "spent": 0.0,
                    "remaining": 0.0,
                }
            summary[category]["count"] += 1
            summary[category]["allocated"] += budget.allocated_amount
            summary[category]["spent"] += budget.spent_amount
            summary[category]["remaining"] += budget.remaining_amount
        return summary
    
    def _summarize_by_status(self, budgets: List[SecurityBudget]) -> Dict[str, int]:
        """Summarize budgets by status"""
        summary = {}
        for budget in budgets:
            status = budget.status
            summary[status] = summary.get(status, 0) + 1
        return summary
