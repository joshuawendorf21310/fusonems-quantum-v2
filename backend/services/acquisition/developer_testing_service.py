"""
SA-11: Developer Security Testing Service

FedRAMP SA-11 compliance service for:
- SAST integration
- DAST integration
- Test results tracking
- Vulnerability remediation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SecurityTest,
    SecurityTestResult,
    TestRemediation,
    TestType,
    TestStatus,
    VulnerabilitySeverity,
)


class DeveloperTestingService:
    """Service for SA-11: Developer Security Testing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_security_test(
        self,
        test_name: str,
        test_type: TestType,
        system_name: str,
        build_id: Optional[int] = None,
        release_id: Optional[int] = None,
        system_id: Optional[str] = None,
        test_description: Optional[str] = None,
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        test_tool: Optional[str] = None,
        test_configuration: Optional[Dict[str, Any]] = None,
        pass_criteria: Optional[Dict[str, Any]] = None,
    ) -> SecurityTest:
        """Create a security test"""
        test = SecurityTest(
            test_name=test_name,
            test_type=test_type.value,
            test_description=test_description,
            system_name=system_name,
            system_id=system_id,
            build_id=build_id,
            release_id=release_id,
            branch_name=branch_name,
            commit_hash=commit_hash,
            test_tool=test_tool,
            test_configuration=test_configuration,
            pass_criteria=pass_criteria,
            status=TestStatus.PENDING.value,
        )
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def start_test(self, test_id: int) -> SecurityTest:
        """Start a security test"""
        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = TestStatus.RUNNING.value
        test.started_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def complete_test(
        self,
        test_id: int,
        test_output: Optional[Dict[str, Any]] = None,
        test_report_url: Optional[str] = None,
        vulnerabilities_found: Optional[int] = None,
    ) -> SecurityTest:
        """Complete a security test"""
        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = TestStatus.COMPLETED.value
        test.completed_at = datetime.utcnow()
        
        if test.started_at:
            duration = (test.completed_at - test.started_at).total_seconds()
            test.duration_seconds = int(duration)
        
        if test_output:
            test.test_output = test_output
        
        if test_report_url:
            test.test_report_url = test_report_url
        
        if vulnerabilities_found is not None:
            test.vulnerabilities_found = vulnerabilities_found
        
        # Calculate pass/fail based on pass criteria
        if test.pass_criteria:
            max_critical = test.pass_criteria.get("max_critical", 0)
            max_high = test.pass_criteria.get("max_high", 0)
            
            critical = test.vulnerabilities_critical or 0
            high = test.vulnerabilities_high or 0
            
            test.test_passed = critical <= max_critical and high <= max_high
        else:
            # Default: pass if no critical or high vulnerabilities
            test.test_passed = (test.vulnerabilities_critical or 0) == 0 and (test.vulnerabilities_high or 0) == 0
        
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def add_test_result(
        self,
        security_test_id: int,
        finding_title: str,
        severity: VulnerabilitySeverity,
        finding_description: Optional[str] = None,
        finding_id: Optional[str] = None,
        vulnerability_type: Optional[str] = None,
        cwe_id: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
    ) -> SecurityTestResult:
        """Add a test result (vulnerability finding)"""
        result = SecurityTestResult(
            security_test_id=security_test_id,
            finding_id=finding_id,
            finding_title=finding_title,
            finding_description=finding_description,
            vulnerability_type=vulnerability_type,
            cwe_id=cwe_id,
            severity=severity.value,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            status="open",
        )
        self.db.add(result)
        
        # Update test vulnerability counts
        test = self.db.query(SecurityTest).filter(SecurityTest.id == security_test_id).first()
        if test:
            test.vulnerabilities_found = (test.vulnerabilities_found or 0) + 1
            
            if severity == VulnerabilitySeverity.CRITICAL:
                test.vulnerabilities_critical = (test.vulnerabilities_critical or 0) + 1
            elif severity == VulnerabilitySeverity.HIGH:
                test.vulnerabilities_high = (test.vulnerabilities_high or 0) + 1
            elif severity == VulnerabilitySeverity.MEDIUM:
                test.vulnerabilities_medium = (test.vulnerabilities_medium or 0) + 1
            else:
                test.vulnerabilities_low = (test.vulnerabilities_low or 0) + 1
        
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def update_test_result_status(
        self,
        test_result_id: int,
        status: str,
        remediation_notes: Optional[str] = None,
        fixed_in_build: Optional[str] = None,
        fixed_in_release: Optional[str] = None,
    ) -> SecurityTestResult:
        """Update test result status"""
        result = self.db.query(SecurityTestResult).filter(
            SecurityTestResult.id == test_result_id
        ).first()
        if not result:
            raise ValueError(f"Test result {test_result_id} not found")
        
        result.status = status
        
        if status == "in_progress":
            result.remediation_status = "in_progress"
        elif status == "fixed":
            result.remediation_status = "completed"
            result.fixed_in_build = fixed_in_build
            result.fixed_in_release = fixed_in_release
        
        if remediation_notes:
            result.remediation_notes = remediation_notes
        
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def verify_fix(
        self,
        test_result_id: int,
        verified_by: str,
    ) -> SecurityTestResult:
        """Verify that a vulnerability has been fixed"""
        result = self.db.query(SecurityTestResult).filter(
            SecurityTestResult.id == test_result_id
        ).first()
        if not result:
            raise ValueError(f"Test result {test_result_id} not found")
        
        result.verified_fixed = True
        result.verified_by = verified_by
        result.verification_date = datetime.utcnow()
        result.status = "fixed"
        
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def create_remediation(
        self,
        security_test_id: int,
        remediation_plan: str,
        test_result_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
        target_completion_date: Optional[datetime] = None,
        remediation_actions: Optional[List[str]] = None,
    ) -> TestRemediation:
        """Create a remediation plan"""
        remediation = TestRemediation(
            security_test_id=security_test_id,
            test_result_id=test_result_id,
            remediation_plan=remediation_plan,
            remediation_actions=remediation_actions,
            assigned_to=assigned_to,
            target_completion_date=target_completion_date,
            status="planned",
        )
        self.db.add(remediation)
        self.db.commit()
        self.db.refresh(remediation)
        return remediation
    
    def complete_remediation(
        self,
        remediation_id: int,
        completed_by: str,
    ) -> TestRemediation:
        """Mark remediation as completed"""
        remediation = self.db.query(TestRemediation).filter(
            TestRemediation.id == remediation_id
        ).first()
        if not remediation:
            raise ValueError(f"Remediation {remediation_id} not found")
        
        remediation.status = "completed"
        remediation.completed_at = datetime.utcnow()
        remediation.completed_by = completed_by
        remediation.completion_percentage = 100.0
        
        self.db.commit()
        self.db.refresh(remediation)
        return remediation
    
    def list_tests(
        self,
        system_name: Optional[str] = None,
        test_type: Optional[TestType] = None,
        status: Optional[TestStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SecurityTest], int]:
        """List security tests"""
        query = self.db.query(SecurityTest)
        
        if system_name:
            query = query.filter(SecurityTest.system_name == system_name)
        
        if test_type:
            query = query.filter(SecurityTest.test_type == test_type.value)
        
        if status:
            query = query.filter(SecurityTest.status == status.value)
        
        total = query.count()
        tests = query.order_by(desc(SecurityTest.created_at)).offset(offset).limit(limit).all()
        
        return tests, total
    
    def get_test_summary(self, test_id: int) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        results = self.db.query(SecurityTestResult).filter(
            SecurityTestResult.security_test_id == test_id
        ).all()
        
        remediations = self.db.query(TestRemediation).filter(
            TestRemediation.security_test_id == test_id
        ).all()
        
        return {
            "test": test,
            "results": results,
            "remediations": remediations,
            "results_summary": self._summarize_results(results),
            "remediation_summary": self._summarize_remediations(remediations),
        }
    
    def _summarize_results(self, results: List[SecurityTestResult]) -> Dict[str, Any]:
        """Summarize test results"""
        return {
            "total": len(results),
            "open": sum(1 for r in results if r.status == "open"),
            "in_progress": sum(1 for r in results if r.status == "in_progress"),
            "fixed": sum(1 for r in results if r.status == "fixed"),
            "by_severity": {
                "critical": sum(1 for r in results if r.severity == VulnerabilitySeverity.CRITICAL.value),
                "high": sum(1 for r in results if r.severity == VulnerabilitySeverity.HIGH.value),
                "medium": sum(1 for r in results if r.severity == VulnerabilitySeverity.MEDIUM.value),
                "low": sum(1 for r in results if r.severity == VulnerabilitySeverity.LOW.value),
            },
        }
    
    def _summarize_remediations(self, remediations: List[TestRemediation]) -> Dict[str, Any]:
        """Summarize remediations"""
        return {
            "total": len(remediations),
            "planned": sum(1 for r in remediations if r.status == "planned"),
            "in_progress": sum(1 for r in remediations if r.status == "in_progress"),
            "completed": sum(1 for r in remediations if r.status == "completed"),
        }
