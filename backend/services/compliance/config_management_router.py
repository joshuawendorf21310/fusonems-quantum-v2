"""
Configuration Management API Router for FedRAMP CM-2, CM-3, CM-6

Provides REST API endpoints for:
- Configuration baseline management
- Configuration change requests
- Change approval workflow
- Configuration compliance checking
- Drift detection and reporting
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_roles
from models.user import User, UserRole
from services.compliance.configuration_management import ConfigurationManagementService
from services.compliance.config_baseline_service import ConfigurationBaselineService
from models.configuration import (
    ConfigurationBaseline,
    ConfigurationChangeRequest,
    ConfigurationChangeApproval,
    ConfigurationComplianceStatus,
    ChangeRequestPriority,
    ChangeRequestStatus,
    ComplianceStatus,
)


router = APIRouter(
    prefix="/api/compliance/configuration",
    tags=["Configuration Management"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class BaselineCreate(BaseModel):
    name: str = Field(..., description="Baseline name")
    description: Optional[str] = None
    version: str = Field(default="1.0", description="Version string")
    configuration_snapshot: dict = Field(..., description="Configuration snapshot as JSON")
    scope: Optional[List[str]] = Field(default=None, description="List of components in scope")


class BaselineResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    version: str
    status: str
    scope: Optional[List[str]]
    created_at: datetime
    activated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ChangeRequestCreate(BaseModel):
    title: str = Field(..., description="Change request title")
    description: str = Field(..., description="Detailed description")
    configuration_changes: dict = Field(..., description="Configuration changes as JSON")
    change_reason: str = Field(..., description="Reason for change")
    priority: ChangeRequestPriority = Field(default=ChangeRequestPriority.MEDIUM)
    baseline_id: Optional[UUID] = None
    affected_components: Optional[List[str]] = None
    risk_level: Optional[str] = None
    impact_assessment: Optional[str] = None
    scheduled_implementation_date: Optional[datetime] = None


class ChangeRequestResponse(BaseModel):
    id: UUID
    change_number: str
    title: str
    description: str
    status: str
    priority: str
    requested_at: datetime
    scheduled_implementation_date: Optional[datetime]
    actual_implementation_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class ApprovalCreate(BaseModel):
    approval_level: int = Field(..., description="Approval level (1, 2, 3, etc.)")
    approval_role_required: Optional[str] = None
    approver_user_id: Optional[int] = None


class ApprovalResponse(BaseModel):
    id: UUID
    change_request_id: UUID
    approval_level: int
    approval_status: str
    approver_email: Optional[str]
    requested_at: datetime
    responded_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    approval_comment: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    component_name: str = Field(..., description="Component name to check")
    baseline_id: Optional[UUID] = None
    compliance_rules: Optional[List[dict]] = None


class ComplianceStatusResponse(BaseModel):
    id: UUID
    component_name: str
    compliance_status: str
    has_drift: bool
    drift_severity: Optional[str]
    last_checked_at: datetime
    
    class Config:
        from_attributes = True


class DriftReportResponse(BaseModel):
    has_baseline: bool
    baseline_id: Optional[UUID]
    baseline_name: Optional[str]
    baseline_version: Optional[str]
    report_generated_at: str
    components_checked: int
    components_with_drift: int
    components_with_critical_drift: int
    component_results: List[dict]


# ============================================================================
# BASELINE ENDPOINTS (CM-2)
# ============================================================================

@router.post(
    "/baselines",
    response_model=BaselineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def create_baseline(
    baseline: BaselineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new configuration baseline (CM-2).
    
    Requires admin or security_officer role.
    """
    try:
        created_baseline = ConfigurationManagementService.create_baseline(
            db=db,
            org_id=current_user.org_id,
            name=baseline.name,
            configuration_snapshot=baseline.configuration_snapshot,
            description=baseline.description,
            version=baseline.version,
            scope=baseline.scope,
            created_by_user_id=current_user.id,
            created_by_email=current_user.email,
        )
        return created_baseline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create baseline: {str(e)}",
        )


@router.post(
    "/baselines/{baseline_id}/activate",
    response_model=BaselineResponse,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def activate_baseline(
    baseline_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate a configuration baseline (CM-2).
    
    Deactivates other active baselines for the organization.
    Requires admin or security_officer role.
    """
    try:
        activated_baseline = ConfigurationManagementService.activate_baseline(
            db=db,
            baseline_id=baseline_id,
            org_id=current_user.org_id,
            activated_by_user_id=current_user.id,
        )
        return activated_baseline
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate baseline: {str(e)}",
        )


@router.get(
    "/baselines",
    response_model=List[BaselineResponse],
)
def list_baselines(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List configuration baselines for the organization (CM-2).
    """
    baselines = ConfigurationManagementService.list_baselines(
        db=db,
        org_id=current_user.org_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return baselines


@router.get(
    "/baselines/active",
    response_model=BaselineResponse,
)
def get_active_baseline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the active configuration baseline (CM-2).
    """
    baseline = ConfigurationManagementService.get_active_baseline(
        db=db,
        org_id=current_user.org_id,
    )
    
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active baseline found",
        )
    
    return baseline


# ============================================================================
# CHANGE REQUEST ENDPOINTS (CM-3)
# ============================================================================

@router.post(
    "/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_change_request(
    change_request: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a configuration change request (CM-3).
    """
    try:
        created_request = ConfigurationManagementService.create_change_request(
            db=db,
            org_id=current_user.org_id,
            title=change_request.title,
            description=change_request.description,
            configuration_changes=change_request.configuration_changes,
            change_reason=change_request.change_reason,
            priority=change_request.priority,
            baseline_id=change_request.baseline_id,
            affected_components=change_request.affected_components,
            risk_level=change_request.risk_level,
            impact_assessment=change_request.impact_assessment,
            scheduled_implementation_date=change_request.scheduled_implementation_date,
            requested_by_user_id=current_user.id,
            requested_by_email=current_user.email,
        )
        return created_request
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create change request: {str(e)}",
        )


@router.get(
    "/change-requests",
    response_model=List[ChangeRequestResponse],
)
def list_change_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List configuration change requests (CM-3).
    """
    change_requests = ConfigurationManagementService.list_change_requests(
        db=db,
        org_id=current_user.org_id,
        status=status_filter,
        priority=priority_filter,
        limit=limit,
        offset=offset,
    )
    return change_requests


@router.get(
    "/change-requests/{change_request_id}",
    response_model=ChangeRequestResponse,
)
def get_change_request(
    change_request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific configuration change request (CM-3).
    """
    change_request = db.query(ConfigurationChangeRequest).filter(
        ConfigurationChangeRequest.id == change_request_id,
        ConfigurationChangeRequest.org_id == current_user.org_id,
    ).first()
    
    if not change_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )
    
    return change_request


@router.post(
    "/change-requests/{change_request_id}/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def create_approval(
    change_request_id: UUID,
    approval: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an approval record for a change request (CM-3).
    
    Requires admin or security_officer role.
    """
    # Verify change request exists and belongs to org
    change_request = db.query(ConfigurationChangeRequest).filter(
        ConfigurationChangeRequest.id == change_request_id,
        ConfigurationChangeRequest.org_id == current_user.org_id,
    ).first()
    
    if not change_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )
    
    created_approval = ConfigurationManagementService.create_approval(
        db=db,
        change_request_id=change_request_id,
        approval_level=approval.approval_level,
        approval_role_required=approval.approval_role_required,
        approver_user_id=approval.approver_user_id or current_user.id,
        approver_email=current_user.email,
    )
    
    return created_approval


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def approve_change_request(
    approval_id: UUID,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a change request (CM-3).
    
    Requires admin or security_officer role.
    """
    try:
        approval, change_request = ConfigurationManagementService.approve_change_request(
            db=db,
            approval_id=approval_id,
            approver_user_id=current_user.id,
            approver_email=current_user.email,
            approval_comment=decision.approval_comment,
        )
        
        # Verify org ownership
        if change_request.org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )
        
        return approval
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def reject_change_request(
    approval_id: UUID,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a change request (CM-3).
    
    Requires admin or security_officer role.
    """
    try:
        approval, change_request = ConfigurationManagementService.reject_change_request(
            db=db,
            approval_id=approval_id,
            approver_user_id=current_user.id,
            approver_email=current_user.email,
            rejection_reason=decision.approval_comment,
        )
        
        # Verify org ownership
        if change_request.org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )
        
        return approval
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/change-requests/{change_request_id}/implement",
    response_model=ChangeRequestResponse,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def implement_change_request(
    change_request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a change request as implemented (CM-3).
    
    Requires admin or security_officer role.
    """
    try:
        implemented_request = ConfigurationManagementService.implement_change_request(
            db=db,
            change_request_id=change_request_id,
            org_id=current_user.org_id,
            implemented_by_user_id=current_user.id,
        )
        return implemented_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# COMPLIANCE CHECKING ENDPOINTS (CM-6)
# ============================================================================

@router.post(
    "/compliance/check",
    response_model=ComplianceStatusResponse,
)
def check_compliance(
    check_request: ComplianceCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check configuration compliance for a component (CM-6).
    """
    try:
        compliance_status = ConfigurationBaselineService.check_compliance(
            db=db,
            org_id=current_user.org_id,
            component_name=check_request.component_name,
            compliance_rules=check_request.compliance_rules,
            baseline_id=str(check_request.baseline_id) if check_request.baseline_id else None,
            checked_by_user_id=current_user.id,
        )
        return compliance_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compliance: {str(e)}",
        )


@router.get(
    "/compliance/status",
    response_model=List[ComplianceStatusResponse],
)
def list_compliance_status(
    component_name: Optional[str] = Query(None),
    compliance_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List configuration compliance status records (CM-6).
    """
    query = db.query(ConfigurationComplianceStatus).filter(
        ConfigurationComplianceStatus.org_id == current_user.org_id,
    )
    
    if component_name:
        query = query.filter(ConfigurationComplianceStatus.component_name == component_name)
    
    if compliance_status:
        query = query.filter(ConfigurationComplianceStatus.compliance_status == compliance_status)
    
    status_records = query.order_by(
        ConfigurationComplianceStatus.last_checked_at.desc(),
    ).limit(limit).offset(offset).all()
    
    return status_records


@router.get(
    "/compliance/drift-report",
    response_model=DriftReportResponse,
)
def get_drift_report(
    baseline_id: Optional[UUID] = Query(None),
    component_names: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a configuration drift report (CM-6).
    """
    try:
        report = ConfigurationBaselineService.generate_drift_report(
            db=db,
            org_id=current_user.org_id,
            baseline_id=str(baseline_id) if baseline_id else None,
            component_names=component_names,
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate drift report: {str(e)}",
        )


@router.post(
    "/capture-configuration",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.admin, UserRole.security_officer]))],
)
def capture_configuration(
    component_name: str = Query(..., description="Component name"),
    component_type: Optional[str] = Query(None, description="Component type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Capture current configuration for a component (CM-2).
    
    Requires admin or security_officer role.
    """
    try:
        config = ConfigurationBaselineService.capture_current_configuration(
            db=db,
            org_id=current_user.org_id,
            component_name=component_name,
            component_type=component_type,
        )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture configuration: {str(e)}",
        )


@router.get(
    "/compare-to-baseline",
    response_model=dict,
)
def compare_to_baseline(
    component_name: str = Query(..., description="Component name"),
    baseline_id: Optional[UUID] = Query(None, description="Baseline ID (uses active if not provided)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare current configuration to baseline (CM-6).
    """
    try:
        comparison = ConfigurationBaselineService.compare_to_baseline(
            db=db,
            org_id=current_user.org_id,
            component_name=component_name,
            baseline_id=str(baseline_id) if baseline_id else None,
        )
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare configuration: {str(e)}",
        )
