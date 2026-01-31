"""
Least Functionality Service for FedRAMP CM-7 Compliance

FedRAMP Requirement CM-7: Least Functionality
- Service inventory
- Unnecessary service detection
- Port/protocol restrictions
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import ServiceInventory


class LeastFunctionalityService:
    """
    Service for least functionality enforcement (CM-7).
    """
    
    # Required services that should always be enabled
    REQUIRED_SERVICES = [
        'database',
        'api_server',
        'authentication',
        'audit_logging',
    ]
    
    @staticmethod
    def register_service(
        db: Session,
        org_id: int,
        service_name: str,
        service_type: str,
        description: Optional[str] = None,
        ports: Optional[List[int]] = None,
        protocols: Optional[List[str]] = None,
        is_required: bool = False,
    ) -> ServiceInventory:
        """
        Register a system service.
        
        Args:
            db: Database session
            org_id: Organization ID
            service_name: Name of service
            service_type: Type of service
            description: Service description
            ports: Ports used by service
            protocols: Protocols used
            is_required: Is this a required service?
            
        Returns:
            Created ServiceInventory record
        """
        # Check if service already exists
        existing = db.query(ServiceInventory).filter(
            ServiceInventory.service_name == service_name,
            ServiceInventory.org_id == org_id,
        ).first()
        
        if existing:
            # Update existing
            existing.service_type = service_type
            existing.description = description
            existing.ports = ports
            existing.protocols = protocols
            existing.is_required = is_required
            existing.last_checked_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
        
        # Determine if service is unnecessary
        is_unnecessary = not is_required and service_name not in LeastFunctionalityService.REQUIRED_SERVICES
        
        service = ServiceInventory(
            org_id=org_id,
            service_name=service_name,
            service_type=service_type,
            description=description,
            ports=ports,
            protocols=protocols,
            is_enabled=True,
            is_required=is_required,
            is_unnecessary=is_unnecessary,
            discovered_at=datetime.now(timezone.utc),
            last_checked_at=datetime.now(timezone.utc),
        )
        
        db.add(service)
        db.commit()
        db.refresh(service)
        
        logger.info(f"Service registered: {service_name} (org_id={org_id}, required={is_required})")
        
        return service
    
    @staticmethod
    def detect_unnecessary_services(
        db: Session,
        org_id: int,
    ) -> List[ServiceInventory]:
        """Detect unnecessary services"""
        services = db.query(ServiceInventory).filter(
            ServiceInventory.org_id == org_id,
            ServiceInventory.is_enabled == True,
        ).all()
        
        unnecessary = []
        for service in services:
            if not service.is_required and service.service_name not in LeastFunctionalityService.REQUIRED_SERVICES:
                service.is_unnecessary = True
                unnecessary.append(service)
        
        if unnecessary:
            db.commit()
            logger.warning(f"Detected {len(unnecessary)} unnecessary services")
        
        return unnecessary
    
    @staticmethod
    def disable_service(
        db: Session,
        service_id: str,
        org_id: int,
        disabled_by_user_id: Optional[int] = None,
    ) -> ServiceInventory:
        """Disable a service"""
        service = db.query(ServiceInventory).filter(
            ServiceInventory.id == service_id,
            ServiceInventory.org_id == org_id,
        ).first()
        
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        if service.is_required:
            raise ValueError(f"Cannot disable required service: {service.service_name}")
        
        service.is_enabled = False
        service.last_checked_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(service)
        
        logger.info(f"Service disabled: {service.service_name}")
        
        return service
    
    @staticmethod
    def restrict_ports(
        db: Session,
        service_id: str,
        org_id: int,
        allowed_ports: List[int],
    ) -> ServiceInventory:
        """Restrict ports for a service"""
        service = db.query(ServiceInventory).filter(
            ServiceInventory.id == service_id,
            ServiceInventory.org_id == org_id,
        ).first()
        
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        service.port_restrictions = allowed_ports
        service.last_checked_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(service)
        
        logger.info(f"Port restrictions applied to service: {service.service_name}")
        
        return service
    
    @staticmethod
    def restrict_protocols(
        db: Session,
        service_id: str,
        org_id: int,
        allowed_protocols: List[str],
    ) -> ServiceInventory:
        """Restrict protocols for a service"""
        service = db.query(ServiceInventory).filter(
            ServiceInventory.id == service_id,
            ServiceInventory.org_id == org_id,
        ).first()
        
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        service.protocol_restrictions = allowed_protocols
        service.last_checked_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(service)
        
        logger.info(f"Protocol restrictions applied to service: {service.service_name}")
        
        return service
    
    @staticmethod
    def get_services(
        db: Session,
        org_id: int,
        enabled_only: bool = False,
        unnecessary_only: bool = False,
    ) -> List[ServiceInventory]:
        """Get services"""
        query = db.query(ServiceInventory).filter(
            ServiceInventory.org_id == org_id
        )
        
        if enabled_only:
            query = query.filter(ServiceInventory.is_enabled == True)
        
        if unnecessary_only:
            query = query.filter(ServiceInventory.is_unnecessary == True)
        
        return query.order_by(desc(ServiceInventory.discovered_at)).all()
