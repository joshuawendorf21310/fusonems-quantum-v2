"""
Device Identification Service for FedRAMP IA-3 Compliance

FedRAMP Requirement IA-3: Device Identification
- Device fingerprinting
- Device registration
- Trusted device management
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.device_auth import (
    DeviceIdentification,
    DeviceType,
    DeviceStatus,
)
from models.user import User


class DeviceIdentificationService:
    """
    Service for device identification and fingerprinting (IA-3).
    """
    
    @staticmethod
    def generate_device_fingerprint(
        user_agent: Optional[str] = None,
        hardware_info: Optional[Dict] = None,
        software_info: Optional[Dict] = None,
        network_info: Optional[Dict] = None,
    ) -> str:
        """
        Generate a unique device fingerprint.
        
        Args:
            user_agent: User agent string
            hardware_info: Hardware characteristics
            software_info: Software/OS information
            network_info: Network information
            
        Returns:
            SHA-256 hash fingerprint
        """
        fingerprint_data = {
            'user_agent': user_agent or '',
            'hardware': hardware_info or {},
            'software': software_info or {},
            'network': network_info or {},
        }
        
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_json.encode()).hexdigest()
        
        return fingerprint
    
    @staticmethod
    def identify_or_register_device(
        db: Session,
        org_id: int,
        device_fingerprint: str,
        user_id: Optional[int] = None,
        device_type: DeviceType = DeviceType.UNKNOWN,
        device_name: Optional[str] = None,
        hardware_info: Optional[Dict] = None,
        software_info: Optional[Dict] = None,
        network_info: Optional[Dict] = None,
        request: Optional[Request] = None,
    ) -> DeviceIdentification:
        """
        Identify an existing device or register a new one.
        
        Args:
            db: Database session
            org_id: Organization ID
            device_fingerprint: Device fingerprint
            user_id: User ID (optional)
            device_type: Type of device
            device_name: User-friendly name
            hardware_info: Hardware characteristics
            software_info: Software/OS information
            network_info: Network information
            request: HTTP request (optional)
            
        Returns:
            DeviceIdentification record
        """
        # Try to find existing device
        device = db.query(DeviceIdentification).filter(
            DeviceIdentification.device_fingerprint == device_fingerprint,
            DeviceIdentification.org_id == org_id,
        ).first()
        
        if device:
            # Update last seen
            device.last_seen_at = datetime.now(timezone.utc)
            device.access_count += 1
            if user_id:
                device.user_id = user_id
            
            # Update information if provided
            if hardware_info:
                device.hardware_info = hardware_info
            if software_info:
                device.software_info = software_info
            if network_info:
                device.network_info = network_info
            
            db.commit()
            db.refresh(device)
            
            logger.debug(f"Device identified: {device_fingerprint} (existing)")
            
            return device
        
        # Register new device
        device = DeviceIdentification(
            org_id=org_id,
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            device_type=device_type.value,
            device_name=device_name,
            hardware_info=hardware_info,
            software_info=software_info,
            network_info=network_info,
            status=DeviceStatus.PENDING.value,
            registered_at=datetime.now(timezone.utc),
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            access_count=1,
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        logger.info(f"Device registered: {device_fingerprint} (org_id={org_id})")
        
        return device
    
    @staticmethod
    def mark_device_trusted(
        db: Session,
        device_id: str,
        org_id: int,
        trust_level: int = 100,
        trust_reason: Optional[str] = None,
    ) -> DeviceIdentification:
        """Mark a device as trusted"""
        device = db.query(DeviceIdentification).filter(
            DeviceIdentification.id == device_id,
            DeviceIdentification.org_id == org_id,
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.is_trusted = True
        device.trust_level = trust_level
        device.trust_reason = trust_reason
        device.status = DeviceStatus.ACTIVE.value
        
        db.commit()
        db.refresh(device)
        
        logger.info(f"Device marked as trusted: {device_id} (trust_level={trust_level})")
        
        return device
    
    @staticmethod
    def mark_device_untrusted(
        db: Session,
        device_id: str,
        org_id: int,
        reason: Optional[str] = None,
    ) -> DeviceIdentification:
        """Mark a device as untrusted"""
        device = db.query(DeviceIdentification).filter(
            DeviceIdentification.id == device_id,
            DeviceIdentification.org_id == org_id,
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.is_trusted = False
        device.trust_level = 0
        device.trust_reason = reason
        device.status = DeviceStatus.SUSPENDED.value
        
        db.commit()
        db.refresh(device)
        
        logger.warning(f"Device marked as untrusted: {device_id} (reason: {reason})")
        
        return device
    
    @staticmethod
    def is_device_trusted(
        db: Session,
        device_fingerprint: str,
        org_id: int,
    ) -> bool:
        """Check if a device is trusted"""
        device = db.query(DeviceIdentification).filter(
            DeviceIdentification.device_fingerprint == device_fingerprint,
            DeviceIdentification.org_id == org_id,
        ).first()
        
        if not device:
            return False
        
        return device.is_trusted and device.status == DeviceStatus.ACTIVE.value
    
    @staticmethod
    def get_user_devices(
        db: Session,
        user_id: int,
        org_id: int,
        trusted_only: bool = False,
    ) -> List[DeviceIdentification]:
        """Get all devices for a user"""
        query = db.query(DeviceIdentification).filter(
            DeviceIdentification.user_id == user_id,
            DeviceIdentification.org_id == org_id,
        )
        
        if trusted_only:
            query = query.filter(DeviceIdentification.is_trusted == True)
        
        return query.order_by(desc(DeviceIdentification.last_seen_at)).all()
    
    @staticmethod
    def extract_device_info_from_request(request: Request) -> Dict:
        """Extract device information from HTTP request"""
        user_agent = request.headers.get("user-agent", "")
        
        # Extract hardware/software info from user agent (simplified)
        hardware_info = {}
        software_info = {
            'user_agent': user_agent,
        }
        
        network_info = {
            'ip_address': request.client.host if request.client else None,
        }
        
        return {
            'user_agent': user_agent,
            'hardware_info': hardware_info,
            'software_info': software_info,
            'network_info': network_info,
        }
