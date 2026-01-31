"""
Incident Response Router for FedRAMP IR-2, IR-3, IR-4, IR-5, IR-6, IR-7, IR-8, IR-9 Compliance

REST API endpoints for comprehensive incident response management:
- IR-2: Incident Response Training
- IR-3: Incident Response Testing
- IR-4: Incident Handling (with IR-4(1) automation)
- IR-5: Incident Monitoring (with IR-5(1) automation)
- IR-6: Incident Reporting
- IR-7: Incident Response Assistance
- IR-8: Incident Response Plan
- IR-9: Information Spillage Response
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles, get_current_user
from models.incident import (
    SecurityIncident,
    IncidentSeverity,
    IncidentStatus,
    IncidentCategory,
)
from models.user import User, UserRole
from .incident_service import IncidentService
from .incident_detection import IncidentDetectionService
from .incident_training_service import IncidentTrainingService
from .incident_testing_service import IncidentTestingService
from .incident_assistance_service import IncidentAssistanceService
from .incident_response_plan_service import IncidentResponsePlanService
from .information_spillage_service import InformationSpillageService

router = APIRouter(
    prefix="/api/incidents",
    tags=["Incident Response"],
)


# ============================================================================
# Pydantic Models
# ============================================================================


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    severity: IncidentSeverity
    category: IncidentCategory
    affected_systems: Optional[List[str]] = Field(default_factory=list)
    affected_users: Optional[List[int]] = Field(default_factory=list)
    affected_resources: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    classification: Optional[str] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[IncidentSeverity] = None
    category: Optional[IncidentCategory] = None
    affected_systems: Optional[List[str]] = None
    affected_users: Optional[List[int]] = None
    affected_resources: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class StatusUpdate(BaseModel):
    status: IncidentStatus
    comment: Optional[str] = None


class ClassificationUpdate(BaseModel):
    severity: IncidentSeverity
    reason: Optional[str] = None


class AssignmentUpdate(BaseModel):
    assigned_to_user_id: int


class InvestigationUpdate(BaseModel):
    root_cause: Optional[str] = None
    impact_assessment: Optional[str] = None
    containment_actions: Optional[str] = None
    remediation_actions: Optional[str] = None
    lessons_learned: Optional[str] = None


class ActivityCreate(BaseModel):
    activity_type: str
    description: str
    details: Optional[dict] = None


class USCertReport(BaseModel):
    report_id: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    incident_number: str
    title: str
    description: str
    severity: str
    category: str
    status: str
    detected_at: str
    created_at: str
    updated_at: Optional[str]
    contained_at: Optional[str]
    resolved_at: Optional[str]
    closed_at: Optional[str]
    detected_by_user_id: Optional[int]
    detected_by_system: bool
    detection_method: Optional[str]
    assigned_to_user_id: Optional[int]
    assigned_at: Optional[str]
    affected_systems: Optional[List[str]]
    affected_users: Optional[List[int]]
    affected_resources: Optional[List[str]]
    root_cause: Optional[str]
    impact_assessment: Optional[str]
    containment_actions: Optional[str]
    remediation_actions: Optional[str]
    lessons_learned: Optional[str]
    us_cert_reported: bool
    us_cert_reported_at: Optional[str]
    us_cert_report_id: Optional[str]
    tags: Optional[List[str]]
    classification: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new security incident"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.create_incident(
        db=db,
        org_id=current_user.org_id,
        title=incident_data.title,
        description=incident_data.description,
        severity=incident_data.severity,
        category=incident_data.category,
        detected_by_user_id=current_user.id,
        detected_by_system=False,
        detection_method="manual",
        affected_systems=incident_data.affected_systems,
        affected_users=incident_data.affected_users,
        affected_resources=incident_data.affected_resources,
        tags=incident_data.tags,
        classification=incident_data.classification,
        training_mode=False,
        request=request,
    )
    
    return IncidentResponse.from_orm(incident)


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    severity: Optional[IncidentSeverity] = Query(None),
    category: Optional[IncidentCategory] = Query(None),
    assigned_to_user_id: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security incidents with optional filters"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incidents = IncidentService.list_incidents(
        db=db,
        org_id=current_user.org_id,
        status=status_filter,
        severity=severity,
        category=category,
        assigned_to_user_id=assigned_to_user_id,
        limit=limit,
        offset=offset,
    )
    
    return [IncidentResponse.from_orm(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get incident by ID"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.get_incident(
        db=db,
        incident_id=incident_id,
        org_id=current_user.org_id,
    )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    return IncidentResponse.from_orm(incident)


@router.put("/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: UUID,
    status_update: StatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update incident status"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.update_incident_status(
        db=db,
        incident_id=incident_id,
        new_status=status_update.status,
        user_id=current_user.id,
        comment=status_update.comment,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.put("/{incident_id}/classification", response_model=IncidentResponse)
async def classify_incident(
    incident_id: UUID,
    classification: ClassificationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update incident severity classification"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.classify_incident(
        db=db,
        incident_id=incident_id,
        severity=classification.severity,
        user_id=current_user.id,
        reason=classification.reason,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.put("/{incident_id}/assignment", response_model=IncidentResponse)
async def assign_incident(
    incident_id: UUID,
    assignment: AssignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign incident to a responder"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    # Verify assigned user exists and is in same org
    assigned_user = db.query(User).filter(User.id == assignment.assigned_to_user_id).first()
    if not assigned_user or assigned_user.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid assigned user",
        )
    
    incident = IncidentService.assign_incident(
        db=db,
        incident_id=incident_id,
        assigned_to_user_id=assignment.assigned_to_user_id,
        assigned_by_user_id=current_user.id,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.put("/{incident_id}/investigation", response_model=IncidentResponse)
async def update_investigation(
    incident_id: UUID,
    investigation: InvestigationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update investigation details"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.update_investigation_details(
        db=db,
        incident_id=incident_id,
        user_id=current_user.id,
        root_cause=investigation.root_cause,
        impact_assessment=investigation.impact_assessment,
        containment_actions=investigation.containment_actions,
        remediation_actions=investigation.remediation_actions,
        lessons_learned=investigation.lessons_learned,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.post("/{incident_id}/activities", status_code=status.HTTP_201_CREATED)
async def add_activity(
    incident_id: UUID,
    activity: ActivityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add activity log entry to incident"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    # Verify incident exists and belongs to org
    incident = IncidentService.get_incident(
        db=db,
        incident_id=incident_id,
        org_id=current_user.org_id,
    )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    activity_entry = IncidentService.add_activity(
        db=db,
        incident_id=incident_id,
        activity_type=activity.activity_type,
        description=activity.description,
        user_id=current_user.id,
        details=activity.details,
        request=request,
    )
    
    return {
        "id": str(activity_entry.id),
        "timestamp": activity_entry.timestamp.isoformat(),
        "activity_type": activity_entry.activity_type,
        "description": activity_entry.description,
    }


@router.post("/{incident_id}/us-cert-report", response_model=IncidentResponse)
async def report_to_us_cert(
    incident_id: UUID,
    report: USCertReport,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark incident as reported to US-CERT (IR-6 requirement)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.report_to_us_cert(
        db=db,
        incident_id=incident_id,
        user_id=current_user.id,
        report_id=report.report_id,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.get("/{incident_id}/report")
async def generate_incident_report(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate comprehensive incident report for compliance"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    # Verify incident exists and belongs to org
    incident = IncidentService.get_incident(
        db=db,
        incident_id=incident_id,
        org_id=current_user.org_id,
    )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    report = IncidentService.generate_incident_report(
        db=db,
        incident_id=incident_id,
    )
    
    return report


@router.post("/detection/scan", status_code=status.HTTP_202_ACCEPTED)
async def run_detection_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run automated incident detection scan (IR-5 requirement)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    created_incidents = IncidentDetectionService.run_detection_scan(
        db=db,
        org_id=current_user.org_id,
        auto_create=True,
    )
    
    return {
        "status": "completed",
        "incidents_created": len(created_incidents),
        "incident_numbers": [inc.incident_number for inc in created_incidents],
    }


# ============================================================================
# IR-4(1) & IR-5(1): Automated Incident Handling & Tracking
# ============================================================================


@router.post("/{incident_id}/automation/enable", response_model=IncidentResponse)
async def enable_automated_handling(
    incident_id: UUID,
    automation_workflow_id: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable automated incident handling (IR-4(1))"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.enable_automated_handling(
        db=db,
        incident_id=incident_id,
        automation_workflow_id=automation_workflow_id,
        user_id=current_user.id,
        request=request,
    )
    
    if incident.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return IncidentResponse.from_orm(incident)


@router.get("/{incident_id}/automation/summary")
async def get_automated_summary(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get automated handling and tracking summary (IR-4(1), IR-5(1))"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    incident = IncidentService.get_incident(
        db=db,
        incident_id=incident_id,
        org_id=current_user.org_id,
    )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    return IncidentService.get_automated_summary(db=db, incident_id=incident_id)


# ============================================================================
# IR-2: Incident Response Training Endpoints
# ============================================================================


@router.post("/training/curricula", status_code=status.HTTP_201_CREATED)
async def create_training_curriculum(
    name: str,
    target_role: str,
    modules: List[dict],
    duration_hours: int = 0,
    required_score_percent: int = 80,
    valid_for_days: int = 365,
    renewal_required: bool = True,
    description: Optional[str] = None,
    version: str = "1.0",
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a training curriculum (IR-2)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    from models.incident import TrainingRole
    
    curriculum = IncidentTrainingService.create_curriculum(
        db=db,
        org_id=current_user.org_id,
        name=name,
        target_role=TrainingRole(target_role),
        modules=modules,
        duration_hours=duration_hours,
        required_score_percent=required_score_percent,
        valid_for_days=valid_for_days,
        renewal_required=renewal_required,
        description=description,
        version=version,
        created_by_user_id=current_user.id,
        request=request,
    )
    
    return {
        "id": str(curriculum.id),
        "name": curriculum.name,
        "target_role": curriculum.target_role,
        "version": curriculum.version,
    }


@router.post("/training/assign", status_code=status.HTTP_201_CREATED)
async def assign_training(
    user_id: int,
    curriculum_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign training to a user (IR-2)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    record = IncidentTrainingService.assign_training(
        db=db,
        org_id=current_user.org_id,
        user_id=user_id,
        curriculum_id=curriculum_id,
        request=request,
    )
    
    return {
        "id": str(record.id),
        "user_id": record.user_id,
        "curriculum_id": str(record.curriculum_id),
        "status": record.status,
    }


@router.get("/training/status/{user_id}")
async def get_training_status(
    user_id: int,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training status for a user (IR-2)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    from models.incident import TrainingRole
    
    status_list = IncidentTrainingService.get_user_training_status(
        db=db,
        org_id=current_user.org_id,
        user_id=user_id,
        role=TrainingRole(role) if role else None,
    )
    
    return status_list


@router.get("/training/compliance")
async def get_training_compliance(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training compliance report (IR-2)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    from models.incident import TrainingRole
    
    report = IncidentTrainingService.get_training_compliance_report(
        db=db,
        org_id=current_user.org_id,
        role=TrainingRole(role) if role else None,
    )
    
    return report


# ============================================================================
# IR-3: Incident Response Testing Endpoints
# ============================================================================


@router.post("/testing/scenarios", status_code=status.HTTP_201_CREATED)
async def create_test_scenario(
    name: str,
    description: str,
    scenario_type: str,
    objectives: List[str],
    procedures_to_test: List[str],
    expected_outcomes: Optional[str] = None,
    scheduled_date: Optional[datetime] = None,
    assigned_user_ids: Optional[List[int]] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a test scenario (IR-3)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    scenario = IncidentTestingService.create_test_scenario(
        db=db,
        org_id=current_user.org_id,
        name=name,
        description=description,
        scenario_type=scenario_type,
        objectives=objectives,
        procedures_to_test=procedures_to_test,
        expected_outcomes=expected_outcomes,
        scheduled_date=scheduled_date,
        assigned_user_ids=assigned_user_ids,
        created_by_user_id=current_user.id,
        request=request,
    )
    
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "scenario_type": scenario.scenario_type,
        "status": scenario.status,
    }


@router.post("/testing/executions", status_code=status.HTTP_201_CREATED)
async def start_test_execution(
    scenario_id: UUID,
    participants: Optional[List[int]] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a test execution (IR-3)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    execution = IncidentTestingService.start_test_execution(
        db=db,
        scenario_id=scenario_id,
        executed_by_user_id=current_user.id,
        participants=participants,
        request=request,
    )
    
    return {
        "id": str(execution.id),
        "scenario_id": str(scenario_id),
        "execution_date": execution.execution_date.isoformat(),
        "status": execution.status,
    }


@router.get("/testing/executions/{execution_id}/analysis")
async def analyze_test_results(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze test execution results (IR-3)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    analysis = IncidentTestingService.analyze_test_results(
        db=db,
        execution_id=execution_id,
    )
    
    return analysis


# ============================================================================
# IR-7: Incident Response Assistance Endpoints
# ============================================================================


@router.post("/assistance/requests", status_code=status.HTTP_201_CREATED)
async def create_assistance_request(
    request_type: str,
    description: str,
    priority: str = "normal",
    incident_id: Optional[UUID] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an assistance request (IR-7)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    assistance_request = IncidentAssistanceService.create_assistance_request(
        db=db,
        org_id=current_user.org_id,
        requested_by_user_id=current_user.id,
        request_type=request_type,
        description=description,
        priority=priority,
        incident_id=incident_id,
        request=request,
    )
    
    return {
        "id": str(assistance_request.id),
        "request_type": assistance_request.request_type,
        "status": assistance_request.status,
        "priority": assistance_request.priority,
    }


@router.get("/assistance/experts")
async def find_experts(
    expertise_area: Optional[str] = None,
    available_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find experts by expertise area (IR-7)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    experts = IncidentAssistanceService.find_experts(
        db=db,
        org_id=current_user.org_id,
        expertise_area=expertise_area,
        available_only=available_only,
    )
    
    return [
        {
            "id": str(expert.id),
            "name": expert.name,
            "email": expert.email,
            "expertise_areas": expert.expertise_areas,
            "is_available": expert.is_available,
        }
        for expert in experts
    ]


# ============================================================================
# IR-8: Incident Response Plan Endpoints
# ============================================================================


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_incident_response_plan(
    name: str,
    plan_content: str,
    version: str = "1.0",
    description: Optional[str] = None,
    review_frequency_days: int = 365,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an incident response plan (IR-8)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    plan = IncidentResponsePlanService.create_plan(
        db=db,
        org_id=current_user.org_id,
        name=name,
        plan_content=plan_content,
        version=version,
        description=description,
        review_frequency_days=review_frequency_days,
        created_by_user_id=current_user.id,
        request=request,
    )
    
    return {
        "id": str(plan.id),
        "name": plan.name,
        "version": plan.version,
        "status": plan.status,
    }


@router.post("/plans/{plan_id}/distribute")
async def distribute_plan(
    plan_id: UUID,
    user_ids: List[int],
    distribution_method: str = "portal",
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Distribute plan to users (IR-8)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    distributions = IncidentResponsePlanService.distribute_plan(
        db=db,
        plan_id=plan_id,
        user_ids=user_ids,
        distribution_method=distribution_method,
        distributed_by_user_id=current_user.id,
        request=request,
    )
    
    return {
        "plan_id": str(plan_id),
        "distributed_count": len(distributions),
        "distributions": [
            {
                "id": str(d.id),
                "user_id": d.user_id,
                "distributed_at": d.distributed_at.isoformat(),
            }
            for d in distributions
        ],
    }


@router.get("/plans/due-for-review")
async def get_plans_due_for_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get plans due for review (IR-8)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    plans = IncidentResponsePlanService.get_plans_due_for_review(
        db=db,
        org_id=current_user.org_id,
    )
    
    return [
        {
            "id": str(plan.id),
            "name": plan.name,
            "version": plan.version,
            "next_review_date": plan.next_review_date.isoformat() if plan.next_review_date else None,
        }
        for plan in plans
    ]


# ============================================================================
# IR-9: Information Spillage Response Endpoints
# ============================================================================


@router.post("/spillage", status_code=status.HTTP_201_CREATED)
async def create_spillage(
    title: str,
    description: str,
    classification: str,
    sensitivity_level: str = "moderate",
    data_type: Optional[str] = None,
    affected_systems: Optional[List[str]] = None,
    affected_data_elements: Optional[List[str]] = None,
    estimated_records_affected: Optional[int] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an information spillage incident (IR-9)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    spillage = InformationSpillageService.create_spillage(
        db=db,
        org_id=current_user.org_id,
        title=title,
        description=description,
        classification=classification,
        sensitivity_level=sensitivity_level,
        data_type=data_type,
        affected_systems=affected_systems,
        affected_data_elements=affected_data_elements,
        estimated_records_affected=estimated_records_affected,
        detected_by_user_id=current_user.id,
        detected_by_system=False,
        detection_method="manual",
        request=request,
    )
    
    return {
        "id": str(spillage.id),
        "spillage_number": spillage.spillage_number,
        "title": spillage.title,
        "classification": spillage.classification,
        "status": spillage.status,
    }


@router.post("/spillage/{spillage_id}/contain")
async def contain_spillage(
    spillage_id: UUID,
    containment_procedures: str,
    containment_actions_taken: List[str],
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Contain an information spillage (IR-9)"""
    require_roles([UserRole.admin, UserRole.compliance, UserRole.founder])
    
    spillage = InformationSpillageService.contain_spillage(
        db=db,
        spillage_id=spillage_id,
        contained_by_user_id=current_user.id,
        containment_procedures=containment_procedures,
        containment_actions_taken=containment_actions_taken,
        request=request,
    )
    
    return {
        "id": str(spillage.id),
        "status": spillage.status,
        "contained_at": spillage.contained_at.isoformat() if spillage.contained_at else None,
    }


@router.post("/spillage/{spillage_id}/verify-cleanup")
async def verify_spillage_cleanup(
    spillage_id: UUID,
    verification_method: str,
    verification_results: str,
    verification_passed: bool,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify spillage cleanup completion (IR-9)"""
    require_roles([UserRole.admin, UserRole.compliance])
    
    spillage = InformationSpillageService.verify_cleanup(
        db=db,
        spillage_id=spillage_id,
        verified_by_user_id=current_user.id,
        verification_method=verification_method,
        verification_results=verification_results,
        verification_passed=verification_passed,
        request=request,
    )
    
    return {
        "id": str(spillage.id),
        "status": spillage.status,
        "verification_passed": spillage.verification_passed,
        "verified_at": spillage.verified_at.isoformat() if spillage.verified_at else None,
    }
