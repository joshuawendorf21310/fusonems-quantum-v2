"""
PE-3: Physical Access Control Service
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.physical_environmental import (
    AccessPoint,
    PhysicalAccessLog,
    AccessPointType,
    AccessControlMethod,
)
from core.logger import logger


class PhysicalAccessControlService:
    """Service for managing physical access control"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_access_point(
        self,
        org_id: int,
        name: str,
        location: str,
        access_point_type: str,
        primary_method: str,
        area_id: Optional[str] = None,
    ) -> AccessPoint:
        """Create a new access point"""
        
        access_point = AccessPoint(
            org_id=org_id,
            name=name,
            location=location,
            access_point_type=access_point_type,
            primary_method=primary_method,
            area_id=area_id,
        )
        
        self.db.add(access_point)
        self.db.commit()
        self.db.refresh(access_point)
        
        logger.info(f"Created access point {access_point.id} at {location}")
        return access_point
    
    def log_access_event(
        self,
        org_id: int,
        access_point_id: int,
        access_method: str,
        access_result: str,
        user_id: Optional[int] = None,
        authorization_id: Optional[int] = None,
        credential_id: Optional[str] = None,
        badge_number: Optional[str] = None,
        tailgating_detected: bool = False,
    ) -> PhysicalAccessLog:
        """Log a physical access event"""
        
        log_entry = PhysicalAccessLog(
            org_id=org_id,
            access_point_id=access_point_id,
            user_id=user_id,
            authorization_id=authorization_id,
            access_method=access_method,
            credential_id=credential_id,
            badge_number=badge_number,
            access_result=access_result,
            tailgating_detected=tailgating_detected,
            timestamp=datetime.utcnow(),
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        if tailgating_detected:
            logger.warning(f"Tailgating detected at access point {access_point_id}")
        
        return log_entry
    
    def get_access_logs(
        self,
        org_id: int,
        access_point_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[PhysicalAccessLog]:
        """Get access logs"""
        
        query = self.db.query(PhysicalAccessLog).filter(
            PhysicalAccessLog.org_id == org_id
        )
        
        if access_point_id:
            query = query.filter(PhysicalAccessLog.access_point_id == access_point_id)
        
        if user_id:
            query = query.filter(PhysicalAccessLog.user_id == user_id)
        
        return query.order_by(PhysicalAccessLog.timestamp.desc()).limit(limit).all()
    
    def detect_tailgating(
        self,
        access_point_id: int,
        time_window_seconds: int = 5,
    ) -> bool:
        """Detect potential tailgating based on access patterns"""
        
        recent_logs = self.db.query(PhysicalAccessLog).filter(
            and_(
                PhysicalAccessLog.access_point_id == access_point_id,
                PhysicalAccessLog.timestamp >= datetime.utcnow() - timedelta(seconds=time_window_seconds),
            )
        ).order_by(PhysicalAccessLog.timestamp.desc()).limit(2).all()
        
        if len(recent_logs) >= 2:
            # Check if two access events happened very close together
            time_diff = (recent_logs[0].timestamp - recent_logs[1].timestamp).total_seconds()
            if time_diff < time_window_seconds and recent_logs[0].user_id != recent_logs[1].user_id:
                return True
        
        return False
