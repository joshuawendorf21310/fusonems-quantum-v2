"""
AC-19: Mobile Device Access Service

Implements MDM integration, device compliance checking, and remote wipe
capabilities for FedRAMP AC-19 compliance.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.access_control import (
    MobileDevice,
    MobileDeviceAccessLog,
    MobileDeviceWipe,
    MobileDeviceType,
    MobileDeviceComplianceStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome
from utils.logger import logger


class MobileDeviceService:
    """Service for managing mobile device access and compliance"""
    
    def __init__(self, db: Session, org_id: int, user_id: Optional[int] = None):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
    
    def register_device(
        self,
        device_name: str,
        device_type: str,
        os_type: str,
        user_id: Optional[int] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        imei: Optional[str] = None,
        serial_number: Optional[str] = None,
        os_version: Optional[str] = None,
        mdm_device_id: Optional[str] = None,
    ) -> MobileDevice:
        """
        Register a mobile device.
        
        Args:
            device_name: Name of the device
            device_type: Type of device (smartphone, tablet, laptop, wearable)
            os_type: Operating system type (iOS, Android, Windows, etc.)
            user_id: Associated user ID
            manufacturer: Device manufacturer
            model: Device model
            imei: IMEI number
            serial_number: Serial number
            os_version: OS version
            mdm_device_id: MDM device identifier
        
        Returns:
            Created MobileDevice
        """
        device = MobileDevice(
            org_id=self.org_id,
            user_id=user_id,
            device_name=device_name,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            imei=imei,
            serial_number=serial_number,
            os_type=os_type,
            os_version=os_version,
            mdm_device_id=mdm_device_id,
            mdm_enrolled=mdm_device_id is not None,
            compliance_status=MobileDeviceComplianceStatus.PENDING.value,
            registered_by=self.user_id,
            registered_at=datetime.now(timezone.utc),
        )
        
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="register_mobile_device",
            resource_type="mobile_device",
            resource_id=str(device.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "device_name": device_name,
                "device_type": device_type,
                "os_type": os_type,
            }
        )
        
        logger.info(f"Registered mobile device: {device_name} ({device_type})")
        return device
    
    def update_device_compliance(
        self,
        device_id: int,
        encryption_enabled: Optional[bool] = None,
        screen_lock_enabled: Optional[bool] = None,
        biometric_enabled: Optional[bool] = None,
        jailbroken_rooted: Optional[bool] = None,
        mdm_managed: Optional[bool] = None,
        mdm_last_sync: Optional[datetime] = None,
    ) -> MobileDevice:
        """
        Update device compliance information.
        
        Args:
            device_id: Device ID
            encryption_enabled: Whether encryption is enabled
            screen_lock_enabled: Whether screen lock is enabled
            biometric_enabled: Whether biometric authentication is enabled
            jailbroken_rooted: Whether device is jailbroken/rooted
            mdm_managed: Whether device is MDM managed
            mdm_last_sync: Last MDM sync time
        
        Returns:
            Updated MobileDevice
        """
        device = self.db.query(MobileDevice).filter(
            and_(
                MobileDevice.id == device_id,
                MobileDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        if encryption_enabled is not None:
            device.encryption_enabled = encryption_enabled
        if screen_lock_enabled is not None:
            device.screen_lock_enabled = screen_lock_enabled
        if biometric_enabled is not None:
            device.biometric_enabled = biometric_enabled
        if jailbroken_rooted is not None:
            device.jailbroken_rooted = jailbroken_rooted
        if mdm_managed is not None:
            device.mdm_managed = mdm_managed
        if mdm_last_sync is not None:
            device.mdm_last_sync = mdm_last_sync
        
        # Check compliance
        compliance_result = self._check_compliance(device)
        device.compliance_status = compliance_result["status"]
        device.compliance_issues = compliance_result["issues"]
        device.last_compliance_check = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="update_device_compliance",
            resource_type="mobile_device",
            resource_id=str(device_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "compliance_status": device.compliance_status,
                "compliance_issues": device.compliance_issues,
            }
        )
        
        return device
    
    def check_compliance(self, device_id: int) -> Dict[str, Any]:
        """
        Check device compliance status.
        
        Returns:
            Dict with 'status' and 'issues' list
        """
        device = self.db.query(MobileDevice).filter(
            and_(
                MobileDevice.id == device_id,
                MobileDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        return self._check_compliance(device)
    
    def _check_compliance(self, device: MobileDevice) -> Dict[str, Any]:
        """Internal compliance check"""
        issues = []
        
        # Check encryption
        if device.encryption_enabled is False:
            issues.append("encryption_not_enabled")
        
        # Check screen lock
        if device.screen_lock_enabled is False:
            issues.append("screen_lock_not_enabled")
        
        # Check jailbroken/rooted
        if device.jailbroken_rooted is True:
            issues.append("device_jailbroken_rooted")
        
        # Check MDM enrollment (if required)
        # This can be customized based on policy
        
        if len(issues) == 0:
            status = MobileDeviceComplianceStatus.COMPLIANT.value
        else:
            status = MobileDeviceComplianceStatus.NON_COMPLIANT.value
        
        return {
            "status": status,
            "issues": issues,
        }
    
    def log_access(
        self,
        device_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> MobileDeviceAccessLog:
        """
        Log mobile device access.
        
        Args:
            device_id: Device ID
            action: Action performed (login, data_access, api_call, etc.)
            resource_type: Type of resource accessed
            resource_id: Resource ID
            ip_address: IP address
            user_agent: User agent string
            location: Location information
            success: Whether access was successful
            failure_reason: Reason for failure if unsuccessful
            user_id: User ID
        
        Returns:
            Created MobileDeviceAccessLog
        """
        log = MobileDeviceAccessLog(
            org_id=self.org_id,
            device_id=device_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            success=success,
            failure_reason=failure_reason,
        )
        
        self.db.add(log)
        
        # Update device last seen
        device = self.db.query(MobileDevice).filter(MobileDevice.id == device_id).first()
        if device:
            device.last_seen_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(log)
        
        # Audit log
        self._audit_log(
            action="log_mobile_device_access",
            resource_type="mobile_device_access",
            resource_id=str(log.id),
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            metadata={
                "device_id": device_id,
                "action": action,
                "success": success,
            }
        )
        
        return log
    
    def initiate_wipe(
        self,
        device_id: int,
        wipe_type: str,
        reason: str,
        initiated_by: int,
        approved_by: Optional[int] = None,
    ) -> MobileDeviceWipe:
        """
        Initiate a remote wipe operation.
        
        Args:
            device_id: Device ID
            wipe_type: Type of wipe (full, selective, account_only)
            reason: Reason for wipe
            initiated_by: User initiating the wipe
            approved_by: User approving the wipe (optional)
        
        Returns:
            Created MobileDeviceWipe
        """
        wipe = MobileDeviceWipe(
            org_id=self.org_id,
            device_id=device_id,
            wipe_type=wipe_type,
            reason=reason,
            initiated_by=initiated_by,
            approved_by=approved_by,
            status="pending" if approved_by is None else "in_progress",
            initiated_at=datetime.now(timezone.utc),
        )
        
        self.db.add(wipe)
        self.db.commit()
        self.db.refresh(wipe)
        
        # Audit log
        self._audit_log(
            action="initiate_mobile_device_wipe",
            resource_type="mobile_device_wipe",
            resource_id=str(wipe.id),
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "device_id": device_id,
                "wipe_type": wipe_type,
                "reason": reason,
            }
        )
        
        logger.warning(f"Mobile device wipe initiated: device {device_id}, type: {wipe_type}")
        return wipe
    
    def complete_wipe(
        self,
        wipe_id: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> MobileDeviceWipe:
        """
        Complete a remote wipe operation.
        
        Args:
            wipe_id: Wipe operation ID
            success: Whether wipe was successful
            error_message: Error message if failed
        
        Returns:
            Updated MobileDeviceWipe
        """
        wipe = self.db.query(MobileDeviceWipe).filter(
            and_(
                MobileDeviceWipe.id == wipe_id,
                MobileDeviceWipe.org_id == self.org_id,
            )
        ).first()
        
        if not wipe:
            raise ValueError(f"Wipe operation {wipe_id} not found")
        
        wipe.status = "completed" if success else "failed"
        wipe.completed_at = datetime.now(timezone.utc)
        wipe.success = success
        wipe.error_message = error_message
        
        # If successful, revoke device
        if success:
            device = self.db.query(MobileDevice).filter(MobileDevice.id == wipe.device_id).first()
            if device:
                device.revoked_at = datetime.now(timezone.utc)
                device.is_active = False
        
        self.db.commit()
        self.db.refresh(wipe)
        
        # Audit log
        self._audit_log(
            action="complete_mobile_device_wipe",
            resource_type="mobile_device_wipe",
            resource_id=str(wipe_id),
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            metadata={
                "success": success,
                "error_message": error_message,
            }
        )
        
        return wipe
    
    def get_registered_devices(
        self,
        user_id: Optional[int] = None,
        compliance_status: Optional[str] = None,
    ) -> List[MobileDevice]:
        """Get registered mobile devices"""
        query = self.db.query(MobileDevice).filter(
            and_(
                MobileDevice.org_id == self.org_id,
                MobileDevice.is_active == True,
            )
        )
        
        if user_id:
            query = query.filter(MobileDevice.user_id == user_id)
        if compliance_status:
            query = query.filter(MobileDevice.compliance_status == compliance_status)
        
        return query.order_by(desc(MobileDevice.registered_at)).all()
    
    def get_access_logs(
        self,
        device_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MobileDeviceAccessLog]:
        """Get mobile device access logs"""
        query = self.db.query(MobileDeviceAccessLog).filter(
            MobileDeviceAccessLog.org_id == self.org_id
        )
        
        if device_id:
            query = query.filter(MobileDeviceAccessLog.device_id == device_id)
        if user_id:
            query = query.filter(MobileDeviceAccessLog.user_id == user_id)
        if start_date:
            query = query.filter(MobileDeviceAccessLog.timestamp >= start_date)
        if end_date:
            query = query.filter(MobileDeviceAccessLog.timestamp <= end_date)
        
        return query.order_by(desc(MobileDeviceAccessLog.timestamp)).limit(limit).all()
    
    def revoke_device(self, device_id: int, reason: Optional[str] = None) -> MobileDevice:
        """Revoke a mobile device"""
        device = self.db.query(MobileDevice).filter(
            and_(
                MobileDevice.id == device_id,
                MobileDevice.org_id == self.org_id,
            )
        ).first()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.revoked_at = datetime.now(timezone.utc)
        device.is_active = False
        
        self.db.commit()
        self.db.refresh(device)
        
        # Audit log
        self._audit_log(
            action="revoke_mobile_device",
            resource_type="mobile_device",
            resource_id=str(device_id),
            outcome=AuditOutcome.SUCCESS,
            metadata={"reason": reason}
        )
        
        return device
    
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
