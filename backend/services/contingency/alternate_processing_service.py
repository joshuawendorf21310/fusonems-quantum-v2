"""
CP-7: Alternate Processing Site Service

Manages alternate processing site configuration, capacity monitoring,
and activation procedures.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.contingency import (
    AlternateProcessingSite,
    ProcessingSiteActivationLog,
    ProcessingSiteStatus,
)
from utils.logger import logger


class AlternateProcessingService:
    """Service for managing alternate processing sites (CP-7)"""
    
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
    
    def create_processing_site(
        self,
        site_name: str,
        site_type: str,
        is_primary: bool = False,
        site_location: Optional[str] = None,
        compute_capacity_cpu_cores: Optional[int] = None,
        compute_capacity_ram_gb: Optional[int] = None,
        connection_endpoint: Optional[str] = None,
        connection_config: Optional[Dict[str, Any]] = None,
        activation_capable: bool = True,
        activation_rto_minutes: Optional[int] = None,
        activation_procedures: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlternateProcessingSite:
        """Create a new alternate processing site"""
        site = AlternateProcessingSite(
            org_id=self.org_id,
            site_name=site_name,
            site_location=site_location,
            site_type=site_type,
            is_primary=is_primary,
            compute_capacity_cpu_cores=compute_capacity_cpu_cores,
            compute_capacity_ram_gb=compute_capacity_ram_gb,
            connection_endpoint=connection_endpoint,
            connection_config=connection_config,
            status=ProcessingSiteStatus.STANDBY.value if not is_primary else ProcessingSiteStatus.ACTIVE.value,
            activation_capable=activation_capable,
            activation_rto_minutes=activation_rto_minutes,
            activation_procedures=activation_procedures,
            metadata=metadata or {},
        )
        
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        
        logger.info(f"Created processing site {site_name} for org {self.org_id}")
        return site
    
    def get_processing_site(self, site_id: int) -> Optional[AlternateProcessingSite]:
        """Get a processing site by ID"""
        return self.db.query(AlternateProcessingSite).filter(
            and_(
                AlternateProcessingSite.id == site_id,
                AlternateProcessingSite.org_id == self.org_id,
            )
        ).first()
    
    def list_processing_sites(
        self,
        status: Optional[str] = None,
        is_primary: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlternateProcessingSite]:
        """List processing sites with optional filters"""
        query = self.db.query(AlternateProcessingSite).filter(
            AlternateProcessingSite.org_id == self.org_id
        )
        
        if status:
            query = query.filter(AlternateProcessingSite.status == status)
        
        if is_primary is not None:
            query = query.filter(AlternateProcessingSite.is_primary == is_primary)
        
        return query.order_by(desc(AlternateProcessingSite.created_at)).offset(offset).limit(limit).all()
    
    def update_processing_site(
        self,
        site_id: int,
        site_name: Optional[str] = None,
        status: Optional[str] = None,
        compute_utilization_percent: Optional[float] = None,
        compute_available_cpu_cores: Optional[int] = None,
        compute_available_ram_gb: Optional[int] = None,
        health_status: Optional[str] = None,
        health_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AlternateProcessingSite]:
        """Update processing site information"""
        site = self.get_processing_site(site_id)
        if not site:
            return None
        
        if site_name is not None:
            site.site_name = site_name
        
        if status is not None:
            site.status = status
        
        if compute_utilization_percent is not None:
            site.compute_utilization_percent = compute_utilization_percent
        
        if compute_available_cpu_cores is not None:
            site.compute_available_cpu_cores = compute_available_cpu_cores
        
        if compute_available_ram_gb is not None:
            site.compute_available_ram_gb = compute_available_ram_gb
        
        if health_status is not None:
            site.health_status = health_status
        
        if health_score is not None:
            site.health_score = health_score
        
        if metadata is not None:
            site.metadata = {**(site.metadata or {}), **metadata}
        
        site.last_health_check = datetime.utcnow()
        site.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(site)
        
        logger.info(f"Updated processing site {site_id}")
        return site
    
    def initiate_activation(
        self,
        site_id: int,
        activation_type: str,
        initiated_by_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProcessingSiteActivationLog]:
        """Initiate activation of an alternate processing site"""
        site = self.get_processing_site(site_id)
        if not site or not site.activation_capable:
            return None
        
        # Create activation log
        activation_log = ProcessingSiteActivationLog(
            processing_site_id=site_id,
            org_id=self.org_id,
            activation_type=activation_type,
            activation_status="initiated",
            initiated_by_user_id=initiated_by_user_id,
            metadata=metadata or {},
        )
        
        self.db.add(activation_log)
        
        # Update site status
        if activation_type == "actual":
            site.status = ProcessingSiteStatus.ACTIVATING.value
        else:
            # Test or drill
            site.status = ProcessingSiteStatus.ACTIVATING.value
        
        site.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(activation_log)
        
        logger.info(f"Initiated {activation_type} activation for processing site {site_id}")
        return activation_log
    
    def update_activation(
        self,
        activation_log_id: int,
        activation_status: str,
        activation_duration_minutes: Optional[int] = None,
        event_message: Optional[str] = None,
        procedures_followed: Optional[str] = None,
        issues_encountered: Optional[str] = None,
    ) -> Optional[ProcessingSiteActivationLog]:
        """Update activation status"""
        activation_log = self.db.query(ProcessingSiteActivationLog).filter(
            and_(
                ProcessingSiteActivationLog.id == activation_log_id,
                ProcessingSiteActivationLog.org_id == self.org_id,
            )
        ).first()
        
        if not activation_log:
            return None
        
        activation_log.activation_status = activation_status
        
        if activation_duration_minutes is not None:
            activation_log.activation_duration_minutes = activation_duration_minutes
        
        if event_message is not None:
            activation_log.event_message = event_message
        
        if procedures_followed is not None:
            activation_log.procedures_followed = procedures_followed
        
        if issues_encountered is not None:
            activation_log.issues_encountered = issues_encountered
        
        # Update site status based on activation status
        if activation_status == "completed":
            site = self.get_processing_site(activation_log.processing_site_id)
            if site:
                site.status = ProcessingSiteStatus.ACTIVE.value
                site.last_activation_test = datetime.utcnow()
                site.updated_at = datetime.utcnow()
        elif activation_status == "failed":
            site = self.get_processing_site(activation_log.processing_site_id)
            if site:
                site.status = ProcessingSiteStatus.FAILED.value
                site.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(activation_log)
        
        logger.info(f"Updated activation {activation_log_id} to {activation_status}")
        return activation_log
    
    def get_activation_logs(
        self,
        processing_site_id: Optional[int] = None,
        activation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProcessingSiteActivationLog]:
        """Get activation logs"""
        query = self.db.query(ProcessingSiteActivationLog).filter(
            ProcessingSiteActivationLog.org_id == self.org_id
        )
        
        if processing_site_id:
            query = query.filter(ProcessingSiteActivationLog.processing_site_id == processing_site_id)
        
        if activation_type:
            query = query.filter(ProcessingSiteActivationLog.activation_type == activation_type)
        
        return query.order_by(desc(ProcessingSiteActivationLog.created_at)).offset(offset).limit(limit).all()
    
    def get_primary_site(self) -> Optional[AlternateProcessingSite]:
        """Get the primary processing site"""
        return self.db.query(AlternateProcessingSite).filter(
            and_(
                AlternateProcessingSite.org_id == self.org_id,
                AlternateProcessingSite.is_primary == True,
            )
        ).first()
    
    def get_alternate_sites(self) -> List[AlternateProcessingSite]:
        """Get all alternate (non-primary) processing sites"""
        return self.db.query(AlternateProcessingSite).filter(
            and_(
                AlternateProcessingSite.org_id == self.org_id,
                AlternateProcessingSite.is_primary == False,
            )
        ).all()
