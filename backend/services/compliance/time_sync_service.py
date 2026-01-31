"""
Time Synchronization Service
FedRAMP Control: AU-8 - Time Stamps

Ensures all system timestamps are synchronized with authoritative time source
Required for audit log integrity and event correlation
"""
from datetime import datetime, timezone
from typing import Optional
import ntplib
from fastapi import HTTPException, status

from core.config import settings
from core.logger import logger


class TimeSyncService:
    """
    NTP-based time synchronization service
    FedRAMP requires synchronization with authoritative time source
    """
    
    def __init__(self):
        self.ntp_servers = [
            "time.nist.gov",  # NIST (authoritative for FedRAMP)
            "time-a-g.nist.gov",
            "time-b-g.nist.gov",
            "time.windows.com",
        ]
        self.max_drift_seconds = 5  # FedRAMP allows max 5 seconds drift
        self.ntp_client = ntplib.NTPClient()
    
    def get_ntp_time(self, server: Optional[str] = None) -> Optional[datetime]:
        """
        Get current time from NTP server
        
        Args:
            server: NTP server to query (defaults to NIST)
            
        Returns:
            datetime: Current time from NTP server, or None on failure
        """
        server = server or self.ntp_servers[0]
        
        try:
            response = self.ntp_client.request(server, version=4, timeout=5)
            ntp_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
            logger.debug(f"NTP time from {server}: {ntp_time.isoformat()}")
            return ntp_time
        except Exception as e:
            logger.warning(f"Failed to get NTP time from {server}: {e}")
            return None
    
    def get_authoritative_time(self) -> datetime:
        """
        Get authoritative time from NTP servers with fallback
        Tries multiple servers if primary fails
        
        Returns:
            datetime: Authoritative time
        """
        for server in self.ntp_servers:
            ntp_time = self.get_ntp_time(server)
            if ntp_time:
                return ntp_time
        
        # If all NTP servers fail, use system time but log warning
        logger.error("All NTP servers unreachable, using system time (COMPLIANCE RISK)")
        return datetime.now(timezone.utc)
    
    def check_time_drift(self) -> dict:
        """
        Check system clock drift against NTP
        FedRAMP AU-8 requires time synchronization within 5 seconds
        
        Returns:
            dict: Drift information and compliance status
        """
        system_time = datetime.now(timezone.utc)
        ntp_time = self.get_authoritative_time()
        
        if not ntp_time:
            return {
                "status": "error",
                "message": "Unable to reach NTP servers",
                "compliant": False,
                "drift_seconds": None
            }
        
        drift = abs((system_time - ntp_time).total_seconds())
        compliant = drift <= self.max_drift_seconds
        
        if not compliant:
            logger.error(
                f"Time drift exceeds FedRAMP threshold: {drift:.2f}s > {self.max_drift_seconds}s"
            )
        
        return {
            "status": "ok" if compliant else "drift_exceeded",
            "system_time": system_time.isoformat(),
            "ntp_time": ntp_time.isoformat(),
            "drift_seconds": round(drift, 3),
            "max_allowed_drift": self.max_drift_seconds,
            "compliant": compliant,
            "ntp_server": self.ntp_servers[0]
        }
    
    def enforce_time_sync(self) -> None:
        """
        Enforce time synchronization
        Raises exception if drift exceeds threshold
        
        Raises:
            HTTPException: If time drift is non-compliant
        """
        if settings.ENV == "test":
            return  # Skip in test environment
        
        drift_info = self.check_time_drift()
        
        if not drift_info["compliant"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "TIME_SYNC_FAILED",
                    "message": "System time drift exceeds FedRAMP threshold",
                    "drift_seconds": drift_info["drift_seconds"],
                    "max_allowed": self.max_drift_seconds,
                    "remediation": "System administrator must synchronize system clock with NTP"
                }
            )
    
    def get_synchronized_time(self) -> datetime:
        """
        Get synchronized time for audit logs
        Uses NTP if available, falls back to system time
        
        Returns:
            datetime: Current synchronized time
        """
        ntp_time = self.get_ntp_time()
        if ntp_time:
            return ntp_time
        return datetime.now(timezone.utc)


# Global service instance
time_sync_service = TimeSyncService()


def get_audit_timestamp() -> datetime:
    """
    Get FedRAMP-compliant timestamp for audit logs
    Synchronized with authoritative time source
    """
    return time_sync_service.get_synchronized_time()
