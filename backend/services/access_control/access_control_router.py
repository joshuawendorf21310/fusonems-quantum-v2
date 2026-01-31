"""
Access Control Router for FedRAMP AC Controls

Provides API endpoints for all access control services.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole
from services.access_control import (
    InformationFlowService,
    LeastPrivilegeService,
    RemoteAccessService,
    WirelessAccessService,
    MobileDeviceService,
    ExternalSystemsService,
    PublicContentService,
)


router = APIRouter(prefix="/api/access-control", tags=["Access Control"])


# ============================================================================
# AC-4: Information Flow Enforcement
# ============================================================================

class FlowRuleCreate(BaseModel):
    rule_name: str
    source_segment: str
    destination_segment: str
    direction: str
    action: str
    description: Optional[str] = None
    protocol: Optional[str] = None
    port_range: Optional[str] = None
    data_classification: Optional[str] = None
    requires_encryption: bool = False
    requires_authentication: bool = True
    priority: int = 100
    conditions: Optional[dict] = None
    action_parameters: Optional[dict] = None


class FlowEvaluationRequest(BaseModel):
    source_segment: str
    destination_segment: str
    direction: str
    protocol: Optional[str] = None
    port: Optional[int] = None
    data_classification: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    data_size: Optional[int] = None


@router.post("/ac4/rules", status_code=status.HTTP_201_CREATED)
def create_flow_rule(
    rule: FlowRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create an information flow rule"""
    service = InformationFlowService(db, user.org_id, user.id)
    return service.create_flow_rule(**rule.dict())


@router.post("/ac4/evaluate")
def evaluate_flow(
    request: FlowEvaluationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Evaluate an information flow request"""
    service = InformationFlowService(db, user.org_id, user.id)
    return service.evaluate_flow(**request.dict(), user_id=user.id)


@router.get("/ac4/rules")
def get_flow_rules(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get active information flow rules"""
    service = InformationFlowService(db, user.org_id, user.id)
    return service.get_active_rules()


@router.get("/ac4/logs")
def get_flow_logs(
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    rule_id: Optional[int] = None,
    action_taken: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get information flow logs"""
    service = InformationFlowService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_flow_logs(
        limit=limit,
        start_date=start,
        end_date=end,
        rule_id=rule_id,
        action_taken=action_taken,
    )


@router.post("/ac4/rules/{rule_id}/approve")
def approve_flow_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve an information flow rule"""
    service = InformationFlowService(db, user.org_id, user.id)
    return service.approve_rule(rule_id, user.id)


@router.delete("/ac4/rules/{rule_id}")
def deactivate_flow_rule(
    rule_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Deactivate an information flow rule"""
    service = InformationFlowService(db, user.org_id, user.id)
    return service.deactivate_rule(rule_id, reason)


# ============================================================================
# AC-6: Least Privilege
# ============================================================================

class PrivilegeRequest(BaseModel):
    user_id: int
    privilege_name: str
    privilege_type: str
    justification: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    business_need: Optional[str] = None
    expires_at: Optional[str] = None
    review_frequency_days: int = 90


class EscalationRequest(BaseModel):
    user_id: int
    escalated_privilege: str
    reason: str
    duration_hours: int = 4
    task_description: Optional[str] = None
    privilege_id: Optional[int] = None


@router.post("/ac6/privileges", status_code=status.HTTP_201_CREATED)
def request_privilege(
    request: PrivilegeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Request a privilege assignment"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    
    expires_at = None
    if request.expires_at:
        expires_at = datetime.fromisoformat(request.expires_at.replace('Z', '+00:00'))
    
    return service.request_privilege(
        user_id=request.user_id,
        privilege_name=request.privilege_name,
        privilege_type=request.privilege_type,
        justification=request.justification,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        business_need=request.business_need,
        expires_at=expires_at,
        review_frequency_days=request.review_frequency_days,
    )


@router.post("/ac6/privileges/{assignment_id}/approve")
def approve_privilege(
    assignment_id: int,
    expires_at: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve a privilege assignment"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    
    exp_at = None
    if expires_at:
        exp_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    return service.approve_privilege(assignment_id, user.id, exp_at)


@router.post("/ac6/privileges/{assignment_id}/revoke")
def revoke_privilege(
    assignment_id: int,
    revocation_reason: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Revoke a privilege assignment"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.revoke_privilege(assignment_id, user.id, revocation_reason)


@router.post("/ac6/escalations", status_code=status.HTTP_201_CREATED)
def request_escalation(
    request: EscalationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Request temporary privilege escalation"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.request_escalation(**request.dict())


@router.post("/ac6/escalations/{escalation_id}/approve")
def approve_escalation(
    escalation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve a privilege escalation"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.approve_escalation(escalation_id, user.id)


@router.get("/ac6/excessive-privileges")
def detect_excessive_privileges(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Detect users with excessive privileges"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.detect_excessive_privileges(user_id)


@router.get("/ac6/pending-reviews")
def get_pending_privilege_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get privileges pending review"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.get_pending_reviews()


@router.post("/ac6/privileges/{assignment_id}/review")
def review_privilege(
    assignment_id: int,
    keep_privilege: bool,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Review a privilege assignment"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.review_privilege(assignment_id, user.id, keep_privilege, review_notes)


@router.get("/ac6/users/{user_id}/privileges")
def get_user_privileges(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get all active privileges for a user"""
    service = LeastPrivilegeService(db, user.org_id, user.id)
    return service.get_user_privileges(user_id)


# ============================================================================
# AC-17: Remote Access
# ============================================================================

class RemoteAccessPolicyCreate(BaseModel):
    policy_name: str
    allowed_methods: List[str]
    requires_vpn: bool = True
    requires_mfa: bool = True
    description: Optional[str] = None
    allowed_countries: Optional[List[str]] = None
    allowed_regions: Optional[List[str]] = None
    blocked_ips: Optional[List[str]] = None
    max_session_duration_minutes: int = 480
    idle_timeout_minutes: int = 30
    max_concurrent_sessions: int = 3
    requires_trusted_device: bool = False
    requires_device_encryption: bool = True


class RemoteSessionCreate(BaseModel):
    user_id: int
    access_method: str
    client_ip: str
    session_id: str
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    client_location: Optional[dict] = None
    vpn_connection_id: Optional[str] = None
    vpn_server: Optional[str] = None
    policy_id: Optional[int] = None


@router.post("/ac17/policies", status_code=status.HTTP_201_CREATED)
def create_remote_access_policy(
    policy: RemoteAccessPolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a remote access policy"""
    service = RemoteAccessService(db, user.org_id, user.id)
    return service.create_policy(**policy.dict())


@router.post("/ac17/sessions", status_code=status.HTTP_201_CREATED)
def create_remote_session(
    session: RemoteSessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Create a remote access session"""
    service = RemoteAccessService(db, user.org_id, user.id)
    return service.create_session(**session.dict())


@router.post("/ac17/sessions/{session_id}/activity")
def update_session_activity(
    session_id: str,
    bytes_sent: Optional[int] = None,
    bytes_received: Optional[int] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Update remote session activity"""
    service = RemoteAccessService(db, user.org_id, user.id)
    return service.update_session_activity(session_id, bytes_sent, bytes_received, action)


@router.post("/ac17/sessions/{session_id}/terminate")
def terminate_remote_session(
    session_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Terminate a remote access session"""
    service = RemoteAccessService(db, user.org_id, user.id)
    return service.terminate_session(session_id, user.id, reason)


@router.get("/ac17/sessions")
def get_active_remote_sessions(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get active remote access sessions"""
    service = RemoteAccessService(db, user.org_id, user.id)
    return service.get_active_sessions(user_id)


@router.get("/ac17/sessions/history")
def get_remote_session_history(
    user_id: Optional[int] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get remote access session history"""
    service = RemoteAccessService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_session_history(user_id, limit, start, end)


# ============================================================================
# AC-18: Wireless Access
# ============================================================================

class WirelessPolicyCreate(BaseModel):
    policy_name: str
    minimum_security_standard: str = "wpa2"
    requires_encryption: bool = True
    requires_authentication: bool = True
    requires_certificate: bool = False
    requires_device_registration: bool = True
    description: Optional[str] = None
    ssid: Optional[str] = None
    allowed_device_types: Optional[List[str]] = None
    network_segment: Optional[str] = None
    allows_internet_access: bool = False
    allows_internal_access: bool = True


class WirelessDeviceRegister(BaseModel):
    device_name: str
    mac_address: str
    device_type: str
    user_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    policy_id: Optional[int] = None
    encryption_support: Optional[List[str]] = None
    certificate_installed: bool = False
    certificate_expires_at: Optional[str] = None


@router.post("/ac18/policies", status_code=status.HTTP_201_CREATED)
def create_wireless_policy(
    policy: WirelessPolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Create a wireless network policy"""
    service = WirelessAccessService(db, user.org_id, user.id)
    
    cert_expires = None
    if policy.certificate_expires_at:
        cert_expires = datetime.fromisoformat(policy.certificate_expires_at.replace('Z', '+00:00'))
    
    policy_dict = policy.dict()
    policy_dict['certificate_expires_at'] = cert_expires
    
    return service.create_policy(**policy_dict)


@router.post("/ac18/devices", status_code=status.HTTP_201_CREATED)
def register_wireless_device(
    device: WirelessDeviceRegister,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Register a wireless device"""
    service = WirelessAccessService(db, user.org_id, user.id)
    
    cert_expires = None
    if device.certificate_expires_at:
        cert_expires = datetime.fromisoformat(device.certificate_expires_at.replace('Z', '+00:00'))
    
    device_dict = device.dict()
    device_dict['certificate_expires_at'] = cert_expires
    
    return service.register_device(**device_dict)


@router.post("/ac18/devices/{device_id}/approve")
def approve_wireless_device(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve a wireless device"""
    service = WirelessAccessService(db, user.org_id, user.id)
    return service.approve_device(device_id, user.id)


@router.post("/ac18/devices/{device_id}/suspend")
def suspend_wireless_device(
    device_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Suspend a wireless device"""
    service = WirelessAccessService(db, user.org_id, user.id)
    return service.suspend_device(device_id, reason)


@router.get("/ac18/devices")
def get_wireless_devices(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get registered wireless devices"""
    service = WirelessAccessService(db, user.org_id, user.id)
    return service.get_registered_devices(user_id, status)


@router.get("/ac18/logs")
def get_wireless_connection_logs(
    device_id: Optional[int] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get wireless connection logs"""
    service = WirelessAccessService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_connection_logs(device_id, limit, start, end)


# ============================================================================
# AC-19: Mobile Device Access
# ============================================================================

class MobileDeviceRegister(BaseModel):
    device_name: str
    device_type: str
    os_type: str
    user_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    mdm_device_id: Optional[str] = None


class MobileDeviceWipeRequest(BaseModel):
    device_id: int
    wipe_type: str
    reason: str


@router.post("/ac19/devices", status_code=status.HTTP_201_CREATED)
def register_mobile_device(
    device: MobileDeviceRegister,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Register a mobile device"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.register_device(**device.dict())


@router.post("/ac19/devices/{device_id}/compliance")
def update_device_compliance(
    device_id: int,
    encryption_enabled: Optional[bool] = None,
    screen_lock_enabled: Optional[bool] = None,
    biometric_enabled: Optional[bool] = None,
    jailbroken_rooted: Optional[bool] = None,
    mdm_managed: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Update device compliance information"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.update_device_compliance(
        device_id,
        encryption_enabled,
        screen_lock_enabled,
        biometric_enabled,
        jailbroken_rooted,
        mdm_managed,
    )


@router.get("/ac19/devices/{device_id}/compliance")
def check_device_compliance(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Check device compliance status"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.check_compliance(device_id)


@router.post("/ac19/wipes", status_code=status.HTTP_201_CREATED)
def initiate_device_wipe(
    request: MobileDeviceWipeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Initiate a remote wipe operation"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.initiate_wipe(
        request.device_id,
        request.wipe_type,
        request.reason,
        user.id,
    )


@router.post("/ac19/wipes/{wipe_id}/complete")
def complete_device_wipe(
    wipe_id: int,
    success: bool,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Complete a remote wipe operation"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.complete_wipe(wipe_id, success, error_message)


@router.get("/ac19/devices")
def get_mobile_devices(
    user_id: Optional[int] = None,
    compliance_status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get registered mobile devices"""
    service = MobileDeviceService(db, user.org_id, user.id)
    return service.get_registered_devices(user_id, compliance_status)


@router.get("/ac19/logs")
def get_mobile_device_access_logs(
    device_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get mobile device access logs"""
    service = MobileDeviceService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_access_logs(device_id, user_id, limit, start, end)


# ============================================================================
# AC-20: Use of External Systems
# ============================================================================

class ExternalSystemRequest(BaseModel):
    system_name: str
    system_type: str
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    connection_method: Optional[str] = None
    data_types_accessed: Optional[List[str]] = None
    data_classification: str = "INTERNAL"
    vendor_name: Optional[str] = None
    vendor_contact: Optional[str] = None
    business_justification: Optional[str] = None


class SecurityAssessmentRequest(BaseModel):
    system_id: int
    assessment_result: str
    assessment_notes: Optional[str] = None
    has_baa: Optional[bool] = None
    baa_expires_at: Optional[str] = None
    has_soc2: Optional[bool] = None
    soc2_report_date: Optional[str] = None
    fedramp_authorized: Optional[bool] = None


@router.post("/ac20/systems", status_code=status.HTTP_201_CREATED)
def request_external_system(
    request: ExternalSystemRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Request connection to an external system"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    return service.request_external_system(**request.dict())


@router.post("/ac20/systems/{system_id}/assess")
def perform_security_assessment(
    system_id: int,
    assessment: SecurityAssessmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Perform security assessment of external system"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    
    baa_expires = None
    if assessment.baa_expires_at:
        baa_expires = datetime.fromisoformat(assessment.baa_expires_at.replace('Z', '+00:00'))
    
    soc2_date = None
    if assessment.soc2_report_date:
        soc2_date = datetime.fromisoformat(assessment.soc2_report_date.replace('Z', '+00:00'))
    
    return service.perform_security_assessment(
        system_id,
        user.id,
        assessment.assessment_result,
        assessment.assessment_notes,
        assessment.has_baa,
        baa_expires,
        assessment.has_soc2,
        soc2_date,
        assessment.fedramp_authorized,
    )


@router.post("/ac20/systems/{system_id}/approve")
def approve_external_system(
    system_id: int,
    review_frequency_days: int = 365,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Approve external system connection"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    return service.approve_system(system_id, user.id, review_frequency_days)


@router.post("/ac20/systems/{system_id}/activate")
def activate_external_system(
    system_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Activate an approved external system"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    return service.activate_system(system_id)


@router.get("/ac20/systems")
def get_active_external_systems(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get all active external systems"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    return service.get_active_systems()


@router.get("/ac20/pending-reviews")
def get_pending_external_system_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get external systems pending review"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    return service.get_pending_reviews()


@router.get("/ac20/logs")
def get_external_system_connection_logs(
    system_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get external system connection logs"""
    service = ExternalSystemsService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_connection_logs(system_id, user_id, limit, start, end)


# ============================================================================
# AC-22: Publicly Accessible Content
# ============================================================================

class PublicContentCreate(BaseModel):
    content_name: str
    content_type: str
    url: str
    data_classification: str = "PUBLIC"
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    contains_phi: bool = False
    contains_pii: bool = False
    contains_sensitive_data: bool = False
    review_frequency_days: int = 90


class ContentReviewRequest(BaseModel):
    content_id: int
    approved: bool
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


@router.post("/ac22/content", status_code=status.HTTP_201_CREATED)
def create_public_content(
    content: PublicContentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Create new publicly accessible content"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.create_content(**content.dict())


@router.post("/ac22/content/{content_id}/submit")
def submit_content_for_review(
    content_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Submit content for review"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.submit_for_review(content_id)


@router.post("/ac22/content/{content_id}/review")
def review_public_content(
    content_id: int,
    review: ContentReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Review publicly accessible content"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.review_content(
        content_id,
        user.id,
        review.approved,
        review.approval_notes,
        review.rejection_reason,
    )


@router.post("/ac22/content/{content_id}/publish")
def publish_content(
    content_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Publish approved content"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.publish_content(content_id)


@router.post("/ac22/content/{content_id}/archive")
def archive_content(
    content_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Archive published content"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.archive_content(content_id)


@router.get("/ac22/content")
def get_published_content(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    """Get all published content"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.get_published_content()


@router.get("/ac22/pending-reviews")
def get_pending_content_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get content pending review"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.get_pending_reviews()


@router.get("/ac22/due-for-review")
def get_content_due_for_review(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get published content due for review"""
    service = PublicContentService(db, user.org_id, user.id)
    return service.get_content_due_for_review()


@router.get("/ac22/logs")
def get_public_content_access_logs(
    content_id: Optional[int] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ip_address: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Get public content access logs"""
    service = PublicContentService(db, user.org_id, user.id)
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    return service.get_access_logs(content_id, limit, start, end, ip_address)
