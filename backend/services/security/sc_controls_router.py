"""
API Router for System Protection (SC) FedRAMP Controls.

Provides endpoints for:
- SC-8(1): Transmission Protection
- SC-15: Collaborative Computing
- SC-17: Public Key Infrastructure
- SC-20: Secure Name Resolution
- SC-28(1): Data at Rest
- SC-39: Process Isolation
- SC-10, SC-18, SC-19, SC-24: Additional SC Controls
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user, require_roles
from models.user import User

from services.security.transmission_protection_service import (
    TransmissionProtectionService,
    ConnectionSecurityLevel
)
from services.security.collaboration_security_service import (
    CollaborationSecurityService,
    SessionPermission
)
from services.security.pki_service import PKIService, CertificateType, KeyAlgorithm
from services.security.dns_security_service import DNSSecurityService, DNSQueryType
from services.security.encryption_at_rest import EncryptionAtRestService
from services.security.process_isolation_service import (
    ProcessIsolationService,
    IsolationLevel
)
from services.security.sc_controls_service import SCControlsService, SystemState

router = APIRouter(prefix="/api/security/sc", tags=["System Protection (SC) Controls"])


# SC-8(1): Transmission Protection
@router.post("/transmission/verify")
async def verify_tls_connection(
    hostname: str,
    port: int = 443,
    require_tls_1_3: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Verify TLS connection security (SC-8(1))."""
    service = TransmissionProtectionService(db)
    security_level, cert_info, error = service.verify_tls_connection(
        hostname, port, require_tls_1_3=require_tls_1_3
    )
    
    return {
        "hostname": hostname,
        "port": port,
        "security_level": security_level.value,
        "certificate": {
            "subject": cert_info.subject if cert_info else None,
            "issuer": cert_info.issuer if cert_info else None,
            "valid_until": cert_info.not_after.isoformat() if cert_info else None,
            "days_until_expiry": cert_info.days_until_expiry if cert_info else None
        } if cert_info else None,
        "error": error
    }


@router.get("/transmission/statistics")
async def get_transmission_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get transmission security statistics."""
    service = TransmissionProtectionService(db)
    return service.get_connection_statistics(start_date, end_date)


@router.get("/transmission/certificates/expiring")
async def get_expiring_certificates(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get certificates expiring within specified days."""
    service = TransmissionProtectionService(db)
    expiring = service.check_certificate_expiry(days_ahead)
    
    return {
        "count": len(expiring),
        "certificates": [
            {
                "hostname": cert.hostname,
                "port": cert.port,
                "not_after": cert.not_after.isoformat(),
                "days_until_expiry": (cert.not_after - datetime.utcnow()).days
            }
            for cert in expiring
        ]
    }


# SC-15: Collaborative Computing
@router.post("/collaboration/sessions")
async def create_collaboration_session(
    session_type: str,
    room_name: str,
    org_id: int,
    require_authentication: bool = True,
    require_moderator_approval: bool = True,
    allow_screen_share: bool = True,
    allow_recording: bool = False,
    max_participants: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "user"]))
):
    """Create collaboration session (SC-15)."""
    service = CollaborationSecurityService(db)
    session = service.create_session(
        session_type=session_type,
        room_name=room_name,
        org_id=org_id,
        created_by=current_user.id,
        require_authentication=require_authentication,
        require_moderator_approval=require_moderator_approval,
        allow_screen_share=allow_screen_share,
        allow_recording=allow_recording,
        max_participants=max_participants
    )
    
    return {
        "session_id": session.session_id,
        "room_name": session.room_name,
        "status": session.status,
        "max_participants": session.max_participants
    }


@router.post("/collaboration/sessions/{session_id}/participants")
async def add_participant(
    session_id: int,
    user_id: int,
    participant_id: str,
    is_moderator: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "user"]))
):
    """Add participant to collaboration session."""
    service = CollaborationSecurityService(db)
    participant = service.add_participant(
        session_id=session_id,
        user_id=user_id,
        participant_id=participant_id,
        is_moderator=is_moderator,
        ip_address=None,  # Would get from request
        user_agent=None  # Would get from request
    )
    
    return {
        "participant_id": participant.participant_id,
        "is_moderator": participant.is_moderator,
        "can_screen_share": participant.can_screen_share,
        "can_record": participant.can_record
    }


@router.get("/collaboration/sessions/{session_id}/statistics")
async def get_session_statistics(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "user"]))
):
    """Get collaboration session statistics."""
    service = CollaborationSecurityService(db)
    return service.get_session_statistics(session_id)


# SC-17: Public Key Infrastructure
@router.post("/pki/certificates")
async def store_certificate(
    certificate_pem: str,
    certificate_type: str = "ssl_tls",
    certificate_chain_pem: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Store PKI certificate (SC-17)."""
    service = PKIService(db)
    cert = service.store_certificate(
        certificate_pem=certificate_pem,
        certificate_type=CertificateType(certificate_type),
        certificate_chain_pem=certificate_chain_pem
    )
    
    return {
        "certificate_id": cert.certificate_id,
        "subject": cert.subject,
        "issuer": cert.issuer,
        "not_after": cert.not_after.isoformat(),
        "status": cert.status
    }


@router.post("/pki/certificates/{certificate_id}/check-revocation")
async def check_certificate_revocation(
    certificate_id: str,
    use_ocsp: bool = True,
    use_crl: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Check certificate revocation status."""
    service = PKIService(db)
    is_revoked, reason, ocsp_response = service.check_certificate_revocation(
        certificate_id, use_ocsp, use_crl
    )
    
    return {
        "certificate_id": certificate_id,
        "is_revoked": is_revoked,
        "revocation_reason": reason,
        "ocsp_response": ocsp_response
    }


@router.get("/pki/certificates/expiring")
async def get_expiring_pki_certificates(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get PKI certificates expiring soon."""
    service = PKIService(db)
    expiring = service.get_expiring_certificates(days_ahead)
    
    return {
        "count": len(expiring),
        "certificates": [
            {
                "certificate_id": cert.certificate_id,
                "subject": cert.subject,
                "not_after": cert.not_after.isoformat(),
                "days_until_expiry": (cert.not_after - datetime.utcnow()).days
            }
            for cert in expiring
        ]
    }


# SC-20: Secure Name Resolution
@router.post("/dns/resolve")
async def resolve_with_dnssec(
    hostname: str,
    query_type: str = "A",
    validate_dnssec: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Resolve hostname with DNSSEC validation (SC-20)."""
    service = DNSSecurityService(db)
    addresses, security_level, details = service.resolve_with_dnssec(
        hostname,
        DNSQueryType(query_type),
        validate_dnssec=validate_dnssec
    )
    
    return {
        "hostname": hostname,
        "resolved_addresses": addresses,
        "security_level": security_level.value,
        "dnssec_validated": (security_level.value == "secure"),
        "validation_details": details
    }


@router.get("/dns/statistics")
async def get_dns_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get DNS resolution statistics."""
    service = DNSSecurityService(db)
    return service.get_resolution_statistics(start_date, end_date)


# SC-28(1): Data at Rest
@router.get("/encryption/status")
async def get_encryption_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get database encryption status (SC-28(1))."""
    service = EncryptionAtRestService(db)
    return service.get_database_encryption_status()


@router.post("/encryption/rotate-key")
async def rotate_encryption_key(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Rotate encryption key."""
    service = EncryptionAtRestService(db)
    new_key_id = service.rotate_encryption_key(force=force)
    
    return {
        "new_key_id": new_key_id,
        "rotation_automated": True
    }


@router.post("/encryption/automate-rotation")
async def automate_key_rotation(
    rotation_interval_days: int = 90,
    auto_rotate: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Configure automated key rotation."""
    service = EncryptionAtRestService(db)
    return service.automate_key_rotation(rotation_interval_days, auto_rotate)


# SC-39: Process Isolation
@router.post("/process-isolation/monitor/{process_id}")
async def monitor_process(
    process_id: int,
    check_isolation: bool = True,
    check_resources: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Monitor process isolation (SC-39)."""
    service = ProcessIsolationService(db)
    return service.monitor_process(process_id, check_isolation, check_resources)


@router.get("/process-isolation/statistics")
async def get_isolation_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get process isolation statistics."""
    service = ProcessIsolationService(db)
    return service.get_isolation_statistics(start_date, end_date)


# SC-10: Network Disconnect
@router.post("/network/disconnect")
async def disconnect_network_session(
    connection_id: str,
    reason: Optional[str] = None,
    disconnect_type: str = "manual",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Disconnect network session (SC-10)."""
    service = SCControlsService(db)
    event = service.disconnect_network_session(
        connection_id=connection_id,
        user_id=current_user.id,
        reason=reason,
        disconnect_type=disconnect_type
    )
    
    return {
        "connection_id": connection_id,
        "disconnected_at": event.disconnected_at.isoformat(),
        "reason": event.disconnect_reason
    }


# SC-18: Mobile Code
@router.post("/mobile-code/check")
async def check_mobile_code(
    code_type: str,
    code_source: str,
    code_hash: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "user"]))
):
    """Check mobile code execution (SC-18)."""
    service = SCControlsService(db)
    is_allowed, execution = service.check_mobile_code(
        code_type=code_type,
        code_source=code_source,
        code_hash=code_hash,
        user_id=current_user.id
    )
    
    return {
        "is_allowed": is_allowed,
        "execution_id": execution.execution_id,
        "status": execution.status,
        "reason": execution.allowed_reason or execution.blocked_reason
    }


# SC-19: Voice over IP
@router.post("/voip/sessions")
async def create_voip_session(
    caller_id: str,
    callee_id: str,
    call_direction: str,
    encrypted: bool = True,
    encryption_protocol: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "user"]))
):
    """Create VoIP session (SC-19)."""
    service = SCControlsService(db)
    session = service.create_voip_session(
        caller_id=caller_id,
        callee_id=callee_id,
        call_direction=call_direction,
        encrypted=encrypted,
        encryption_protocol=encryption_protocol
    )
    
    return {
        "session_id": session.session_id,
        "encrypted": session.encrypted,
        "encryption_protocol": session.encryption_protocol
    }


# SC-24: Fail in Known State
@router.post("/system-state/transition")
async def record_state_transition(
    from_state: str,
    to_state: str,
    component: Optional[str] = None,
    transition_reason: Optional[str] = None,
    recovery_actions: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Record system state transition (SC-24)."""
    service = SCControlsService(db)
    transition = service.record_state_transition(
        from_state=SystemState(from_state),
        to_state=SystemState(to_state),
        component=component,
        transition_reason=transition_reason,
        recovery_actions=recovery_actions
    )
    
    return {
        "transition_id": transition.transition_id,
        "from_state": transition.from_state,
        "to_state": transition.to_state,
        "component": transition.component
    }


@router.get("/system-state/history")
async def get_state_history(
    component: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "security_officer"]))
):
    """Get system state transition history."""
    service = SCControlsService(db)
    transitions = service.get_system_state_history(component, limit)
    
    return {
        "count": len(transitions),
        "transitions": [
            {
                "transition_id": t.transition_id,
                "from_state": t.from_state,
                "to_state": t.to_state,
                "component": t.component,
                "created_at": t.created_at.isoformat()
            }
            for t in transitions
        ]
    }
