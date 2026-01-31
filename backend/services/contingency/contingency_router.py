"""
FedRAMP Contingency Planning (CP) Router

Provides API endpoints for all CP controls:
- CP-2: Contingency Plan
- CP-3: Contingency Training
- CP-4: Contingency Plan Testing
- CP-6: Alternate Storage Site
- CP-7: Alternate Processing Site
- CP-9: Information System Backup
- CP-10: Information System Recovery
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.user import User, UserRole
from services.contingency import (
    ContingencyPlanService,
    ContingencyTrainingService,
    PlanTestingService,
    AlternateStorageService,
    AlternateProcessingService,
    BackupService,
    RecoveryService,
)
from utils.write_ops import audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/contingency",
    tags=["Contingency Planning"],
    dependencies=[Depends(require_module("COMPLIANCE"))],
)


# ============================================================================
# CP-2: Contingency Plan Pydantic Models
# ============================================================================

class PlanCreate(BaseModel):
    plan_id: str
    version: str
    title: str
    plan_content: str
    description: Optional[str] = None
    plan_document_path: Optional[str] = None
    review_frequency_days: int = 365
    metadata: Optional[dict] = None


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    plan_content: Optional[str] = None
    plan_document_path: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class PlanDistributionCreate(BaseModel):
    user_email: str
    user_role: Optional[str] = None
    distribution_method: str = "email"
    user_id: Optional[int] = None
    metadata: Optional[dict] = None


# ============================================================================
# CP-2: Contingency Plan Endpoints
# ============================================================================

@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a new contingency plan"""
    service = ContingencyPlanService(db, user.org_id)
    plan = service.create_plan(
        plan_id=payload.plan_id,
        version=payload.version,
        title=payload.title,
        plan_content=payload.plan_content,
        description=payload.description,
        plan_document_path=payload.plan_document_path,
        review_frequency_days=payload.review_frequency_days,
        created_by_user_id=user.id,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="contingency_plan",
        classification="NON_PHI",
        after_state=model_snapshot(plan),
        event_type="contingency.plan.created",
        event_payload={"plan_id": plan.id},
    )
    
    return plan


@router.get("/plans")
def list_plans(
    status: Optional[str] = None,
    plan_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """List contingency plans"""
    service = ContingencyPlanService(db, user.org_id)
    return service.list_plans(status=status, plan_id=plan_id, limit=limit, offset=offset)


@router.get("/plans/{plan_id}")
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get a contingency plan by ID"""
    service = ContingencyPlanService(db, user.org_id)
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Update a contingency plan"""
    service = ContingencyPlanService(db, user.org_id)
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    before_state = model_snapshot(plan)
    plan = service.update_plan(
        plan_id=plan_id,
        title=payload.title,
        description=payload.description,
        plan_content=payload.plan_content,
        plan_document_path=payload.plan_document_path,
        status=payload.status,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="contingency_plan",
        classification="NON_PHI",
        before_state=before_state,
        after_state=model_snapshot(plan),
        event_type="contingency.plan.updated",
        event_payload={"plan_id": plan.id},
    )
    
    return plan


@router.post("/plans/{plan_id}/approve")
def approve_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve a contingency plan"""
    service = ContingencyPlanService(db, user.org_id)
    plan = service.approve_plan(plan_id, user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="approve",
        resource="contingency_plan",
        classification="NON_PHI",
        after_state=model_snapshot(plan),
        event_type="contingency.plan.approved",
        event_payload={"plan_id": plan.id},
    )
    
    return plan


@router.post("/plans/{plan_id}/review")
def review_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Review a contingency plan"""
    service = ContingencyPlanService(db, user.org_id)
    plan = service.review_plan(plan_id, user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="review",
        resource="contingency_plan",
        classification="NON_PHI",
        after_state=model_snapshot(plan),
        event_type="contingency.plan.reviewed",
        event_payload={"plan_id": plan.id},
    )
    
    return plan


@router.get("/plans/{plan_id}/distributions")
def list_plan_distributions(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """List distributions for a plan"""
    service = ContingencyPlanService(db, user.org_id)
    return service.get_distributions(plan_id=plan_id)


@router.post("/plans/{plan_id}/distribute")
def distribute_plan(
    plan_id: int,
    payload: PlanDistributionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Distribute a contingency plan"""
    service = ContingencyPlanService(db, user.org_id)
    distribution = service.distribute_plan(
        plan_id=plan_id,
        user_email=payload.user_email,
        user_role=payload.user_role,
        distribution_method=payload.distribution_method,
        user_id=payload.user_id,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="distribute",
        resource="plan_distribution",
        classification="NON_PHI",
        after_state=model_snapshot(distribution),
        event_type="contingency.plan.distributed",
        event_payload={"distribution_id": distribution.id},
    )
    
    return distribution


@router.post("/distributions/{distribution_id}/acknowledge")
def acknowledge_distribution(
    distribution_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Acknowledge receipt of a distributed plan"""
    service = ContingencyPlanService(db, user.org_id)
    distribution = service.acknowledge_distribution(
        distribution_id=distribution_id,
        ip_address=request.client.host if request.client else None,
    )
    if not distribution:
        raise HTTPException(status_code=404, detail="Distribution not found")
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="acknowledge",
        resource="plan_distribution",
        classification="NON_PHI",
        after_state=model_snapshot(distribution),
        event_type="contingency.plan.acknowledged",
        event_payload={"distribution_id": distribution.id},
    )
    
    return distribution


@router.get("/plans/due-for-review")
def get_plans_due_for_review(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get plans due for review"""
    service = ContingencyPlanService(db, user.org_id)
    return service.get_plans_due_for_review(days_ahead=days_ahead)


# ============================================================================
# CP-3: Contingency Training Endpoints
# ============================================================================

class TrainingCreate(BaseModel):
    training_name: str
    training_type: str
    scheduled_date: datetime
    user_email: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    training_content_path: Optional[str] = None
    training_materials: Optional[dict] = None
    metadata: Optional[dict] = None


class TrainingUpdate(BaseModel):
    status: Optional[str] = None
    completion_percentage: Optional[float] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    completed_date: Optional[datetime] = None
    metadata: Optional[dict] = None


class DrillCreate(BaseModel):
    drill_name: str
    drill_type: str
    scheduled_date: datetime
    scenario_description: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/trainings", status_code=status.HTTP_201_CREATED)
def create_training(
    payload: TrainingCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a contingency training record"""
    service = ContingencyTrainingService(db, user.org_id)
    training = service.create_training(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="contingency_training",
        classification="NON_PHI",
        after_state=model_snapshot(training),
        event_type="contingency.training.created",
        event_payload={"training_id": training.id},
    )
    
    return training


@router.get("/trainings")
def list_trainings(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    training_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """List contingency trainings"""
    service = ContingencyTrainingService(db, user.org_id)
    return service.list_trainings(
        user_id=user_id,
        status=status,
        training_type=training_type,
        limit=limit,
        offset=offset,
    )


@router.post("/trainings/{training_id}/complete")
def complete_training(
    training_id: int,
    completion_percentage: float = 100.0,
    score: Optional[float] = None,
    passed: Optional[bool] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Complete a training"""
    service = ContingencyTrainingService(db, user.org_id)
    training = service.complete_training(
        training_id=training_id,
        completion_percentage=completion_percentage,
        score=score,
        passed=passed,
    )
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="complete",
            resource="contingency_training",
            classification="NON_PHI",
            after_state=model_snapshot(training),
            event_type="contingency.training.completed",
            event_payload={"training_id": training.id},
        )
    
    return training


@router.post("/drills", status_code=status.HTTP_201_CREATED)
def create_drill(
    payload: DrillCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a contingency drill"""
    service = ContingencyTrainingService(db, user.org_id)
    drill = service.create_drill(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="contingency_drill",
        classification="NON_PHI",
        after_state=model_snapshot(drill),
        event_type="contingency.drill.created",
        event_payload={"drill_id": drill.id},
    )
    
    return drill


@router.post("/drills/{drill_id}/complete")
def complete_drill(
    drill_id: int,
    drill_results: Optional[str] = None,
    lessons_learned: Optional[str] = None,
    action_items: Optional[List[dict]] = None,
    participants_count: Optional[int] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Complete a drill"""
    service = ContingencyTrainingService(db, user.org_id)
    drill = service.complete_drill(
        drill_id=drill_id,
        drill_results=drill_results,
        lessons_learned=lessons_learned,
        action_items=action_items,
        participants_count=participants_count,
    )
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="complete",
            resource="contingency_drill",
            classification="NON_PHI",
            after_state=model_snapshot(drill),
            event_type="contingency.drill.completed",
            event_payload={"drill_id": drill.id},
        )
    
    return drill


# ============================================================================
# CP-4: Contingency Plan Testing Endpoints
# ============================================================================

class PlanTestCreate(BaseModel):
    plan_id: int
    test_name: str
    test_type: str
    scheduled_date: datetime
    test_description: Optional[str] = None
    test_procedures: Optional[str] = None
    test_team: Optional[List[int]] = None
    metadata: Optional[dict] = None


@router.post("/plan-tests", status_code=status.HTTP_201_CREATED)
def create_plan_test(
    payload: PlanTestCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a contingency plan test"""
    service = PlanTestingService(db, user.org_id)
    test = service.create_test(
        plan_id=payload.plan_id,
        test_name=payload.test_name,
        test_type=payload.test_type,
        scheduled_date=payload.scheduled_date,
        test_description=payload.test_description,
        test_procedures=payload.test_procedures,
        test_team=payload.test_team,
        conducted_by_user_id=user.id,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="contingency_plan_test",
        classification="NON_PHI",
        after_state=model_snapshot(test),
        event_type="contingency.plan_test.created",
        event_payload={"test_id": test.id},
    )
    
    return test


@router.post("/plan-tests/{test_id}/complete")
def complete_plan_test(
    test_id: int,
    test_result: str,
    test_results: Optional[str] = None,
    test_report_path: Optional[str] = None,
    issues_identified: Optional[List[dict]] = None,
    remediation_plan: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Complete a plan test"""
    service = PlanTestingService(db, user.org_id)
    test = service.complete_test(
        test_id=test_id,
        test_result=test_result,
        test_results=test_results,
        test_report_path=test_report_path,
        issues_identified=issues_identified,
        remediation_plan=remediation_plan,
    )
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="complete",
            resource="contingency_plan_test",
            classification="NON_PHI",
            after_state=model_snapshot(test),
            event_type="contingency.plan_test.completed",
            event_payload={"test_id": test.id},
        )
    
    return test


# ============================================================================
# CP-6: Alternate Storage Site Endpoints
# ============================================================================

class StorageSiteCreate(BaseModel):
    site_name: str
    site_type: str
    is_primary: bool = False
    site_location: Optional[str] = None
    storage_capacity_gb: Optional[float] = None
    connection_endpoint: Optional[str] = None
    connection_config: Optional[dict] = None
    failover_capable: bool = True
    failover_rto_minutes: Optional[int] = None
    failover_rpo_minutes: Optional[int] = None
    metadata: Optional[dict] = None


@router.post("/storage-sites", status_code=status.HTTP_201_CREATED)
def create_storage_site(
    payload: StorageSiteCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create an alternate storage site"""
    service = AlternateStorageService(db, user.org_id)
    site = service.create_storage_site(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="alternate_storage_site",
        classification="NON_PHI",
        after_state=model_snapshot(site),
        event_type="contingency.storage_site.created",
        event_payload={"site_id": site.id},
    )
    
    return site


@router.get("/storage-sites")
def list_storage_sites(
    status: Optional[str] = None,
    is_primary: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """List storage sites"""
    service = AlternateStorageService(db, user.org_id)
    return service.list_storage_sites(status=status, is_primary=is_primary)


@router.post("/storage-sites/{site_id}/replication-log")
def log_replication_event(
    site_id: int,
    replication_status: str,
    event_type: str,
    replication_lag_seconds: Optional[int] = None,
    data_transferred_gb: Optional[float] = None,
    event_message: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Log a replication event"""
    service = AlternateStorageService(db, user.org_id)
    log_entry = service.log_replication_event(
        storage_site_id=site_id,
        replication_status=replication_status,
        event_type=event_type,
        replication_lag_seconds=replication_lag_seconds,
        data_transferred_gb=data_transferred_gb,
        event_message=event_message,
    )
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="log_replication",
            resource="storage_replication_log",
            classification="NON_PHI",
            after_state=model_snapshot(log_entry),
            event_type="contingency.replication.logged",
            event_payload={"log_id": log_entry.id},
        )
    
    return log_entry


# ============================================================================
# CP-7: Alternate Processing Site Endpoints
# ============================================================================

class ProcessingSiteCreate(BaseModel):
    site_name: str
    site_type: str
    is_primary: bool = False
    site_location: Optional[str] = None
    compute_capacity_cpu_cores: Optional[int] = None
    compute_capacity_ram_gb: Optional[int] = None
    connection_endpoint: Optional[str] = None
    connection_config: Optional[dict] = None
    activation_capable: bool = True
    activation_rto_minutes: Optional[int] = None
    activation_procedures: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/processing-sites", status_code=status.HTTP_201_CREATED)
def create_processing_site(
    payload: ProcessingSiteCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create an alternate processing site"""
    service = AlternateProcessingService(db, user.org_id)
    site = service.create_processing_site(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="alternate_processing_site",
        classification="NON_PHI",
        after_state=model_snapshot(site),
        event_type="contingency.processing_site.created",
        event_payload={"site_id": site.id},
    )
    
    return site


@router.post("/processing-sites/{site_id}/activate")
def initiate_activation(
    site_id: int,
    activation_type: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Initiate activation of an alternate processing site"""
    service = AlternateProcessingService(db, user.org_id)
    activation_log = service.initiate_activation(
        site_id=site_id,
        activation_type=activation_type,
        initiated_by_user_id=user.id,
    )
    if not activation_log:
        raise HTTPException(status_code=404, detail="Site not found or not activation capable")
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="initiate_activation",
        resource="processing_site_activation",
        classification="NON_PHI",
        after_state=model_snapshot(activation_log),
        event_type="contingency.processing_site.activation_initiated",
        event_payload={"activation_id": activation_log.id},
    )
    
    return activation_log


# ============================================================================
# CP-9: Information System Backup Endpoints
# ============================================================================

class BackupCreate(BaseModel):
    backup_name: str
    backup_type: str
    system_component: str
    scheduled_time: datetime
    backup_location: str
    retention_days: int = 90
    backup_format: Optional[str] = None
    metadata: Optional[dict] = None


class BackupScheduleCreate(BaseModel):
    schedule_name: str
    system_component: str
    backup_type: str
    schedule_frequency: str
    retention_days: int = 90
    schedule_cron: Optional[str] = None
    schedule_time: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/backups", status_code=status.HTTP_201_CREATED)
def create_backup(
    payload: BackupCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a backup record"""
    service = BackupService(db, user.org_id)
    backup = service.create_backup(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="system_backup",
        classification="NON_PHI",
        after_state=model_snapshot(backup),
        event_type="contingency.backup.created",
        event_payload={"backup_id": backup.id},
    )
    
    return backup


@router.post("/backups/{backup_id}/verify")
def verify_backup(
    backup_id: int,
    verification_method: str,
    verification_result: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Verify a backup"""
    service = BackupService(db, user.org_id)
    backup = service.verify_backup(
        backup_id=backup_id,
        verification_method=verification_method,
        verification_result=verification_result,
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="verify",
            resource="system_backup",
            classification="NON_PHI",
            after_state=model_snapshot(backup),
            event_type="contingency.backup.verified",
            event_payload={"backup_id": backup.id},
        )
    
    return backup


@router.post("/backup-schedules", status_code=status.HTTP_201_CREATED)
def create_backup_schedule(
    payload: BackupScheduleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a backup schedule"""
    service = BackupService(db, user.org_id)
    schedule = service.create_backup_schedule(**payload.model_dump())
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="backup_schedule",
        classification="NON_PHI",
        after_state=model_snapshot(schedule),
        event_type="contingency.backup_schedule.created",
        event_payload={"schedule_id": schedule.id},
    )
    
    return schedule


# ============================================================================
# CP-10: Information System Recovery Endpoints
# ============================================================================

class RecoveryCreate(BaseModel):
    recovery_name: str
    recovery_type: str
    system_component: str
    recovery_source: str
    incident_description: Optional[str] = None
    incident_type: Optional[str] = None
    backup_id: Optional[int] = None
    target_rpo_minutes: Optional[int] = None
    target_rto_minutes: Optional[int] = None
    recovery_procedures: Optional[str] = None
    metadata: Optional[dict] = None


class RecoveryTestCreate(BaseModel):
    test_name: str
    test_type: str
    system_component: str
    scheduled_date: datetime
    target_rpo_minutes: Optional[int] = None
    target_rto_minutes: Optional[int] = None
    test_procedures: Optional[str] = None
    test_team: Optional[List[int]] = None
    metadata: Optional[dict] = None


@router.post("/recoveries", status_code=status.HTTP_201_CREATED)
def create_recovery(
    payload: RecoveryCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a recovery record"""
    service = RecoveryService(db, user.org_id)
    recovery = service.create_recovery(
        recovery_name=payload.recovery_name,
        recovery_type=payload.recovery_type,
        system_component=payload.system_component,
        recovery_source=payload.recovery_source,
        incident_description=payload.incident_description,
        incident_type=payload.incident_type,
        backup_id=payload.backup_id,
        target_rpo_minutes=payload.target_rpo_minutes,
        target_rto_minutes=payload.target_rto_minutes,
        recovery_procedures=payload.recovery_procedures,
        initiated_by_user_id=user.id,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="system_recovery",
        classification="NON_PHI",
        after_state=model_snapshot(recovery),
        event_type="contingency.recovery.created",
        event_payload={"recovery_id": recovery.id},
    )
    
    return recovery


@router.post("/recoveries/{recovery_id}/complete")
def complete_recovery(
    recovery_id: int,
    recovery_result: Optional[str] = None,
    recovery_steps: Optional[List[dict]] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Complete a recovery"""
    service = RecoveryService(db, user.org_id)
    recovery = service.complete_recovery(
        recovery_id=recovery_id,
        recovery_result=recovery_result,
        recovery_steps=recovery_steps,
    )
    if not recovery:
        raise HTTPException(status_code=404, detail="Recovery not found")
    
    if request:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="complete",
            resource="system_recovery",
            classification="NON_PHI",
            after_state=model_snapshot(recovery),
            event_type="contingency.recovery.completed",
            event_payload={"recovery_id": recovery.id},
        )
    
    return recovery


@router.post("/recovery-tests", status_code=status.HTTP_201_CREATED)
def create_recovery_test(
    payload: RecoveryTestCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a recovery test"""
    service = RecoveryService(db, user.org_id)
    test = service.create_recovery_test(
        test_name=payload.test_name,
        test_type=payload.test_type,
        system_component=payload.system_component,
        scheduled_date=payload.scheduled_date,
        target_rpo_minutes=payload.target_rpo_minutes,
        target_rto_minutes=payload.target_rto_minutes,
        test_procedures=payload.test_procedures,
        test_team=payload.test_team,
        conducted_by_user_id=user.id,
        metadata=payload.metadata,
    )
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="recovery_test",
        classification="NON_PHI",
        after_state=model_snapshot(test),
        event_type="contingency.recovery_test.created",
        event_payload={"test_id": test.id},
    )
    
    return test
