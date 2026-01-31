"""
Media Transport Service for FedRAMP MP-5 Compliance

FedRAMP MP-5: Media Transport
- Control transport authorization
- Track chain of custody
- Enforce encryption requirements
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logger import logger
from models.media_protection import (
    MediaTransport,
    MediaStorage,
    TransportStatus,
)
from models.comprehensive_audit_log import ComprehensiveAuditLog, AuditEventType, AuditOutcome


class MediaTransportService:
    """
    Service for managing media transport (MP-5).
    
    Implements FedRAMP MP-5 control requirements.
    """
    
    @staticmethod
    def _generate_transport_number(db: Session, org_id: int) -> str:
        """Generate unique transport number."""
        year = datetime.now(timezone.utc).year
        last_transport = db.query(MediaTransport).filter(
            MediaTransport.org_id == org_id,
            MediaTransport.transport_number.like(f"TRANS-{year}-%"),
        ).order_by(desc(MediaTransport.transport_number)).first()
        
        if last_transport:
            try:
                last_num = int(last_transport.transport_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"TRANS-{year}-{next_num:04d}"
    
    @staticmethod
    def create_transport(
        db: Session,
        org_id: int,
        media_id: UUID,
        transport_purpose: str,
        origin_location: str,
        destination_location: str,
        transporter_name: str,
        authorized_by_user_id: int,
        destination_contact: Optional[str] = None,
        destination_contact_phone: Optional[str] = None,
        transporter_company: Optional[str] = None,
        transporter_contact: Optional[str] = None,
        encryption_required: bool = True,
        encryption_method: Optional[str] = None,
        transport_date: Optional[datetime] = None,
        expected_delivery_date: Optional[datetime] = None,
        tracking_number: Optional[str] = None,
        carrier_name: Optional[str] = None,
    ) -> MediaTransport:
        """
        Create a media transport record (MP-5).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Media ID
            transport_purpose: Purpose of transport
            origin_location: Origin location
            destination_location: Destination location
            transporter_name: Name of transporter
            authorized_by_user_id: User ID authorizing transport
            destination_contact: Destination contact
            destination_contact_phone: Destination contact phone
            transporter_company: Transporter company
            transporter_contact: Transporter contact
            encryption_required: Encryption required
            encryption_method: Encryption method
            transport_date: Transport date
            expected_delivery_date: Expected delivery date
            tracking_number: Tracking number
            carrier_name: Carrier name
            
        Returns:
            Created MediaTransport record
        """
        # Verify media exists
        media = db.query(MediaStorage).filter(
            MediaStorage.id == media_id,
            MediaStorage.org_id == org_id,
        ).first()
        
        if not media:
            raise ValueError(f"Media {media_id} not found")
        
        transport_number = MediaTransportService._generate_transport_number(db, org_id)
        
        transport = MediaTransport(
            org_id=org_id,
            media_id=media_id,
            transport_number=transport_number,
            transport_purpose=transport_purpose,
            origin_location=origin_location,
            destination_location=destination_location,
            destination_contact=destination_contact,
            destination_contact_phone=destination_contact_phone,
            authorized_by_user_id=authorized_by_user_id,
            authorization_date=datetime.now(timezone.utc),
            transporter_name=transporter_name,
            transporter_company=transporter_company,
            transporter_contact=transporter_contact,
            encryption_required=encryption_required,
            encryption_method=encryption_method,
            transport_status=TransportStatus.PENDING.value,
            transport_date=transport_date or datetime.now(timezone.utc),
            expected_delivery_date=expected_delivery_date,
            tracking_number=tracking_number,
            carrier_name=carrier_name,
            chain_of_custody=[],
        )
        
        db.add(transport)
        db.commit()
        db.refresh(transport)
        
        # Log audit event
        MediaTransportService._log_audit(
            db=db,
            org_id=org_id,
            user_id=authorized_by_user_id,
            action="create_media_transport",
            resource_type="media_transport",
            resource_id=str(transport.id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "media_id": str(media_id),
                "transport_number": transport_number,
                "origin": origin_location,
                "destination": destination_location,
            },
        )
        
        logger.info(
            "Created media transport: transport_number=%s, media_id=%s",
            transport_number,
            media_id,
        )
        
        return transport
    
    @staticmethod
    def update_chain_of_custody(
        db: Session,
        transport_id: UUID,
        org_id: int,
        custody_entry: Dict,
        updated_by_user_id: Optional[int] = None,
    ) -> MediaTransport:
        """
        Update chain of custody (MP-5).
        
        Args:
            db: Database session
            transport_id: Transport ID
            org_id: Organization ID
            custody_entry: Custody entry to add
            updated_by_user_id: User ID making update
            
        Returns:
            Updated MediaTransport record
        """
        transport = db.query(MediaTransport).filter(
            MediaTransport.id == transport_id,
            MediaTransport.org_id == org_id,
        ).first()
        
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")
        
        if not transport.chain_of_custody:
            transport.chain_of_custody = []
        
        custody_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        transport.chain_of_custody.append(custody_entry)
        
        db.commit()
        db.refresh(transport)
        
        # Log audit event
        MediaTransportService._log_audit(
            db=db,
            org_id=org_id,
            user_id=updated_by_user_id,
            action="update_chain_of_custody",
            resource_type="media_transport",
            resource_id=str(transport_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "transport_number": transport.transport_number,
                "custody_entry": custody_entry,
            },
        )
        
        logger.info("Updated chain of custody: transport_id=%s", transport_id)
        
        return transport
    
    @staticmethod
    def mark_delivered(
        db: Session,
        transport_id: UUID,
        org_id: int,
        actual_delivery_date: Optional[datetime] = None,
        updated_by_user_id: Optional[int] = None,
    ) -> MediaTransport:
        """
        Mark transport as delivered (MP-5).
        
        Args:
            db: Database session
            transport_id: Transport ID
            org_id: Organization ID
            actual_delivery_date: Actual delivery date
            updated_by_user_id: User ID making update
            
        Returns:
            Updated MediaTransport record
        """
        transport = db.query(MediaTransport).filter(
            MediaTransport.id == transport_id,
            MediaTransport.org_id == org_id,
        ).first()
        
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")
        
        transport.transport_status = TransportStatus.DELIVERED.value
        transport.actual_delivery_date = actual_delivery_date or datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(transport)
        
        # Log audit event
        MediaTransportService._log_audit(
            db=db,
            org_id=org_id,
            user_id=updated_by_user_id,
            action="mark_transport_delivered",
            resource_type="media_transport",
            resource_id=str(transport_id),
            outcome=AuditOutcome.SUCCESS.value,
            metadata={
                "transport_number": transport.transport_number,
                "delivery_date": transport.actual_delivery_date.isoformat(),
            },
        )
        
        logger.info("Marked transport delivered: transport_id=%s", transport_id)
        
        return transport
    
    @staticmethod
    def list_transports(
        db: Session,
        org_id: int,
        media_id: Optional[UUID] = None,
        transport_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaTransport]:
        """
        List media transport records (MP-5).
        
        Args:
            db: Database session
            org_id: Organization ID
            media_id: Optional media ID filter
            transport_status: Optional status filter
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of MediaTransport records
        """
        query = db.query(MediaTransport).filter(
            MediaTransport.org_id == org_id,
        )
        
        if media_id:
            query = query.filter(MediaTransport.media_id == media_id)
        
        if transport_status:
            query = query.filter(MediaTransport.transport_status == transport_status)
        
        return query.order_by(desc(MediaTransport.transport_date)).limit(limit).offset(offset).all()
    
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
        """Log media transport audit event."""
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
