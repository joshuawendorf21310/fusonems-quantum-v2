"""
AC-18: Wireless Access Service

Implements wireless policy enforcement, device authentication, and encryption
requirements for FedRAMP AC-18 compliance.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.access_control import (
    WirelessNetworkPolicy,
    WirelessDevice,
    WirelessConnectionLog,
    WirelessSecurityStandard,
    WirelessDeviceStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from utils.logger import logger


class WirelessAccessService:
    """Service for managing wireless network access and devices"""
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def create_policy(
        self,
        policy_name: str,
        minimum_security_standard: str = WirelessSecurityStandard.WPA2.value,
        requires_encryption: bool = True,
        requires_authentication: bool = True,
        requires_certificate: bool = False,
        requires_device_registration: bool = True,
        description: Optional[str] = None,
        ssid: Optional[str] = None,
        allowed_device_types: Optional[List[str]] = None,
        network_segment: Optional[str] = None,
        allows_internet_access: bool = False,
        allows_internal_access: bool = True,
    ) -> WirelessNetworkPolicy:
        """
        Create a wireless network policy.
        
        Args:
            policy_name: Name of the policy
            minimum_security_standard: Minimum security standard (WPA2, WPA3)
            requires_encryption: Whether encryption is required
            requires_authentication: Whether authentication is required
            requires_certificate: Whether certificate is required
            requires_device_registration: Whether device registration is required
            description: Optional description
            ssid: Network SSID
            allowed_device_types: List of allowed device types
            network_segment: Network segment (guest, internal, management)
            allows_internet_access: Whether internet access is allowed
            allows_internal_access: Whether internal access is allowed
        
        Returns:
            Created WirelessNetworkPolicy
        """
        policy = WirelessNetworkPolicy(
            org_id=self.org_id,
            policy_name=policy_name,
            description=description,
            ssid=ssid,
            minimum_security_standard=minimum_security_standard,
            requires_encryption=requires_encryption,
            requires_authentication=requires_authentication,
            requires_certificate=requires_certificate,
            requires_device_registration=requires_device_registration,
            allowed_device_types=allowed_device_types or [],
            network_segment=network_segment,
            allows_internet_access=allows_internet_access,
            allows_internal_access=allows_internal_access,
            is_active=True,
            created_by=self.user_id,
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        # Audit log
        self._audit_log(
            action="create_wireless_policy",
            resource_type="wireless_network_policy",
            resource_id=str(policy.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"policy_name": policy_name}
        )
        
        logger.info(f"Created wireless network policy: {policy_name}")
        return policy
    
    def register_device(
        self,
        device_name: str,
        mac_address: str,
        device_type: str,
        user_id: Optional[int] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        policy_id: Optional[int] = None,
        encryption_support: Optional[List[str]] = None,
        certificate_installed: bool = False,
        certificate_expires_at: Optional[datetime] = None,
    ) -> WirelessDevice:
        """
        Register a wireless device.
        
        Args:
            device_name: Name of the device
            mac_address: MAC address (format: XX:XX:XX:XX:XX:XX)
            device_type: Type of device
            user_id: Associated user ID
            manufacturer: Device manufacturer
            model: Device model
            serial_number: Serial number
            policy_id: Policy ID
            encryption_support: List of supported encryption standards
            certificate_installed: Whether certificate is installed
            certificate_expires_at: Certificate expiration date
        
        Returns:
            Created WirelessDevice
        """
        device = WirelessDevice(
            org_id=self.org_id,
            user_id=user_id,
            policy_id=policy_id,
            device_name=device_name,
            mac_address=mac_address.upper(),  # Normalize to uppercase
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            encryption_support=encryption_support or [],
            certificate_installed=certificate_installed,
            certificate_expires_at=certificate_expires_at,
            status=WirelessDeviceStatus.REGISTERED.value,
            registered_by=self.user_id,
            registered_at=datetime.now(timezone.utc),
        )
        
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="register_wireless_device",
            resource_type="wireless_device",
            resource_id=str(device.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "device_name": device_name,
                "mac_address": mac_address,
                "device_type": device_type,
            }
        )
        
        logger.info(f"Registered wireless device: {device_name} ({mac_address})")
        return device
    
    def approve_device(self, device_id: int, approved_by: int) -> WirelessDevice:
        """Approve a wireless device registration"""
        device = self.db.query(WirelessDevice).filter(
            and_(
                WirelessDevice.id == device_id,
                WirelessDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.status = WirelessDeviceStatus.ACTIVE.value
        device.approved_by = approved_by
        
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="approve_wireless_device",
            resource_type="wireless_device",
            resource_id=str(device_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"approved_by": approved_by}
        )
        
        return device
    
    def check_device_compliance(
        self,
        device_id: int,
        security_standard_used: Optional[str] = None,
        encryption_enabled: Optional[bool] = None,
        certificate_installed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Check if a device complies with policy requirements.
        
        Returns:
            Dict with 'compliant' and 'issues' list
        """
        device = self.db.query(WirelessDevice).filter(
            and_(
                WirelessDevice.id == device_id,
                WirelessDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        policy = self.db.query(WirelessNetworkPolicy).filter(
            WirelessNetworkPolicy.id == device.policy_id
        ).first() if device.policy_id else None
        
        if not policy:
            return {"compliant": True, "issues": []}
        
        issues = []
        
        # Check security standard
        if policy.minimum_security_standard and security_standard_used:
            standard_order = {
                WirelessSecurityStandard.WEP.value: 1,
                WirelessSecurityStandard.WPA.value: 2,
                WirelessSecurityStandard.WPA2.value: 3,
                WirelessSecurityStandard.WPA3.value: 4,
            }
            min_level = standard_order.get(policy.minimum_security_standard, 0)
            used_level = standard_order.get(security_standard_used, 0)
            
            if used_level < min_level:
                issues.append("security_standard_below_minimum")
        
        # Check encryption
        if policy.requires_encryption and not (encryption_enabled or device.encryption_support):
            issues.append("encryption_required")
        
        # Check certificate
        if policy.requires_certificate and not (certificate_installed or device.certificate_installed):
            issues.append("certificate_required")
        
        # Check device registration
        if policy.requires_device_registration and device.status != WirelessDeviceStatus.ACTIVE.value:
            issues.append("device_not_registered")
        
        # Check device type
        if policy.allowed_device_types and device.device_type not in policy.allowed_device_types:
            issues.append("device_type_not_allowed")
        
        compliant = len(issues) == 0
        
        # Update device compliance status
        device.last_seen_at = datetime.now(timezone.utc)
        if issues:
            device.compliance_issues = issues
        
        self.db.commit()
        
        return {"compliant": compliant, "issues": issues}
    
    def log_connection(
        self,
        mac_address: str,
        ssid: Optional[str] = None,
        ip_address: Optional[str] = None,
        security_standard_used: Optional[str] = None,
        encryption_enabled: Optional[bool] = None,
        authentication_method: Optional[str] = None,
        connected: bool = True,
        device_id: Optional[int] = None,
        policy_id: Optional[int] = None,
        connection_duration_seconds: Optional[int] = None,
        bytes_sent: int = 0,
        bytes_received: int = 0,
    ) -> WirelessConnectionLog:
        """
        Log a wireless network connection.
        
        Args:
            mac_address: Device MAC address
            ssid: Network SSID
            ip_address: Assigned IP address
            security_standard_used: Security standard used
            encryption_enabled: Whether encryption was enabled
            authentication_method: Authentication method used
            connected: Whether connection was successful
            device_id: Device ID (if registered)
            policy_id: Policy ID
            connection_duration_seconds: Connection duration
            bytes_sent: Bytes sent
            bytes_received: Bytes received
        
        Returns:
            Created WirelessConnectionLog
        """
        # Try to find device by MAC address
        if not device_id:
            device = self.db.query(WirelessDevice).filter(
                and_(
                    WirelessDevice.mac_address == mac_address.upper(),
                    WirelessDevice.org_id == self.org_id,
                )
            ).first()
            if device:
                device_id = device.id
                policy_id = device.policy_id
        
        log = WirelessConnectionLog(
            org_id=self.org_id,
            device_id=device_id,
            policy_id=policy_id,
            timestamp=datetime.now(timezone.utc),
            ssid=ssid,
            mac_address=mac_address.upper(),
            ip_address=ip_address,
            security_standard_used=security_standard_used,
            encryption_enabled=encryption_enabled,
            authentication_method=authentication_method,
            connected=connected,
            connection_duration_seconds=connection_duration_seconds,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        # Audit log
        self._audit_log(
            action="log_wireless_connection",
            resource_type="wireless_connection",
            resource_id=str(log.id),
            outcome=AuditOutcome.SUCCESS if connected else AuditOutcome.FAILURE,
            metadata={
                "mac_address": mac_address,
                "ssid": ssid,
                "connected": connected,
            }
        )
        
        return log
    
    def suspend_device(self, device_id: int, reason: Optional[str] = None) -> WirelessDevice:
        """Suspend a wireless device"""
        device = self.db.query(WirelessDevice).filter(
            and_(
                WirelessDevice.id == device_id,
                WirelessDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.status = WirelessDeviceStatus.SUSPENDED.value
        device.suspended_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="suspend_wireless_device",
            resource_type="wireless_device",
            resource_id=str(device_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"reason": reason}
        )
        
        return device
    
    def revoke_device(self, device_id: int, reason: Optional[str] = None) -> WirelessDevice:
        """Revoke a wireless device"""
        device = self.db.query(WirelessDevice).filter(
            and_(
                WirelessDevice.id == device_id,
                WirelessDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.status = WirelessDeviceStatus.REVOKED.value
        device.revoked_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="revoke_wireless_device",
            resource_type="wireless_device",
            resource_id=str(device_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"reason": reason}
        )
        
        return device
    
    def get_registered_devices(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[WirelessDevice]:
        """Get registered wireless devices"""
        query = self.db.query(WirelessDevice).filter(
            WirelessDevice.org_id == self.org_id
        )
        
        if user_id:
            query = query.filter(WirelessDevice.user_id == user_id)
        if status:
            query = query.filter(WirelessDevice.status == status)
        
        return query.order_by(desc(WirelessDevice.registered_at)).all()
    
    def get_connection_logs(
        self,
        device_id: Optional[int] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[WirelessConnectionLog]:
        """Get wireless connection logs"""
        query = self.db.query(WirelessConnectionLog).filter(
            WirelessConnectionLog.org_id == self.org_id
        )
        
        if device_id:
            query = query.filter(WirelessConnectionLog.device_id == device_id)
        if start_date:
            query = query.filter(WirelessConnectionLog.timestamp >= start_date)
        if end_date:
            query = query.filter(WirelessConnectionLog.timestamp <= end_date)
        
        return query.order_by(desc(WirelessConnectionLog.timestamp)).limit(limit).all()
    
    def _audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: AuditOutcome,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create audit log entry"""
        audit = ComprehensiveAuditLog(
            org_id=self.org_id,
            user_id=self.user_id,
            event_type=AuditEventType.AUTHORIZATION.value,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome.value,
            metadata=metadata or {},
        )
        self.db.add(audit)
        self.db.commit()
