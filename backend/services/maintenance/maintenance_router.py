"""
Maintenance API Router for FedRAMP MA-2 through MA-6

Provides REST API endpoints for all Maintenance controls.
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
from services.maintenance.controlled_maintenance_service import ControlledMaintenanceService
from services.maintenance.maintenance_tools_service import MaintenanceToolsService
from services.maintenance.nonlocal_maintenance_service import NonlocalMaintenanceService
from services.maintenance.maintenance_personnel_service import MaintenancePersonnelService
from services.maintenance.timely_maintenance_service import TimelyMaintenanceService


router = APIRouter(
    prefix="/api/compliance/maintenance",
    tags=["Maintenance"],
)


# ============================================================================
# MA-2: CONTROLLED MAINTENANCE ENDPOINTS
# ============================================================================

class MaintenanceCreate(BaseModel):
    title: str
    description: str
    maintenance_type: str
    system_name: str
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    priority: str = Field(default="medium")
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    impact_assessment: Optional[str] = None
    downtime_expected: bool = False
    downtime_duration_minutes: Optional[int] = None
    approval_required: bool = True


@router.post("/maintenance", status_code=status.HTTP_201_CREATED)
def create_maintenance(
    maintenance: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create maintenance record (MA-2)."""
    try:
        return ControlledMaintenanceService.create_maintenance(
            db=db,
            org_id=current_user.org_id,
            title=maintenance.title,
            description=maintenance.description,
            maintenance_type=maintenance.maintenance_type,
            system_name=maintenance.system_name,
            scheduled_start_date=maintenance.scheduled_start_date,
            scheduled_end_date=maintenance.scheduled_end_date,
            requested_by_user_id=current_user.id,
            requested_by_email=current_user.email,
            priority=maintenance.priority,
            component_name=maintenance.component_name,
            component_type=maintenance.component_type,
            impact_assessment=maintenance.impact_assessment,
            downtime_expected=maintenance.downtime_expected,
            downtime_duration_minutes=maintenance.downtime_duration_minutes,
            approval_required=maintenance.approval_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/maintenance/{maintenance_id}/approve")
def approve_maintenance(
    maintenance_id: UUID,
    approval_comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Approve maintenance (MA-2)."""
    try:
        return ControlledMaintenanceService.approve_maintenance(
            db=db,
            maintenance_id=maintenance_id,
            org_id=current_user.org_id,
            approved_by_user_id=current_user.id,
            approval_comment=approval_comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/maintenance/{maintenance_id}/start")
def start_maintenance(
    maintenance_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Start maintenance (MA-2)."""
    try:
        return ControlledMaintenanceService.start_maintenance(
            db=db,
            maintenance_id=maintenance_id,
            org_id=current_user.org_id,
            started_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/maintenance/{maintenance_id}/complete")
def complete_maintenance(
    maintenance_id: UUID,
    completion_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Complete maintenance (MA-2)."""
    try:
        return ControlledMaintenanceService.complete_maintenance(
            db=db,
            maintenance_id=maintenance_id,
            org_id=current_user.org_id,
            completion_notes=completion_notes,
            completed_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/maintenance")
def list_maintenance(
    maintenance_status: Optional[str] = Query(None),
    maintenance_type: Optional[str] = Query(None),
    system_name: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List maintenance records (MA-2)."""
    return ControlledMaintenanceService.list_maintenance(
        db=db,
        org_id=current_user.org_id,
        maintenance_status=maintenance_status,
        maintenance_type=maintenance_type,
        system_name=system_name,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# MA-3: MAINTENANCE TOOLS ENDPOINTS
# ============================================================================

class MaintenanceToolCreate(BaseModel):
    tool_name: str
    tool_type: str
    tool_description: Optional[str] = None
    tool_version: Optional[str] = None
    tool_manufacturer: Optional[str] = None
    tool_serial_number: Optional[str] = None
    security_risks: Optional[dict] = None
    security_mitigations: Optional[str] = None
    requires_approval: bool = True
    usage_restrictions: Optional[str] = None
    allowed_systems: Optional[List[str]] = None
    restricted_systems: Optional[List[str]] = None
    location: Optional[str] = None


@router.post("/tools", status_code=status.HTTP_201_CREATED)
def register_tool(
    tool: MaintenanceToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Register maintenance tool (MA-3)."""
    try:
        return MaintenanceToolsService.register_tool(
            db=db,
            org_id=current_user.org_id,
            tool_name=tool.tool_name,
            tool_type=tool.tool_type,
            tool_description=tool.tool_description,
            tool_version=tool.tool_version,
            tool_manufacturer=tool.tool_manufacturer,
            tool_serial_number=tool.tool_serial_number,
            tool_capabilities=None,
            security_risks=tool.security_risks,
            security_mitigations=tool.security_mitigations,
            requires_approval=tool.requires_approval,
            usage_restrictions=tool.usage_restrictions,
            allowed_systems=tool.allowed_systems,
            restricted_systems=tool.restricted_systems,
            location=tool.location,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tools/{tool_id}/approve")
def approve_tool(
    tool_id: UUID,
    authorization_expires_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Approve maintenance tool (MA-3)."""
    try:
        return MaintenanceToolsService.approve_tool(
            db=db,
            tool_id=tool_id,
            org_id=current_user.org_id,
            authorized_by_user_id=current_user.id,
            authorization_expires_at=authorization_expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tools")
def list_tools(
    tool_status: Optional[str] = Query(None),
    tool_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List maintenance tools (MA-3)."""
    return MaintenanceToolsService.list_tools(
        db=db,
        org_id=current_user.org_id,
        tool_status=tool_status,
        tool_type=tool_type,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# MA-4: NONLOCAL MAINTENANCE ENDPOINTS
# ============================================================================

class RemoteMaintenanceSessionCreate(BaseModel):
    session_purpose: str
    system_name: str
    personnel_id: UUID
    access_method: str
    system_ip_address: Optional[str] = None
    system_hostname: Optional[str] = None
    maintenance_id: Optional[UUID] = None
    access_protocol: Optional[str] = None
    encryption_required: bool = True
    encryption_method: Optional[str] = None
    authorization_expires_at: Optional[datetime] = None
    session_monitored: bool = True
    allowed_commands: Optional[List[str]] = None
    restricted_commands: Optional[List[str]] = None
    allowed_files: Optional[List[str]] = None
    restricted_files: Optional[List[str]] = None


@router.post("/remote-sessions", status_code=status.HTTP_201_CREATED)
def create_remote_session(
    session: RemoteMaintenanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Create remote maintenance session (MA-4)."""
    try:
        return NonlocalMaintenanceService.create_session(
            db=db,
            org_id=current_user.org_id,
            session_purpose=session.session_purpose,
            system_name=session.system_name,
            personnel_id=session.personnel_id,
            authorized_by_user_id=current_user.id,
            access_method=session.access_method,
            system_ip_address=session.system_ip_address,
            system_hostname=session.system_hostname,
            maintenance_id=session.maintenance_id,
            access_protocol=session.access_protocol,
            encryption_required=session.encryption_required,
            encryption_method=session.encryption_method,
            authorization_expires_at=session.authorization_expires_at,
            session_monitored=session.session_monitored,
            allowed_commands=session.allowed_commands,
            restricted_commands=session.restricted_commands,
            allowed_files=session.allowed_files,
            restricted_files=session.restricted_files,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/remote-sessions/{session_id}/terminate")
def terminate_session(
    session_id: UUID,
    termination_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Terminate remote maintenance session (MA-4)."""
    try:
        return NonlocalMaintenanceService.terminate_session(
            db=db,
            session_id=session_id,
            org_id=current_user.org_id,
            terminated_by_user_id=current_user.id,
            termination_reason=termination_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/remote-sessions")
def list_remote_sessions(
    session_status: Optional[str] = Query(None),
    system_name: Optional[str] = Query(None),
    personnel_id: Optional[UUID] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List remote maintenance sessions (MA-4)."""
    return NonlocalMaintenanceService.list_sessions(
        db=db,
        org_id=current_user.org_id,
        session_status=session_status,
        system_name=system_name,
        personnel_id=personnel_id,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# MA-5: MAINTENANCE PERSONNEL ENDPOINTS
# ============================================================================

class MaintenancePersonnelCreate(BaseModel):
    personnel_name: str
    personnel_email: Optional[str] = None
    personnel_phone: Optional[str] = None
    company_name: Optional[str] = None
    company_contact: Optional[str] = None
    company_phone: Optional[str] = None
    escort_required: str = Field(default="required")
    access_level: Optional[str] = None
    allowed_systems: Optional[List[str]] = None
    restricted_systems: Optional[List[str]] = None


@router.post("/personnel", status_code=status.HTTP_201_CREATED)
def register_personnel(
    personnel: MaintenancePersonnelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Register maintenance personnel (MA-5)."""
    try:
        return MaintenancePersonnelService.register_personnel(
            db=db,
            org_id=current_user.org_id,
            personnel_name=personnel.personnel_name,
            personnel_email=personnel.personnel_email,
            personnel_phone=personnel.personnel_phone,
            company_name=personnel.company_name,
            company_contact=personnel.company_contact,
            company_phone=personnel.company_phone,
            escort_required=personnel.escort_required,
            access_level=personnel.access_level,
            allowed_systems=personnel.allowed_systems,
            restricted_systems=personnel.restricted_systems,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/personnel/{personnel_id}/authorize")
def authorize_personnel(
    personnel_id: UUID,
    authorization_expires_at: Optional[datetime] = None,
    background_check_completed: bool = False,
    background_check_date: Optional[datetime] = None,
    background_check_results: Optional[str] = None,
    escort_personnel_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Authorize maintenance personnel (MA-5)."""
    try:
        return MaintenancePersonnelService.authorize_personnel(
            db=db,
            personnel_id=personnel_id,
            org_id=current_user.org_id,
            authorized_by_user_id=current_user.id,
            authorization_expires_at=authorization_expires_at,
            background_check_completed=background_check_completed,
            background_check_date=background_check_date,
            background_check_results=background_check_results,
            escort_personnel_id=escort_personnel_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/personnel/{personnel_id}/revoke")
def revoke_personnel_authorization(
    personnel_id: UUID,
    revocation_reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Revoke personnel authorization (MA-5)."""
    try:
        return MaintenancePersonnelService.revoke_authorization(
            db=db,
            personnel_id=personnel_id,
            org_id=current_user.org_id,
            revocation_reason=revocation_reason,
            revoked_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/personnel")
def list_personnel(
    authorization_status: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List maintenance personnel (MA-5)."""
    return MaintenancePersonnelService.list_personnel(
        db=db,
        org_id=current_user.org_id,
        authorization_status=authorization_status,
        company_name=company_name,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# MA-6: TIMELY MAINTENANCE ENDPOINTS
# ============================================================================

class MaintenanceSLACreate(BaseModel):
    system_name: str
    maintenance_type: str
    sla_hours: int
    maintenance_due_date: datetime
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    preventive_schedule_days: Optional[int] = None


@router.post("/sla", status_code=status.HTTP_201_CREATED)
def create_maintenance_sla(
    sla: MaintenanceSLACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Create maintenance SLA (MA-6)."""
    try:
        return TimelyMaintenanceService.create_sla(
            db=db,
            org_id=current_user.org_id,
            system_name=sla.system_name,
            maintenance_type=sla.maintenance_type,
            sla_hours=sla.sla_hours,
            maintenance_due_date=sla.maintenance_due_date,
            component_name=sla.component_name,
            component_type=sla.component_type,
            preventive_schedule_days=sla.preventive_schedule_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sla/{sla_id}/complete")
def update_maintenance_completion(
    sla_id: UUID,
    maintenance_id: UUID,
    maintenance_completed_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.security_officer])),
):
    """Update maintenance completion (MA-6)."""
    try:
        return TimelyMaintenanceService.update_completion(
            db=db,
            timely_maint_id=sla_id,
            org_id=current_user.org_id,
            maintenance_id=maintenance_id,
            maintenance_completed_date=maintenance_completed_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sla/compliance")
def check_sla_compliance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check SLA compliance (MA-6)."""
    return TimelyMaintenanceService.check_sla_compliance(
        db=db,
        org_id=current_user.org_id,
    )


@router.get("/sla")
def list_maintenance_slas(
    system_name: Optional[str] = Query(None),
    sla_status: Optional[str] = Query(None),
    maintenance_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List maintenance SLAs (MA-6)."""
    return TimelyMaintenanceService.list_slas(
        db=db,
        org_id=current_user.org_id,
        system_name=system_name,
        sla_status=sla_status,
        maintenance_type=maintenance_type,
        limit=limit,
        offset=offset,
    )
