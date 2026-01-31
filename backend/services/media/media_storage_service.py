"""
Media Storage Service for FedRAMP MP-4 Compliance

FedRAMP MP-4: Media Storage
- Track storage locations
- Monitor environmental controls
- Manage inventory
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.media_protection import (
    MediaStorage,
    MediaType,
    StorageStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class MediaStorageService:
    """
    Service for managing media storage (MP-4).
    
    Implements FedRAMP MP-4 control requirements.
    """
    
    @staticmethod
    def create_storage(
        db: Session,
        org_id: int,
        media_identifier: str,
        media_type: str,
        storage_location: str,
        media_description: Optional[str] = None,
        storage_facility: Optional[str] = None,
        storage_room: Optional[str] = None,
        storage_container: Optional[str] = None,
        temperature_min: Optional[str] = None,
        temperature_max: Optional[str] = None,
        humidity_min: Optional[str] = None,
        humidity_max: Optional[str] = None,
        fire_suppression: bool = False,
        access_control: Optional[str] = None,
        created_by_user_id: Optional[int] = None,
    ) -> MediaStorage:
        """
        Create a media storage record (MP-4).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_identifier: Unique media identifier
            media_type: Type of media
            storage_location: Storage location
            media_description: Optional description
            storage_facility: Facility name
            storage_room: Room number/name
            storage_container: Container identifier
            temperature_min: Minimum temperature
            temperature_max: Maximum temperature
            humidity_min: Minimum humidity
            humidity_max: Maximum humidity
            fire_suppression: Fire suppression available
            access_control: Access control type
            created_by_user_id: User ID creating record
            
        Returns:
            Created MediaStorage record
        """
        # Check for duplicate identifier
        existing = db.query(MediaStorage).filter(
            MediaStorage.media_identifier == media_identifier,
        ).first()
        
        if existing:
            raise ValueError(f"Media identifier {media_identifier} already exists")
        
        storage = MediaStorage(
            org_id=org_id,
            media_identifier=media_identifier,
            media_type=media_type,
            media_description=media_description,
            storage_location=storage_location,
            storage_facility=storage_facility,
            storage_room=storage_room,
            storage_container=storage_container,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
            fire_suppression=fire_suppression,
            access_control=access_control,
            storage_status=StorageStatus.IN_USE.value,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(storage)
        db.commit()
        db.refresh(storage)
        
        # Log audit event
        MediaStorageService._log_audit(
            db=db,
            org_id=org_id,
            user_id=created_by_user_id,
            action="create_media_storage",
            resource_type="media_storage",
            resource_id=str(storage.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_identifier": media_identifier,
                "media_type": media_type,
                "storage_location": storage_location,
            },
        )
        
        logger.info(
            "Created media storage: media_identifier=%s, location=%s",
            media_identifier,
            storage_location,
        )
        
        return storage
    
    @staticmethod
    def update_storage_location(
        db: Session,
        storage_id: UUID,
        org_id: int,
        storage_location: str,
        storage_facility: Optional[str] = None,
        storage_room: Optional[str] = None,
        storage_container: Optional[str] = None,
        updated_by_user_id: Optional[int] = None,
    ) -> MediaStorage:
        """
        Update storage location (MP-4).
        
        Args:
            db: Database session
            storage_id: Storage record ID
            org_id: Organization ID
            storage_location: New storage location
            storage_facility: Facility name
            storage_room: Room number/name
            storage_container: Container identifier
            updated_by_user_id: User ID making update
            
        Returns:
            Updated MediaStorage record
        """
        storage = db.query(MediaStorage).filter(
            MediaStorage.id == storage_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not storage:
            raise ValueError(f"Storage record {storage_id} not found")
        
        old_location = storage.storage_location
        
        storage.storage_location = storage_location
        storage.storage_facility = storage_facility
        storage.storage_room = storage_room
        storage.storage_container = storage_container
        
        db.commit()
        db.refresh(storage)
        
        # Log audit event
        MediaStorageService._log_audit(
            db=db,
            org_id=org_id,
            user_id=updated_by_user_id,
            action="update_storage_location",
            resource_type="media_storage",
            resource_id=str(storage_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_identifier": storage.media_identifier,
                "old_location": old_location,
                "new_location": storage_location,
            },
        )
        
        logger.info(
            "Updated storage location: storage_id=%s, old=%s, new=%s",
            storage_id,
            old_location,
            storage_location,
        )
        
        return storage
    
    @staticmethod
    def perform_inventory_check(
        db: Session,
        storage_id: UUID,
        org_id: int,
        checked_by_user_id: Optional[int] = None,
    ) -> MediaStorage:
        """
        Perform inventory check (MP-4).
        
        Args:
            db: Database session
            storage_id: Storage record ID
            org_id: Organization ID
            checked_by_user_id: User ID performing check
            
        Returns:
            Updated MediaStorage record
        """
        storage = db.query(MediaStorage).filter(
            MediaStorage.id == storage_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not storage:
            raise ValueError(f"Storage record {storage_id} not found")
        
        now = datetime.now(timezone.utc)
        storage.last_inventory_check = now
        
        # Set next check date (default: 30 days)
        from datetime import timedelta
        storage.next_inventory_check = now + timedelta(days=30)
        
        db.commit()
        db.refresh(storage)
        
        # Log audit event
        MediaStorageService._log_audit(
            db=db,
            org_id=org_id,
            user_id=checked_by_user_id,
            action="inventory_check",
            resource_type="media_storage",
            resource_id=str(storage_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_identifier": storage.media_identifier,
                "inventory_date": now.isoformat(),
            },
        )
        
        logger.info("Performed inventory check: storage_id=%s", storage_id)
        
        return storage
    
    @staticmethod
    def list_storage(
        db: Session,
        org_id: int,
        storage_status: Optional[str] = None,
        media_type: Optional[str] = None,
        storage_location: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaStorage]:
        """
        List media storage records (MP-4).
        
        Args:
            db: Database session
            org_id: Organization ID
            storage_status: Optional status filter
            media_type: Optional media type filter
            storage_location: Optional location filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of MediaStorage records
        """
        query = db.query(MediaStorage).filter(
            MediaStorage.org_id == org_id,
        )
        
        if storage_status:
            query = query.filter(MediaStorage.storage_status == storage_status)
        
        if media_type:
            query = query.filter(MediaStorage.media_type == media_type)
        
        if storage_location:
            query = query.filter(MediaStorage.storage_location.ilike(f"%{storage_location}%"))
        
        return query.order_by(desc(MediaStorage.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def _log_audit(
        db: Session,
        org_id: int,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        metadata: Optional[dict] = None,
    ):
        """Log media storage audit event."""
        try:
            audit_log = ComprehensiveAuditLog(
                org_id=org_id,
                user_id=user_id,
                event_type=AuditEventType.DATA_MODIFICATION.value,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                metadata=metadata,
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error("Failed to log audit event: %s", e)
            db.rollback()
