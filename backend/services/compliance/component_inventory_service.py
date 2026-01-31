"""
Component Inventory Service for FedRAMP CM-8 Compliance

FedRAMP Requirement CM-8: Component Inventory
- Automated asset discovery
- Software inventory
- Hardware inventory
- License management
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.cm_controls import SystemComponent, ComponentType, ComponentStatus


class ComponentInventoryService:
    """
    Service for component inventory management (CM-8).
    """
    
    @staticmethod
    def register_component(
        db: Session,
        org_id: int,
        component_name: str,
        component_type: ComponentType,
        version: Optional[str] = None,
        vendor: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        hostname: Optional[str] = None,
        ip_address: Optional[str] = None,
        port: Optional[int] = None,
        configuration: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None,
        discovery_method: str = "manual",
    ) -> SystemComponent:
        """
        Register a system component.
        
        Args:
            db: Database session
            org_id: Organization ID
            component_name: Name of component
            component_type: Type of component
            version: Component version
            vendor: Vendor name
            description: Component description
            location: Physical or logical location
            hostname: Hostname
            ip_address: IP address
            port: Port number
            configuration: Component configuration
            dependencies: Dependencies on other components
            discovery_method: How component was discovered
            
        Returns:
            Created SystemComponent
        """
        # Check if component already exists
        existing = db.query(SystemComponent).filter(
            SystemComponent.component_name == component_name,
            SystemComponent.org_id == org_id,
            SystemComponent.component_type == component_type.value,
        ).first()
        
        if existing:
            # Update existing
            existing.version = version
            existing.vendor = vendor
            existing.description = description
            existing.location = location
            existing.hostname = hostname
            existing.ip_address = ip_address
            existing.port = port
            existing.configuration = configuration
            existing.dependencies = dependencies
            existing.last_seen_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
        
        component = SystemComponent(
            org_id=org_id,
            component_name=component_name,
            component_type=component_type.value,
            version=version,
            vendor=vendor,
            description=description,
            location=location,
            hostname=hostname,
            ip_address=ip_address,
            port=port,
            status=ComponentStatus.ACTIVE.value,
            configuration=configuration,
            dependencies=dependencies,
            discovered_at=datetime.now(timezone.utc),
            discovery_method=discovery_method,
            last_seen_at=datetime.now(timezone.utc),
        )
        
        db.add(component)
        db.commit()
        db.refresh(component)
        
        logger.info(
            f"Component registered: {component_name} "
            f"(type={component_type.value}, org_id={org_id})"
        )
        
        return component
    
    @staticmethod
    def discover_components_automated(
        db: Session,
        org_id: int,
        components: List[Dict],
    ) -> List[SystemComponent]:
        """
        Automatically discover and register components.
        
        Args:
            db: Database session
            org_id: Organization ID
            components: List of component dictionaries
            
        Returns:
            List of registered/updated components
        """
        registered = []
        
        for comp_data in components:
            component = ComponentInventoryService.register_component(
                db=db,
                org_id=org_id,
                component_name=comp_data['name'],
                component_type=ComponentType(comp_data.get('type', 'software')),
                version=comp_data.get('version'),
                vendor=comp_data.get('vendor'),
                description=comp_data.get('description'),
                location=comp_data.get('location'),
                hostname=comp_data.get('hostname'),
                ip_address=comp_data.get('ip_address'),
                port=comp_data.get('port'),
                configuration=comp_data.get('configuration'),
                dependencies=comp_data.get('dependencies'),
                discovery_method="automated",
            )
            registered.append(component)
        
        logger.info(f"Automatically discovered {len(registered)} components (org_id={org_id})")
        
        return registered
    
    @staticmethod
    def mark_component_inactive(
        db: Session,
        component_id: str,
        org_id: int,
    ) -> SystemComponent:
        """Mark a component as inactive"""
        component = db.query(SystemComponent).filter(
            SystemComponent.id == component_id,
            SystemComponent.org_id == org_id,
        ).first()
        
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        component.status = ComponentStatus.INACTIVE.value
        db.commit()
        db.refresh(component)
        
        logger.info(f"Component marked inactive: {component.component_name}")
        
        return component
    
    @staticmethod
    def get_components(
        db: Session,
        org_id: int,
        component_type: Optional[ComponentType] = None,
        status: Optional[ComponentStatus] = None,
    ) -> List[SystemComponent]:
        """Get components"""
        query = db.query(SystemComponent).filter(
            SystemComponent.org_id == org_id
        )
        
        if component_type:
            query = query.filter(SystemComponent.component_type == component_type.value)
        
        if status:
            query = query.filter(SystemComponent.status == status.value)
        
        return query.order_by(desc(SystemComponent.discovered_at)).all()
    
    @staticmethod
    def get_component_by_name(
        db: Session,
        org_id: int,
        component_name: str,
        component_type: Optional[ComponentType] = None,
    ) -> Optional[SystemComponent]:
        """Get a component by name"""
        query = db.query(SystemComponent).filter(
            SystemComponent.component_name == component_name,
            SystemComponent.org_id == org_id,
        )
        
        if component_type:
            query = query.filter(SystemComponent.component_type == component_type.value)
        
        return query.first()
