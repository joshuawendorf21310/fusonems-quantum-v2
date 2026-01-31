"""
CP-4: Contingency Plan Testing Service

Manages contingency plan testing schedules, results documentation,
and issue tracking.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.contingency import (
    ContingencyPlanTest,
    TestStatus,
    TestResult,
)
from utils.logger import logger


class PlanTestingService:
    """Service for managing contingency plan testing (CP-4)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    def create_test(
        self,
        plan_id: int,
        test_name: str,
        test_type: str,
        scheduled_date: datetime,
        test_description: Optional[str] = None,
        test_procedures: Optional[str] = None,
        test_team: Optional[List[int]] = None,
        conducted_by_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContingencyPlanTest:
        """Create a new contingency plan test"""
        test = ContingencyPlanTest(
            org_id=self.org_id,
            plan_id=plan_id,
            test_name=test_name,
            test_type=test_type,
            test_description=test_description,
            scheduled_date=scheduled_date,
            status=TestStatus.SCHEDULED.value,
            test_procedures=test_procedures,
            test_team=test_team or [],
            conducted_by_user_id=conducted_by_user_id,
            metadata=metadata or {},
        )
        
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Created contingency plan test {test.id} for plan {plan_id}")
        return test
    
    def get_test(self, test_id: int) -> Optional[ContingencyPlanTest]:
        """Get a test by ID"""
        return self.db.query(ContingencyPlanTest).filter(
            and_(
                ContingencyPlanTest.id == test_id,
                ContingencyPlanTest.org_id == self.org_id,
            )
        ).first()
    
    def list_tests(
        self,
        plan_id: Optional[int] = None,
        status: Optional[str] = None,
        test_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContingencyPlanTest]:
        """List tests with optional filters"""
        query = self.db.query(ContingencyPlanTest).filter(
            ContingencyPlanTest.org_id == self.org_id
        )
        
        if plan_id:
            query = query.filter(ContingencyPlanTest.plan_id == plan_id)
        
        if status:
            query = query.filter(ContingencyPlanTest.status == status)
        
        if test_type:
            query = query.filter(ContingencyPlanTest.test_type == test_type)
        
        return query.order_by(desc(ContingencyPlanTest.scheduled_date)).offset(offset).limit(limit).all()
    
    def start_test(self, test_id: int) -> Optional[ContingencyPlanTest]:
        """Start a test"""
        test = self.get_test(test_id)
        if not test:
            return None
        
        test.status = TestStatus.IN_PROGRESS.value
        test.start_date = datetime.utcnow()
        test.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Started test {test_id}")
        return test
    
    def complete_test(
        self,
        test_id: int,
        test_result: str,
        test_results: Optional[str] = None,
        test_report_path: Optional[str] = None,
        issues_identified: Optional[List[Dict[str, Any]]] = None,
        remediation_plan: Optional[str] = None,
    ) -> Optional[ContingencyPlanTest]:
        """Complete a test with results"""
        test = self.get_test(test_id)
        if not test:
            return None
        
        test.status = TestStatus.COMPLETED.value
        test.end_date = datetime.utcnow()
        test.test_result = test_result
        test.test_results = test_results
        test.test_report_path = test_report_path
        test.issues_identified = issues_identified or []
        test.remediation_plan = remediation_plan
        
        test.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Completed test {test_id} with result {test_result}")
        return test
    
    def update_test(
        self,
        test_id: int,
        test_results: Optional[str] = None,
        test_report_path: Optional[str] = None,
        issues_identified: Optional[List[Dict[str, Any]]] = None,
        remediation_plan: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ContingencyPlanTest]:
        """Update test details"""
        test = self.get_test(test_id)
        if not test:
            return None
        
        if test_results is not None:
            test.test_results = test_results
        
        if test_report_path is not None:
            test.test_report_path = test_report_path
        
        if issues_identified is not None:
            test.issues_identified = issues_identified
        
        if remediation_plan is not None:
            test.remediation_plan = remediation_plan
        
        if metadata is not None:
            test.metadata = {**(test.metadata or {}), **metadata}
        
        test.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(test)
        
        logger.info(f"Updated test {test_id}")
        return test
    
    def get_plan_tests(self, plan_id: int) -> List[ContingencyPlanTest]:
        """Get all tests for a specific plan"""
        return self.list_tests(plan_id=plan_id)
    
    def get_upcoming_tests(self, days_ahead: int = 30) -> List[ContingencyPlanTest]:
        """Get tests scheduled within the specified days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(ContingencyPlanTest).filter(
            and_(
                ContingencyPlanTest.org_id == self.org_id,
                ContingencyPlanTest.status == TestStatus.SCHEDULED.value,
                ContingencyPlanTest.scheduled_date <= cutoff_date,
            )
        ).order_by(ContingencyPlanTest.scheduled_date).all()
