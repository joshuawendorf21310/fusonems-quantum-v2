"""
SA-15: Development Process, Standards, and Tools Service

FedRAMP SA-15 compliance service for:
- Secure coding standards
- Tool approval
- Compliance checking
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    DevelopmentTool,
    SecureCodingStandard,
    ComplianceCheck,
    ToolStatus,
    StandardStatus,
)


class DevelopmentStandardsService:
    """Service for SA-15: Development Process, Standards, and Tools"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tool(
        self,
        tool_name: str,
        tool_type: str,
        tool_vendor: Optional[str] = None,
        tool_version: Optional[str] = None,
        tool_description: Optional[str] = None,
        tool_url: Optional[str] = None,
    ) -> DevelopmentTool:
        """Create a development tool"""
        tool = DevelopmentTool(
            tool_name=tool_name,
            tool_type=tool_type,
            tool_vendor=tool_vendor,
            tool_version=tool_version,
            tool_description=tool_description,
            tool_url=tool_url,
            status=ToolStatus.PENDING_APPROVAL.value,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool
    
    def approve_tool(
        self,
        tool_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None,
        compliance_checked: bool = False,
        compliance_notes: Optional[str] = None,
    ) -> DevelopmentTool:
        """Approve a development tool"""
        tool = self.db.query(DevelopmentTool).filter(DevelopmentTool.id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool.status = ToolStatus.APPROVED.value
        tool.approved_by = approved_by
        tool.approval_date = datetime.utcnow()
        tool.approval_notes = approval_notes
        tool.compliance_checked = compliance_checked
        tool.compliance_notes = compliance_notes
        
        self.db.commit()
        self.db.refresh(tool)
        return tool
    
    def create_standard(
        self,
        standard_name: str,
        standard_type: str,
        requirements: Optional[List[str]] = None,
        standard_version: Optional[str] = None,
        standard_description: Optional[str] = None,
        standard_reference: Optional[str] = None,
        mandatory_requirements: Optional[List[str]] = None,
        applicable_languages: Optional[List[str]] = None,
        applicable_systems: Optional[List[str]] = None,
        enforcement_level: Optional[str] = None,
    ) -> SecureCodingStandard:
        """Create a secure coding standard"""
        standard = SecureCodingStandard(
            standard_name=standard_name,
            standard_type=standard_type,
            standard_version=standard_version,
            standard_description=standard_description,
            standard_reference=standard_reference,
            requirements=requirements,
            mandatory_requirements=mandatory_requirements,
            applicable_languages=applicable_languages,
            applicable_systems=applicable_systems,
            enforcement_level=enforcement_level,
            status=StandardStatus.ACTIVE.value,
        )
        self.db.add(standard)
        self.db.commit()
        self.db.refresh(standard)
        return standard
    
    def enable_compliance_checking(
        self,
        standard_id: int,
        compliance_tool: str,
    ) -> SecureCodingStandard:
        """Enable compliance checking for a standard"""
        standard = self.db.query(SecureCodingStandard).filter(
            SecureCodingStandard.id == standard_id
        ).first()
        if not standard:
            raise ValueError(f"Standard {standard_id} not found")
        
        standard.compliance_checking_enabled = True
        standard.compliance_tool = compliance_tool
        
        self.db.commit()
        self.db.refresh(standard)
        return standard
    
    def create_compliance_check(
        self,
        check_name: str,
        system_name: str,
        standard_id: Optional[int] = None,
        system_id: Optional[str] = None,
        build_id: Optional[int] = None,
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        check_tool: Optional[str] = None,
        check_configuration: Optional[Dict[str, Any]] = None,
        checked_by: Optional[str] = None,
    ) -> ComplianceCheck:
        """Create a compliance check"""
        check = ComplianceCheck(
            check_name=check_name,
            standard_id=standard_id,
            system_name=system_name,
            system_id=system_id,
            build_id=build_id,
            branch_name=branch_name,
            commit_hash=commit_hash,
            check_tool=check_tool,
            check_configuration=check_configuration,
            checked_by=checked_by,
        )
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check
    
    def update_compliance_check_results(
        self,
        check_id: int,
        requirements_checked: int,
        requirements_passed: int,
        requirements_failed: int,
        violations: Optional[List[Dict[str, Any]]] = None,
    ) -> ComplianceCheck:
        """Update compliance check results"""
        check = self.db.query(ComplianceCheck).filter(ComplianceCheck.id == check_id).first()
        if not check:
            raise ValueError(f"Compliance check {check_id} not found")
        
        check.requirements_checked = requirements_checked
        check.requirements_passed = requirements_passed
        check.requirements_failed = requirements_failed
        check.compliance_percentage = (requirements_passed / requirements_checked * 100) if requirements_checked > 0 else 0
        check.compliant = requirements_failed == 0
        
        if violations:
            check.violations = violations
            check.critical_violations = sum(1 for v in violations if v.get("severity") == "critical")
            check.high_violations = sum(1 for v in violations if v.get("severity") == "high")
            check.medium_violations = sum(1 for v in violations if v.get("severity") == "medium")
            check.low_violations = sum(1 for v in violations if v.get("severity") == "low")
        
        self.db.commit()
        self.db.refresh(check)
        return check
    
    def list_tools(
        self,
        tool_type: Optional[str] = None,
        status: Optional[ToolStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DevelopmentTool], int]:
        """List development tools"""
        query = self.db.query(DevelopmentTool)
        
        if tool_type:
            query = query.filter(DevelopmentTool.tool_type == tool_type)
        
        if status:
            query = query.filter(DevelopmentTool.status == status.value)
        
        total = query.count()
        tools = query.order_by(desc(DevelopmentTool.created_at)).offset(offset).limit(limit).all()
        
        return tools, total
    
    def list_standards(
        self,
        standard_type: Optional[str] = None,
        status: Optional[StandardStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SecureCodingStandard], int]:
        """List secure coding standards"""
        query = self.db.query(SecureCodingStandard)
        
        if standard_type:
            query = query.filter(SecureCodingStandard.standard_type == standard_type)
        
        if status:
            query = query.filter(SecureCodingStandard.status == status.value)
        
        total = query.count()
        standards = query.order_by(desc(SecureCodingStandard.created_at)).offset(offset).limit(limit).all()
        
        return standards, total
    
    def list_compliance_checks(
        self,
        system_name: Optional[str] = None,
        standard_id: Optional[int] = None,
        compliant: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[ComplianceCheck], int]:
        """List compliance checks"""
        query = self.db.query(ComplianceCheck)
        
        if system_name:
            query = query.filter(ComplianceCheck.system_name == system_name)
        
        if standard_id:
            query = query.filter(ComplianceCheck.standard_id == standard_id)
        
        if compliant is not None:
            query = query.filter(ComplianceCheck.compliant == compliant)
        
        total = query.count()
        checks = query.order_by(desc(ComplianceCheck.check_date)).offset(offset).limit(limit).all()
        
        return checks, total
    
    def get_compliance_summary(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance summary"""
        query = self.db.query(ComplianceCheck)
        
        if system_name:
            query = query.filter(ComplianceCheck.system_name == system_name)
        
        checks = query.all()
        
        return {
            "total_checks": len(checks),
            "compliant_checks": sum(1 for c in checks if c.compliant),
            "non_compliant_checks": sum(1 for c in checks if not c.compliant),
            "average_compliance": sum(c.compliance_percentage for c in checks) / len(checks) if checks else 0,
            "violations_summary": self._summarize_violations(checks),
        }
    
    def _summarize_violations(self, checks: List[ComplianceCheck]) -> Dict[str, int]:
        """Summarize violations across checks"""
        return {
            "critical": sum(c.critical_violations for c in checks),
            "high": sum(c.high_violations for c in checks),
            "medium": sum(c.medium_violations for c in checks),
            "low": sum(c.low_violations for c in checks),
        }
