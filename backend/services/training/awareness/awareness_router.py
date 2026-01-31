"""
Awareness & Training (AT) API Router
FedRAMP AT Controls Implementation

Provides REST API endpoints for:
- AT-2: Security Awareness Training
- AT-3: Role-Based Security Training
- AT-4: Security Training Records
- AT-5: Contacts with Security Groups
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_roles
from models.user import User, UserRole
from models.awareness_training import (
    TrainingStatus,
    TrainingDeliveryMethod,
    CompetencyLevel,
    ContactType,
)

from ..awareness.awareness_training_service import AwarenessTrainingService
from ..role_based_training_service import RoleBasedTrainingService
from ..training_records_service import TrainingRecordsService
from ..security_contacts_service import SecurityContactsService


router = APIRouter(
    prefix="/api/training/security",
    tags=["Awareness & Training (FedRAMP AT)"],
)


# ============================================================================
# AT-2: Security Awareness Training Endpoints
# ============================================================================

class AwarenessTrainingModuleCreate(BaseModel):
    module_code: str
    module_name: str
    module_description: Optional[str] = None
    module_category: str = "general"
    delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE
    duration_minutes: int = 60
    training_content_path: Optional[str] = None
    mandatory: bool = True
    required_frequency_months: int = 12
    passing_score_percentage: float = 80.0
    reminder_days_before_due: Optional[List[int]] = None


@router.post("/awareness/module", status_code=status.HTTP_201_CREATED)
def create_awareness_training_module(
    module: AwarenessTrainingModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Create a security awareness training module (AT-2)"""
    service = AwarenessTrainingService(db)
    return service.create_training_module(
        org_id=current_user.org_id,
        module_code=module.module_code,
        module_name=module.module_name,
        module_description=module.module_description,
        module_category=module.module_category,
        delivery_method=module.delivery_method,
        duration_minutes=module.duration_minutes,
        training_content_path=module.training_content_path,
        mandatory=module.mandatory,
        required_frequency_months=module.required_frequency_months,
        passing_score_percentage=module.passing_score_percentage,
        reminder_days_before_due=module.reminder_days_before_due,
        created_by_user_id=current_user.id,
    )


@router.post("/awareness/assign", status_code=status.HTTP_201_CREATED)
def assign_awareness_training(
    user_id: int,
    training_id: int,
    due_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Assign security awareness training to a user (AT-2)"""
    service = AwarenessTrainingService(db)
    return service.assign_training(
        org_id=current_user.org_id,
        user_id=user_id,
        training_id=training_id,
        due_date=due_date,
        assigned_by_user_id=current_user.id,
    )


@router.post("/awareness/{assignment_id}/complete")
def complete_awareness_training(
    assignment_id: int,
    score_percentage: float,
    passed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete security awareness training (AT-2)"""
    service = AwarenessTrainingService(db)
    return service.complete_training(
        assignment_id=assignment_id,
        org_id=current_user.org_id,
        score_percentage=score_percentage,
        passed=passed,
    )


@router.get("/awareness/modules")
def list_awareness_training_modules(
    mandatory: Optional[bool] = Query(None),
    active: Optional[bool] = Query(True),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security awareness training modules (AT-2)"""
    service = AwarenessTrainingService(db)
    return service.list_training_modules(
        org_id=current_user.org_id,
        mandatory=mandatory,
        active=active,
        limit=limit,
        offset=offset,
    )


@router.get("/awareness/assignments")
def get_user_awareness_assignments(
    user_id: Optional[int] = Query(None),
    status: Optional[TrainingStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security awareness training assignments (AT-2)"""
    service = AwarenessTrainingService(db)
    user_id = user_id or current_user.id
    return service.get_user_assignments(
        org_id=current_user.org_id,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/awareness/overdue")
def get_overdue_awareness_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Get overdue security awareness training assignments (AT-2)"""
    service = AwarenessTrainingService(db)
    return service.get_overdue_assignments(org_id=current_user.org_id)


# ============================================================================
# AT-3: Role-Based Security Training Endpoints
# ============================================================================

class RoleBasedTrainingCreate(BaseModel):
    training_code: str
    training_name: str
    training_description: Optional[str] = None
    training_category: str = "general"
    required_role: Optional[str] = None
    required_roles: Optional[List[str]] = None
    delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE
    duration_minutes: int = 60
    training_content_path: Optional[str] = None
    mandatory: bool = True
    required_frequency_months: int = 12
    passing_score_percentage: float = 80.0
    requires_competency_validation: bool = False
    competency_level_required: Optional[CompetencyLevel] = None


@router.post("/role-based", status_code=status.HTTP_201_CREATED)
def create_role_based_training(
    training: RoleBasedTrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Create a role-based security training (AT-3)"""
    service = RoleBasedTrainingService(db)
    return service.create_role_training(
        org_id=current_user.org_id,
        training_code=training.training_code,
        training_name=training.training_name,
        training_description=training.training_description,
        training_category=training.training_category,
        required_role=training.required_role,
        required_roles=training.required_roles,
        delivery_method=training.delivery_method,
        duration_minutes=training.duration_minutes,
        training_content_path=training.training_content_path,
        mandatory=training.mandatory,
        required_frequency_months=training.required_frequency_months,
        passing_score_percentage=training.passing_score_percentage,
        requires_competency_validation=training.requires_competency_validation,
        competency_level_required=training.competency_level_required,
        created_by_user_id=current_user.id,
    )


@router.post("/role-based/assign", status_code=status.HTTP_201_CREATED)
def assign_role_based_training(
    user_id: int,
    training_id: int,
    due_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Assign role-based security training to a user (AT-3)"""
    service = RoleBasedTrainingService(db)
    return service.assign_training(
        org_id=current_user.org_id,
        user_id=user_id,
        training_id=training_id,
        due_date=due_date,
        assigned_by_user_id=current_user.id,
    )


@router.post("/role-based/{assignment_id}/validate-competency")
def validate_competency(
    assignment_id: int,
    competency_level_achieved: CompetencyLevel,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Validate competency for role-based training (AT-3)"""
    service = RoleBasedTrainingService(db)
    return service.validate_competency(
        assignment_id=assignment_id,
        org_id=current_user.org_id,
        competency_level_achieved=competency_level_achieved,
        assessed_by_user_id=current_user.id,
    )


@router.get("/role-based")
def list_role_based_trainings(
    required_role: Optional[str] = Query(None),
    active: Optional[bool] = Query(True),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List role-based security trainings (AT-3)"""
    service = RoleBasedTrainingService(db)
    return service.list_trainings(
        org_id=current_user.org_id,
        required_role=required_role,
        active=active,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# AT-4: Security Training Records Endpoints
# ============================================================================

class TrainingRecordCreate(BaseModel):
    user_id: int
    training_type: str
    training_name: str
    training_provider: Optional[str] = None
    training_code: Optional[str] = None
    training_date: Optional[date] = None
    completion_date: Optional[date] = None
    delivery_method: TrainingDeliveryMethod = TrainingDeliveryMethod.ONLINE
    duration_hours: float = 1.0
    status: TrainingStatus = TrainingStatus.COMPLETED
    score_percentage: Optional[float] = None
    passed: Optional[bool] = None
    certificate_issued: bool = False
    certificate_number: Optional[str] = None
    certificate_issue_date: Optional[date] = None
    certificate_expiration_date: Optional[date] = None
    certificate_document_path: Optional[str] = None
    competency_level_achieved: Optional[CompetencyLevel] = None
    external_training: bool = False
    external_provider_name: Optional[str] = None
    ceu_credits: float = 0.0
    cme_credits: float = 0.0
    compliance_required: bool = True
    notes: Optional[str] = None


@router.post("/records", status_code=status.HTTP_201_CREATED)
def create_training_record(
    record: TrainingRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a security training record (AT-4)"""
    service = TrainingRecordsService(db)
    return service.create_training_record(
        org_id=current_user.org_id,
        user_id=record.user_id,
        training_type=record.training_type,
        training_name=record.training_name,
        training_provider=record.training_provider,
        training_code=record.training_code,
        training_date=record.training_date,
        completion_date=record.completion_date,
        delivery_method=record.delivery_method,
        duration_hours=record.duration_hours,
        status=record.status,
        score_percentage=record.score_percentage,
        passed=record.passed,
        certificate_issued=record.certificate_issued,
        certificate_number=record.certificate_number,
        certificate_issue_date=record.certificate_issue_date,
        certificate_expiration_date=record.certificate_expiration_date,
        certificate_document_path=record.certificate_document_path,
        competency_level_achieved=record.competency_level_achieved,
        competency_validated=False,
        external_training=record.external_training,
        external_provider_name=record.external_provider_name,
        ceu_credits=record.ceu_credits,
        cme_credits=record.cme_credits,
        compliance_required=record.compliance_required,
        notes=record.notes,
        recorded_by_user_id=current_user.id,
    )


@router.get("/records")
def list_training_records(
    user_id: Optional[int] = Query(None),
    training_type: Optional[str] = Query(None),
    status: Optional[TrainingStatus] = Query(None),
    compliance_status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security training records (AT-4)"""
    service = TrainingRecordsService(db)
    return service.list_training_records(
        org_id=current_user.org_id,
        user_id=user_id,
        training_type=training_type,
        status=status,
        compliance_status=compliance_status,
        limit=limit,
        offset=offset,
    )


@router.get("/records/{user_id}/history")
def get_user_training_history(
    user_id: int,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get complete training history for a user (AT-4)"""
    service = TrainingRecordsService(db)
    return service.get_user_training_history(
        org_id=current_user.org_id,
        user_id=user_id,
        limit=limit,
    )


@router.get("/records/compliance-report")
def get_compliance_report(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Get compliance report for training records (AT-4)"""
    service = TrainingRecordsService(db)
    return service.get_compliance_report(
        org_id=current_user.org_id,
        user_id=user_id,
    )


@router.get("/records/expiring-certificates")
def get_expiring_certificates(
    days_ahead: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training records with expiring certificates (AT-4)"""
    service = TrainingRecordsService(db)
    return service.get_expiring_certificates(
        org_id=current_user.org_id,
        days_ahead=days_ahead,
    )


# ============================================================================
# AT-5: Contacts with Security Groups Endpoints
# ============================================================================

class SecurityGroupContactCreate(BaseModel):
    user_id: int
    security_group_name: str
    security_group_type: str
    contact_type: ContactType
    security_group_website: Optional[str] = None
    security_group_contact_email: Optional[str] = None
    event_name: Optional[str] = None
    event_date: Optional[date] = None
    event_location: Optional[str] = None
    event_duration_days: Optional[int] = None
    membership_status: Optional[str] = None
    membership_start_date: Optional[date] = None
    membership_end_date: Optional[date] = None
    membership_level: Optional[str] = None
    participation_role: Optional[str] = None
    presentation_title: Optional[str] = None
    presentation_date: Optional[date] = None
    knowledge_shared: bool = False
    knowledge_shared_summary: Optional[str] = None
    knowledge_shared_with_team: bool = False
    benefits_received: Optional[str] = None
    outcomes_achieved: Optional[str] = None
    follow_up_required: bool = False
    notes: Optional[str] = None


@router.post("/security-contacts", status_code=status.HTTP_201_CREATED)
def create_security_group_contact(
    contact: SecurityGroupContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a security group contact record (AT-5)"""
    service = SecurityContactsService(db)
    return service.create_security_group_contact(
        org_id=current_user.org_id,
        user_id=contact.user_id,
        security_group_name=contact.security_group_name,
        security_group_type=contact.security_group_type,
        contact_type=contact.contact_type,
        security_group_website=contact.security_group_website,
        security_group_contact_email=contact.security_group_contact_email,
        event_name=contact.event_name,
        event_date=contact.event_date,
        event_location=contact.event_location,
        event_duration_days=contact.event_duration_days,
        membership_status=contact.membership_status,
        membership_start_date=contact.membership_start_date,
        membership_end_date=contact.membership_end_date,
        membership_level=contact.membership_level,
        participation_role=contact.participation_role,
        presentation_title=contact.presentation_title,
        presentation_date=contact.presentation_date,
        knowledge_shared=contact.knowledge_shared,
        knowledge_shared_summary=contact.knowledge_shared_summary,
        knowledge_shared_with_team=contact.knowledge_shared_with_team,
        benefits_received=contact.benefits_received,
        outcomes_achieved=contact.outcomes_achieved,
        follow_up_required=contact.follow_up_required,
        notes=contact.notes,
        recorded_by_user_id=current_user.id,
    )


@router.post("/security-contacts/{contact_id}/knowledge-sharing")
def record_knowledge_sharing(
    contact_id: int,
    knowledge_shared_summary: str,
    knowledge_shared_with_team: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record knowledge sharing from a security group contact (AT-5)"""
    service = SecurityContactsService(db)
    return service.record_knowledge_sharing(
        contact_id=contact_id,
        org_id=current_user.org_id,
        knowledge_shared_summary=knowledge_shared_summary,
        knowledge_shared_with_team=knowledge_shared_with_team,
    )


@router.get("/security-contacts")
def list_security_group_contacts(
    user_id: Optional[int] = Query(None),
    security_group_name: Optional[str] = Query(None),
    contact_type: Optional[ContactType] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security group contacts (AT-5)"""
    service = SecurityContactsService(db)
    return service.list_contacts(
        org_id=current_user.org_id,
        user_id=user_id,
        security_group_name=security_group_name,
        contact_type=contact_type,
        limit=limit,
        offset=offset,
    )


@router.get("/security-contacts/memberships")
def get_memberships(
    user_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security group memberships (AT-5)"""
    service = SecurityContactsService(db)
    return service.get_memberships(
        org_id=current_user.org_id,
        user_id=user_id,
        active_only=active_only,
    )


@router.get("/security-contacts/expiring-memberships")
def get_expiring_memberships(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get expiring security group memberships (AT-5)"""
    service = SecurityContactsService(db)
    return service.get_expiring_memberships(
        org_id=current_user.org_id,
        days_ahead=days_ahead,
    )
