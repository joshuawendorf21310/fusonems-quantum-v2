"""
CP-6: Alternate Storage Site Service

Manages alternate storage site configuration, replication monitoring,
and failover automation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.contingency import (
    AlternateStorageSite,
    StorageReplicationLog,
    StorageSiteStatus,
    ReplicationStatus,
)
from utils.logger import logger


class AlternateStorageService:
    """Service for managing alternate storage sites (CP-6)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    def create_storage_site(
        self,
        site_name: str,
        site_type: str,
        is_primary: bool = False,
        site_location: Optional[str] = None,
        storage_capacity_gb: Optional[float] = None,
        connection_endpoint: Optional[str] = None,
        connection_config: Optional[Dict[str, Any]] = None,
        failover_capable: bool = True,
        failover_rto_minutes: Optional[int] = None,
        failover_rpo_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlternateStorageSite:
        """Create a new alternate storage site"""
        site = AlternateStorageSite(
            org_id=self.org_id,
            site_name=site_name,
            site_location=site_location,
            site_type=site_type,
            is_primary=is_primary,
            storage_capacity_gb=storage_capacity_gb,
            connection_endpoint=connection_endpoint,
            connection_config=connection_config,
            status=StorageSiteStatus.STANDBY.value if not is_primary else StorageSiteStatus.ACTIVE.value,
            failover_capable=failover_capable,
            failover_rto_minutes=failover_rto_minutes,
            failover_rpo_minutes=failover_rpo_minutes,
            metadata=metadata or {},
        )
        
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        
        logger.info(f"Created storage site {site_name} for org {self.org_id}")
        return site
    
    def get_storage_site(self, site_id: int) -> Optional[AlternateStorageSite]:
        """Get a storage site by ID"""
        return self.db.query(AlternateStorageSite).filter(
            and_(
                AlternateStorageSite.id == site_id,
                AlternateStorageSite.org_id == self.org_id,
            )
        ).first()
    
    def list_storage_sites(
        self,
        status: Optional[str] = None,
        is_primary: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlternateStorageSite]:
        """List storage sites with optional filters"""
        query = self.db.query(AlternateStorageSite).filter(
            AlternateStorageSite.org_id == self.org_id
        )
        
        if status:
            query = query.filter(AlternateStorageSite.status == status)
        
        if is_primary is not None:
            query = query.filter(AlternateStorageSite.is_primary == is_primary)
        
        return query.order_by(desc(AlternateStorageSite.created_at)).offset(offset).limit(limit).all()
    
    def update_storage_site(
        self,
        site_id: int,
        site_name: Optional[str] = None,
        status: Optional[str] = None,
        storage_used_gb: Optional[float] = None,
        storage_available_gb: Optional[float] = None,
        replication_status: Optional[str] = None,
        replication_lag_seconds: Optional[int] = None,
        replication_health_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AlternateStorageSite]:
        """Update storage site information"""
        site = self.get_storage_site(site_id)
        if not site:
            return None
        
        if site_name is not None:
            site.site_name = site_name
        
        if status is not None:
            site.status = status
        
        if storage_used_gb is not None:
            site.storage_used_gb = storage_used_gb
        
        if storage_available_gb is not None:
            site.storage_available_gb = storage_available_gb
        
        if replication_status is not None:
            site.replication_status = replication_status
        
        if replication_lag_seconds is not None:
            site.replication_lag_seconds = replication_lag_seconds
        
        if replication_health_score is not None:
            site.replication_health_score = replication_health_score
        
        if metadata is not None:
            site.metadata = {**(site.metadata or {}), **metadata}
        
        site.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(site)
        
        logger.info(f"Updated storage site {site_id}")
        return site
    
    def log_replication_event(
        self,
        storage_site_id: int,
        replication_status: str,
        event_type: str,
        replication_lag_seconds: Optional[int] = None,
        data_transferred_gb: Optional[float] = None,
        event_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageReplicationLog:
        """Log a replication event"""
        log_entry = StorageReplicationLog(
            storage_site_id=storage_site_id,
            org_id=self.org_id,
            replication_status=replication_status,
            replication_lag_seconds=replication_lag_seconds,
            data_transferred_gb=data_transferred_gb,
            event_type=event_type,
            event_message=event_message,
            metadata=metadata or {},
        )
        
        self.db.add(log_entry)
        
        # Update site's last replication check
        site = self.get_storage_site(storage_site_id)
        if site:
            site.last_replication_check = datetime.utcnow()
            site.replication_status = replication_status
            if replication_lag_seconds is not None:
                site.replication_lag_seconds = replication_lag_seconds
        
        self.db.commit()
        self.db.refresh(log_entry)
        
        logger.info(f"Logged replication event for site {storage_site_id}: {event_type}")
        return log_entry
    
    def get_replication_logs(
        self,
        storage_site_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StorageReplicationLog]:
        """Get replication logs"""
        query = self.db.query(StorageReplicationLog).filter(
            StorageReplicationLog.org_id == self.org_id
        )
        
        if storage_site_id:
            query = query.filter(StorageReplicationLog.storage_site_id == storage_site_id)
        
        return query.order_by(desc(StorageReplicationLog.created_at)).offset(offset).limit(limit).all()
    
    def test_failover(self, site_id: int) -> Optional[AlternateStorageSite]:
        """Test failover to an alternate storage site"""
        site = self.get_storage_site(site_id)
        if not site or not site.failover_capable:
            return None
        
        site.last_failover_test = datetime.utcnow()
        site.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(site)
        
        logger.info(f"Tested failover for storage site {site_id}")
        return site
    
    def get_primary_site(self) -> Optional[AlternateStorageSite]:
        """Get the primary storage site"""
        return self.db.query(AlternateStorageSite).filter(
            and_(
                AlternateStorageSite.org_id == self.org_id,
                AlternateStorageSite.is_primary == True,
            )
        ).first()
    
    def get_alternate_sites(self) -> List[AlternateStorageSite]:
        """Get all alternate (non-primary) storage sites"""
        return self.db.query(AlternateStorageSite).filter(
            and_(
                AlternateStorageSite.org_id == self.org_id,
                AlternateStorageSite.is_primary == False,
            )
        ).all()
