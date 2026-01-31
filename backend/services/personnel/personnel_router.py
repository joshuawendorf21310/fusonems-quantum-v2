"""
Personnel Security (PS) API Router
FedRAMP PS Controls Implementation

Provides REST API endpoints for:
- PS-2: Position Risk Designation
- PS-3: Personnel Screening
- PS-4: Personnel Termination
- PS-5: Personnel Transfer
- PS-6: Access Agreements
- PS-7: Third-Party Personnel Security
- PS-8: Personnel Sanctions
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_roles
from models.user import User, UserRole
from models.personnel_security import (
    PositionRiskLevel,
    ScreeningStatus,
    TerminationStatus,
    TransferStatus,
    AgreementStatus,
    ThirdPartyStatus,
    SanctionStatus,
)

from .position_risk_service import PositionRiskService
from .screening_service import ScreeningService
from .termination_service import TerminationService
from .transfer_service import TransferService
from .access_agreements_service import AccessAgreementsService
from .third_party_security_service import ThirdPartySecurityService
from .sanctions_service import SanctionsService


router = APIRouter(
    prefix="/api/personnel/security",
    tags=["Personnel Security (FedRAMP PS)"],
)


# ============================================================================
# PS-2: Position Risk Designation Endpoints
# ============================================================================

class PositionRiskCreate(BaseModel):
    position_title: str
    position_id: str
    department: str
    risk_level: PositionRiskLevel
    risk_justification: str
    requires_clearance: bool = False
    clearance_level: Optional[str] = None
    special_requirements: Optional[str] = None
    review_frequency_months: int = 12


@router.post("/position-risk", status_code=status.HTTP_201_CREATED)
def create_position_risk(
    position_risk: PositionRiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Create a position risk designation (PS-2)"""
    service = PositionRiskService(db)
    return service.create_position_risk_designation(
        org_id=current_user.org_id,
        position_title=position_risk.position_title,
        position_id=position_risk.position_id,
        department=position_risk.department,
        risk_level=position_risk.risk_level,
        risk_justification=position_risk.risk_justification,
        requires_clearance=position_risk.requires_clearance,
        clearance_level=position_risk.clearance_level,
        special_requirements=position_risk.special_requirements,
        review_frequency_months=position_risk.review_frequency_months,
        created_by_user_id=current_user.id,
    )


@router.get("/position-risk")
def list_position_risks(
    risk_level: Optional[PositionRiskLevel] = Query(None),
    department: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List position risk designations (PS-2)"""
    service = PositionRiskService(db)
    return service.list_position_risk_designations(
        org_id=current_user.org_id,
        risk_level=risk_level,
        department=department,
        limit=limit,
        offset=offset,
    )


@router.get("/position-risk/due-for-review")
def get_designations_due_for_review(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get position risk designations due for review (PS-2)"""
    service = PositionRiskService(db)
    return service.get_designations_due_for_review(
        org_id=current_user.org_id,
        days_ahead=days_ahead,
    )


@router.get("/position-risk/statistics")
def get_risk_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get risk level statistics (PS-2)"""
    service = PositionRiskService(db)
    return service.get_risk_statistics(org_id=current_user.org_id)


# ============================================================================
# PS-3: Personnel Screening Endpoints
# ============================================================================

class ScreeningCreate(BaseModel):
    user_id: int
    position_risk_id: int
    screening_type: str = "initial"
    rescreening_frequency_months: int = 36


@router.post("/screening", status_code=status.HTTP_201_CREATED)
def initiate_screening(
    screening: ScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Initiate a personnel screening (PS-3)"""
    service = ScreeningService(db)
    return service.initiate_screening(
        org_id=current_user.org_id,
        user_id=screening.user_id,
        position_risk_id=screening.position_risk_id,
        screening_type=screening.screening_type,
        rescreening_frequency_months=screening.rescreening_frequency_months,
        created_by_user_id=current_user.id,
    )


@router.post("/screening/{screening_id}/component")
def update_screening_component(
    screening_id: int,
    component: str = Query(..., description="Component: background_check, credit_check, drug_test, reference_check"),
    completed: bool = Query(True),
    result: Optional[str] = Query(None),
    completed_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Update a screening component (PS-3)"""
    service = ScreeningService(db)
    return service.update_screening_component(
        screening_id=screening_id,
        org_id=current_user.org_id,
        component=component,
        completed=completed,
        result=result,
        completed_date=completed_date,
    )


@router.get("/screening")
def list_screenings(
    user_id: Optional[int] = Query(None),
    status: Optional[ScreeningStatus] = Query(None),
    screening_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personnel screenings (PS-3)"""
    service = ScreeningService(db)
    return service.list_screenings(
        org_id=current_user.org_id,
        user_id=user_id,
        status=status,
        screening_type=screening_type,
        limit=limit,
        offset=offset,
    )


@router.get("/screening/due-for-rescreening")
def get_screenings_due_for_rescreening(
    days_ahead: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get screenings due for rescreening (PS-3)"""
    service = ScreeningService(db)
    return service.get_screenings_due_for_rescreening(
        org_id=current_user.org_id,
        days_ahead=days_ahead,
    )


# ============================================================================
# PS-4: Personnel Termination Endpoints
# ============================================================================

class TerminationCreate(BaseModel):
    user_id: int
    termination_date: date
    termination_reason: str
    termination_type: str
    termination_notes: Optional[str] = None


@router.post("/termination", status_code=status.HTTP_201_CREATED)
def initiate_termination(
    termination: TerminationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin])),
):
    """Initiate a personnel termination (PS-4)"""
    service = TerminationService(db)
    return service.initiate_termination(
        org_id=current_user.org_id,
        user_id=termination.user_id,
        termination_date=termination.termination_date,
        termination_reason=termination.termination_reason,
        termination_type=termination.termination_type,
        termination_notes=termination.termination_notes,
        initiated_by_user_id=current_user.id,
    )


@router.post("/termination/{termination_id}/revoke-access")
def revoke_access(
    termination_id: int,
    systems_access_revoked: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin])),
):
    """Revoke system access for terminated personnel (PS-4)"""
    service = TerminationService(db)
    return service.revoke_access(
        termination_id=termination_id,
        org_id=current_user.org_id,
        systems_access_revoked=systems_access_revoked,
        revoked_by_user_id=current_user.id,
    )


@router.post("/termination/{termination_id}/exit-interview")
def complete_exit_interview(
    termination_id: int,
    exit_interview_notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Complete exit interview (PS-4)"""
    service = TerminationService(db)
    return service.complete_exit_interview(
        termination_id=termination_id,
        org_id=current_user.org_id,
        exit_interview_notes=exit_interview_notes,
        conducted_by_user_id=current_user.id,
    )


@router.get("/termination")
def list_terminations(
    user_id: Optional[int] = Query(None),
    status: Optional[TerminationStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personnel terminations (PS-4)"""
    service = TerminationService(db)
    return service.list_terminations(
        org_id=current_user.org_id,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# PS-5: Personnel Transfer Endpoints
# ============================================================================

class TransferCreate(BaseModel):
    user_id: int
    transfer_date: date
    transfer_reason: str
    to_position_id: int
    to_department: str
    to_role: str
    from_position_id: Optional[int] = None
    from_department: Optional[str] = None
    from_role: Optional[str] = None
    requires_new_screening: bool = False
    transfer_notes: Optional[str] = None


@router.post("/transfer", status_code=status.HTTP_201_CREATED)
def initiate_transfer(
    transfer: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin])),
):
    """Initiate a personnel transfer (PS-5)"""
    service = TransferService(db)
    return service.initiate_transfer(
        org_id=current_user.org_id,
        user_id=transfer.user_id,
        transfer_date=transfer.transfer_date,
        transfer_reason=transfer.transfer_reason,
        to_position_id=transfer.to_position_id,
        to_department=transfer.to_department,
        to_role=transfer.to_role,
        from_position_id=transfer.from_position_id,
        from_department=transfer.from_department,
        from_role=transfer.from_role,
        requires_new_screening=transfer.requires_new_screening,
        transfer_notes=transfer.transfer_notes,
        initiated_by_user_id=current_user.id,
    )


@router.post("/transfer/{transfer_id}/adjust-access")
def adjust_access(
    transfer_id: int,
    access_changes: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin])),
):
    """Adjust system access for transferred personnel (PS-5)"""
    service = TransferService(db)
    return service.adjust_access(
        transfer_id=transfer_id,
        org_id=current_user.org_id,
        access_changes=access_changes,
        adjusted_by_user_id=current_user.id,
    )


@router.get("/transfer")
def list_transfers(
    user_id: Optional[int] = Query(None),
    status: Optional[TransferStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personnel transfers (PS-5)"""
    service = TransferService(db)
    return service.list_transfers(
        org_id=current_user.org_id,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# PS-6: Access Agreements Endpoints
# ============================================================================

class AccessAgreementCreate(BaseModel):
    user_id: int
    agreement_type: str
    agreement_title: str
    agreement_version: str
    agreement_content: Optional[str] = None
    agreement_document_path: Optional[str] = None
    effective_date: Optional[date] = None
    requires_renewal: bool = True
    renewal_frequency_months: int = 12


@router.post("/access-agreement", status_code=status.HTTP_201_CREATED)
def create_access_agreement(
    agreement: AccessAgreementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Create an access agreement (PS-6)"""
    service = AccessAgreementsService(db)
    return service.create_access_agreement(
        org_id=current_user.org_id,
        user_id=agreement.user_id,
        agreement_type=agreement.agreement_type,
        agreement_title=agreement.agreement_title,
        agreement_version=agreement.agreement_version,
        agreement_content=agreement.agreement_content,
        agreement_document_path=agreement.agreement_document_path,
        effective_date=agreement.effective_date,
        requires_renewal=agreement.requires_renewal,
        renewal_frequency_months=agreement.renewal_frequency_months,
        created_by_user_id=current_user.id,
    )


@router.post("/access-agreement/{agreement_id}/sign")
def sign_agreement(
    agreement_id: int,
    signature_method: str = Query("electronic"),
    signed_document_path: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sign an access agreement (PS-6)"""
    service = AccessAgreementsService(db)
    return service.sign_agreement(
        agreement_id=agreement_id,
        org_id=current_user.org_id,
        signature_method=signature_method,
        signed_document_path=signed_document_path,
        signed_by_user_id=current_user.id,
    )


@router.get("/access-agreement")
def list_agreements(
    user_id: Optional[int] = Query(None),
    agreement_type: Optional[str] = Query(None),
    status: Optional[AgreementStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List access agreements (PS-6)"""
    service = AccessAgreementsService(db)
    return service.list_agreements(
        org_id=current_user.org_id,
        user_id=user_id,
        agreement_type=agreement_type,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/access-agreement/due-for-renewal")
def get_agreements_due_for_renewal(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get access agreements due for renewal (PS-6)"""
    service = AccessAgreementsService(db)
    return service.get_agreements_due_for_renewal(
        org_id=current_user.org_id,
        days_ahead=days_ahead,
    )


# ============================================================================
# PS-7: Third-Party Personnel Security Endpoints
# ============================================================================

class ThirdPartyCreate(BaseModel):
    vendor_name: str
    vendor_contact_name: str
    vendor_contact_email: str
    vendor_contact_phone: Optional[str] = None
    personnel_name: Optional[str] = None
    personnel_email: Optional[str] = None
    personnel_phone: Optional[str] = None
    personnel_role: Optional[str] = None
    contract_number: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    security_clearance_required: bool = False
    security_clearance_level: Optional[str] = None
    background_check_required: bool = True
    nda_required: bool = True
    notes: Optional[str] = None


@router.post("/third-party", status_code=status.HTTP_201_CREATED)
def register_third_party(
    third_party: ThirdPartyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Register third-party personnel (PS-7)"""
    service = ThirdPartySecurityService(db)
    return service.register_third_party_personnel(
        org_id=current_user.org_id,
        vendor_name=third_party.vendor_name,
        vendor_contact_name=third_party.vendor_contact_name,
        vendor_contact_email=third_party.vendor_contact_email,
        vendor_contact_phone=third_party.vendor_contact_phone,
        personnel_name=third_party.personnel_name,
        personnel_email=third_party.personnel_email,
        personnel_phone=third_party.personnel_phone,
        personnel_role=third_party.personnel_role,
        contract_number=third_party.contract_number,
        contract_start_date=third_party.contract_start_date,
        contract_end_date=third_party.contract_end_date,
        security_clearance_required=third_party.security_clearance_required,
        security_clearance_level=third_party.security_clearance_level,
        background_check_required=third_party.background_check_required,
        nda_required=third_party.nda_required,
        notes=third_party.notes,
        created_by_user_id=current_user.id,
    )


@router.post("/third-party/{third_party_id}/grant-access")
def grant_third_party_access(
    third_party_id: int,
    systems_accessed: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin])),
):
    """Grant system access to third-party personnel (PS-7)"""
    service = ThirdPartySecurityService(db)
    return service.grant_system_access(
        third_party_id=third_party_id,
        org_id=current_user.org_id,
        systems_accessed=systems_accessed,
    )


@router.get("/third-party")
def list_third_party_personnel(
    vendor_name: Optional[str] = Query(None),
    status: Optional[ThirdPartyStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List third-party personnel (PS-7)"""
    service = ThirdPartySecurityService(db)
    return service.list_third_party_personnel(
        org_id=current_user.org_id,
        vendor_name=vendor_name,
        status=status,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# PS-8: Personnel Sanctions Endpoints
# ============================================================================

class SanctionCreate(BaseModel):
    user_id: int
    violation_type: str
    violation_description: str
    violation_date: date
    sanction_type: str
    sanction_severity: str
    sanction_start_date: date
    sanction_end_date: Optional[date] = None
    sanction_conditions: Optional[str] = None
    remediation_required: bool = True
    remediation_plan: Optional[str] = None
    incident_report_path: Optional[str] = None
    supporting_documents: Optional[List[str]] = None
    notes: Optional[str] = None


@router.post("/sanction", status_code=status.HTTP_201_CREATED)
def create_sanction(
    sanction: SanctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Create a personnel sanction (PS-8)"""
    service = SanctionsService(db)
    return service.create_sanction(
        org_id=current_user.org_id,
        user_id=sanction.user_id,
        violation_type=sanction.violation_type,
        violation_description=sanction.violation_description,
        violation_date=sanction.violation_date,
        sanction_type=sanction.sanction_type,
        sanction_severity=sanction.sanction_severity,
        sanction_start_date=sanction.sanction_start_date,
        sanction_end_date=sanction.sanction_end_date,
        sanction_conditions=sanction.sanction_conditions,
        remediation_required=sanction.remediation_required,
        remediation_plan=sanction.remediation_plan,
        incident_report_path=sanction.incident_report_path,
        supporting_documents=sanction.supporting_documents,
        notes=sanction.notes,
        reported_by_user_id=current_user.id,
    )


@router.post("/sanction/{sanction_id}/complete-remediation")
def complete_remediation(
    sanction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.compliance])),
):
    """Complete remediation for a sanction (PS-8)"""
    service = SanctionsService(db)
    return service.complete_remediation(
        sanction_id=sanction_id,
        org_id=current_user.org_id,
    )


@router.get("/sanction")
def list_sanctions(
    user_id: Optional[int] = Query(None),
    violation_type: Optional[str] = Query(None),
    status: Optional[SanctionStatus] = Query(None),
    sanction_severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personnel sanctions (PS-8)"""
    service = SanctionsService(db)
    return service.list_sanctions(
        org_id=current_user.org_id,
        user_id=user_id,
        violation_type=violation_type,
        status=status,
        sanction_severity=sanction_severity,
        limit=limit,
        offset=offset,
    )
