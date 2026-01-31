"""
Separate Device Authentication Service for FedRAMP IA-2(11) Compliance

FedRAMP Requirement IA-2(11): Remote Access - Separate Device
- Hardware token integration
- Separate device requirement for privileged access
- Device registration and validation
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.device_auth import (
    SeparateDeviceAuth,
    DeviceType,
    DeviceStatus,
)
from models.user import User


class SeparateDeviceAuthService:
    """
    Service for separate device authentication (IA-2(11)).
    """
    
    # Privileged roles that require separate device
    PRIVILEGED_ROLES = ['admin', 'ops_admin', 'founder', 'compliance']
    
    @staticmethod
    def register_device(
        db: Session,
        org_id: int,
        user_id: int,
        device_id: str,
        device_type: DeviceType = DeviceType.HARDWARE_TOKEN,
        device_name: Optional[str] = None,
        device_serial: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        hardware_info: Optional[Dict] = None,
        registered_by_user_id: Optional[int] = None,
        expires_in_days: Optional[int] = None,
    ) -> SeparateDeviceAuth:
        """
        Register a separate device for privileged access.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID
            device_id: Unique device identifier
            device_type: Type of device
            device_name: User-friendly name
            device_serial: Device serial number
            device_fingerprint: Device fingerprint
            hardware_info: Hardware characteristics
            registered_by_user_id: User registering the device
            expires_in_days: Days until expiration (None = no expiration)
            
        Returns:
            Created SeparateDeviceAuth record
        """
        # Check if device already registered
        existing = db.query(SeparateDeviceAuth).filter(
            SeparateDeviceAuth.device_id == device_id,
            SeparateDeviceAuth.org_id == org_id,
        ).first()
        
        if existing and existing.status != DeviceStatus.REVOKED.value:
            raise ValueError(f"Device {device_id} is already registered")
        
        # Generate fingerprint if not provided
        if not device_fingerprint:
            fingerprint_data = f"{device_id}:{device_serial}:{org_id}:{user_id}"
            device_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        device_auth = SeparateDeviceAuth(
            org_id=org_id,
            user_id=user_id,
            device_id=device_id,
            device_type=device_type.value,
            device_name=device_name,
            device_serial=device_serial,
            device_fingerprint=device_fingerprint,
            hardware_info=hardware_info,
            status=DeviceStatus.REGISTERED.value,
            registered_at=datetime.now(timezone.utc),
            registered_by_user_id=registered_by_user_id,
            expires_at=expires_at,
        )
        
        db.add(device_auth)
        db.commit()
        db.refresh(device_auth)
        
        logger.info(
            f"Separate device registered: {device_id} "
            f"(user_id={user_id}, type={device_type.value})"
        )
        
        return device_auth
    
    @staticmethod
    def activate_device(
        db: Session,
        device_id: str,
        org_id: int,
        user_id: int,
    ) -> SeparateDeviceAuth:
        """Activate a registered device"""
        device_auth = db.query(SeparateDeviceAuth).filter(
            SeparateDeviceAuth.device_id == device_id,
            SeparateDeviceAuth.org_id == org_id,
            SeparateDeviceAuth.user_id == user_id,
        ).first()
        
        if not device_auth:
            raise ValueError(f"Device {device_id} not found")
        
        if device_auth.status == DeviceStatus.REVOKED.value:
            raise ValueError(f"Device {device_id} has been revoked")
        
        if device_auth.expires_at and device_auth.expires_at < datetime.now(timezone.utc):
            device_auth.status = DeviceStatus.EXPIRED.value
            db.commit()
            raise ValueError(f"Device {device_id} has expired")
        
        device_auth.status = DeviceStatus.ACTIVE.value
        db.commit()
        db.refresh(device_auth)
        
        return device_auth
    
    @staticmethod
    def verify_device(
        db: Session,
        device_id: str,
        org_id: int,
        user_id: int,
        device_fingerprint: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a separate device for authentication.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        device_auth = db.query(SeparateDeviceAuth).filter(
            SeparateDeviceAuth.device_id == device_id,
            SeparateDeviceAuth.org_id == org_id,
            SeparateDeviceAuth.user_id == user_id,
        ).first()
        
        if not device_auth:
            return False, "Device not registered"
        
        if device_auth.status != DeviceStatus.ACTIVE.value:
            return False, f"Device status is {device_auth.status}"
        
        if device_auth.expires_at and device_auth.expires_at < datetime.now(timezone.utc):
            device_auth.status = DeviceStatus.EXPIRED.value
            db.commit()
            return False, "Device has expired"
        
        # Verify fingerprint if provided
        if device_fingerprint and device_auth.device_fingerprint:
            if device_fingerprint != device_auth.device_fingerprint:
                return False, "Device fingerprint mismatch"
        
        # Update usage
        device_auth.last_used_at = datetime.now(timezone.utc)
        device_auth.usage_count += 1
        db.commit()
        
        return True, None
    
    @staticmethod
    def requires_separate_device(user_role: str) -> bool:
        """Check if a role requires separate device authentication"""
        return user_role.lower() in [r.lower() for r in SeparateDeviceAuthService.PRIVILEGED_ROLES]
    
    @staticmethod
    def revoke_device(
        db: Session,
        device_id: str,
        org_id: int,
        revoked_by_user_id: int,
        revocation_reason: str,
    ) -> SeparateDeviceAuth:
        """Revoke a separate device"""
        device_auth = db.query(SeparateDeviceAuth).filter(
            SeparateDeviceAuth.device_id == device_id,
            SeparateDeviceAuth.org_id == org_id,
        ).first()
        
        if not device_auth:
            raise ValueError(f"Device {device_id} not found")
        
        device_auth.status = DeviceStatus.REVOKED.value
        device_auth.revoked_at = datetime.now(timezone.utc)
        device_auth.revoked_by_user_id = revoked_by_user_id
        device_auth.revocation_reason = revocation_reason
        
        db.commit()
        db.refresh(device_auth)
        
        logger.warning(
            f"Separate device revoked: {device_id} "
            f"(reason: {revocation_reason})"
        )
        
        return device_auth
    
    @staticmethod
    def get_user_devices(
        db: Session,
        user_id: int,
        org_id: int,
        status: Optional[str] = None,
    ) -> List[SeparateDeviceAuth]:
        """Get all devices for a user"""
        query = db.query(SeparateDeviceAuth).filter(
            SeparateDeviceAuth.user_id == user_id,
            SeparateDeviceAuth.org_id == org_id,
        )
        
        if status:
            query = query.filter(SeparateDeviceAuth.status == status)
        
        return query.order_by(desc(SeparateDeviceAuth.registered_at)).all()
