"""
Multi-Factor Authentication Router
FedRAMP Control: IA-2(1), IA-2(2), IA-2(8), IA-2(11)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.mfa import MFADevice
from services.auth.mfa_service import MFAService
from services.audit.comprehensive_audit_service import ComprehensiveAuditService
from core.logger import logger


router = APIRouter(prefix="/api/auth/mfa", tags=["Multi-Factor Authentication"])


class EnrollMFARequest(BaseModel):
    device_name: str
    device_type: str = "totp"  # totp, webauthn, hardware


class VerifyEnrollmentRequest(BaseModel):
    device_id: int
    verification_code: str


class VerifyMFARequest(BaseModel):
    code: str
    device_id: Optional[int] = None  # If not provided, tries all active devices


class VerifyBackupCodeRequest(BaseModel):
    backup_code: str


@router.post("/enroll")
def enroll_mfa_device(
    request: EnrollMFARequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Enroll a new MFA device (IA-2(1))
    Returns QR code for TOTP setup
    """
    mfa_service = MFAService(db)
    audit_service = ComprehensiveAuditService(db)
    
    try:
        device, secret, qr_code = mfa_service.enroll_mfa_device(
            user=user,
            device_name=request.device_name,
            device_type=request.device_type
        )
        
        # Audit log
        audit_service.log_security_event(
            user=user,
            action="mfa_device_enrolled",
            resource=f"mfa_device:{device.id}",
            outcome="success",
            details={"device_name": request.device_name, "device_type": request.device_type},
            ip_address=http_request.client.host if http_request and http_request.client else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return {
            "device_id": device.id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "secret": secret,  # Show only once
            "qr_code": qr_code,  # Base64 encoded PNG
            "message": "Scan QR code with your authenticator app, then verify with a code"
        }
    
    except Exception as e:
        logger.error(f"MFA enrollment failed for user {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA enrollment failed"
        )


@router.post("/verify-enrollment")
def verify_enrollment(
    request: VerifyEnrollmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Verify and activate MFA device enrollment
    User must provide a valid TOTP code to confirm setup
    """
    mfa_service = MFAService(db)
    audit_service = ComprehensiveAuditService(db)
    
    # Get device
    device = db.query(MFADevice).filter(
        MFADevice.id == request.device_id,
        MFADevice.user_id == user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if device.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device already activated"
        )
    
    # Decrypt secret for verification
    secret = mfa_service._decrypt_secret(device.secret_encrypted)
    
    # Verify code
    success = mfa_service.verify_and_activate_device(
        device=device,
        secret=secret,
        verification_code=request.verification_code
    )
    
    # Audit log
    audit_service.log_security_event(
        user=user,
        action="mfa_device_verified",
        resource=f"mfa_device:{device.id}",
        outcome="success" if success else "failure",
        details={"device_name": device.device_name},
        ip_address=http_request.client.host if http_request and http_request.client else None,
        user_agent=http_request.headers.get("user-agent") if http_request else None
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    return {
        "status": "activated",
        "device_id": device.id,
        "device_name": device.device_name,
        "message": "MFA device successfully activated"
    }


@router.post("/verify")
def verify_mfa_code(
    request: VerifyMFARequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Verify MFA code during login or privileged operation
    IA-2(1): Implements MFA for privileged users
    """
    mfa_service = MFAService(db)
    audit_service = ComprehensiveAuditService(db)
    
    # Get active devices
    devices = mfa_service.get_active_devices(user)
    
    if not devices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active MFA devices"
        )
    
    # Try specific device or all devices
    devices_to_try = [d for d in devices if d.id == request.device_id] if request.device_id else devices
    
    for device in devices_to_try:
        secret = mfa_service._decrypt_secret(device.secret_encrypted)
        if mfa_service.verify_totp_code(secret, request.code):
            # Update last used
            device.last_used_at = datetime.now(timezone.utc)
            if http_request and http_request.client:
                device.last_ip = http_request.client.host
            db.commit()
            
            # Log attempt
            audit_service.log_authentication_event(
                user=user,
                action="mfa_verification",
                outcome="success",
                details={"device_id": device.id, "device_type": device.device_type},
                ip_address=http_request.client.host if http_request and http_request.client else None
            )
            
            return {
                "verified": True,
                "device_id": device.id,
                "device_name": device.device_name
            }
    
    # All verifications failed
    audit_service.log_authentication_event(
        user=user,
        action="mfa_verification",
        outcome="failure",
        details={"reason": "invalid_code"},
        ip_address=http_request.client.host if http_request and http_request.client else None
    )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid MFA code"
    )


@router.post("/generate-backup-codes")
def generate_backup_codes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Generate backup codes for account recovery
    IA-5: Alternative authentication mechanism
    """
    mfa_service = MFAService(db)
    audit_service = ComprehensiveAuditService(db)
    
    # Verify user has MFA enabled
    if not mfa_service.is_mfa_enrolled(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA must be enrolled before generating backup codes"
        )
    
    # Generate codes
    codes = mfa_service.generate_backup_codes(user, count=10)
    
    # Audit log
    audit_service.log_security_event(
        user=user,
        action="backup_codes_generated",
        resource="mfa_backup_codes",
        outcome="success",
        details={"count": len(codes)},
        ip_address=http_request.client.host if http_request and http_request.client else None
    )
    
    return {
        "backup_codes": codes,
        "message": "Save these codes securely. Each can only be used once.",
        "warning": "These codes will not be shown again"
    }


@router.get("/devices")
def list_mfa_devices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all MFA devices for current user"""
    mfa_service = MFAService(db)
    devices = mfa_service.get_active_devices(user)
    
    return {
        "devices": [
            {
                "id": d.id,
                "name": d.device_name,
                "type": d.device_type,
                "enrolled_at": d.enrolled_at.isoformat(),
                "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
                "is_active": d.is_active
            }
            for d in devices
        ],
        "mfa_required": mfa_service.is_mfa_required(user),
        "mfa_enrolled": mfa_service.is_mfa_enrolled(user)
    }


@router.delete("/devices/{device_id}")
def disable_mfa_device(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    http_request: Request = None
):
    """Disable an MFA device"""
    mfa_service = MFAService(db)
    audit_service = ComprehensiveAuditService(db)
    
    success = mfa_service.disable_device(device_id, user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Audit log
    audit_service.log_security_event(
        user=user,
        action="mfa_device_disabled",
        resource=f"mfa_device:{device_id}",
        outcome="success",
        ip_address=http_request.client.host if http_request and http_request.client else None
    )
    
    return {"message": "MFA device disabled"}


@router.get("/status")
def get_mfa_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get MFA status for current user"""
    mfa_service = MFAService(db)
    
    return {
        "mfa_required": mfa_service.is_mfa_required(user),
        "mfa_enrolled": mfa_service.is_mfa_enrolled(user),
        "device_count": len(mfa_service.get_active_devices(user)),
        "user_role": user.role,
        "environment": settings.ENV
    }
