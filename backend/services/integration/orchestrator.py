"""
Service Orchestration Layer
Ensures all services work together seamlessly.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from core.database import get_db
from core.logger import logger
from models.epcr_core import EpcrRecord, EpcrRecordStatus
from models.billing_claims import BillingRecord, BillingClaim
from models.cad import CADIncident
from services.cad.socket_bridge import get_socket_bridge
from utils.events import emit_event


class ServiceOrchestrator:
    """
    Orchestrates communication between all platform services.
    Ensures CAD, ePCR, Billing, and other services work together.
    """
    
    @staticmethod
    def on_epcr_finalized(db: Session, epcr_record: EpcrRecord, user_id: int):
        """
        Called when ePCR is finalized.
        Triggers:
        1. Billing record creation
        2. CAD backend notification
        3. Claims workflow initiation
        4. NEMSIS submission (if configured)
        """
        try:
            logger.info(f"Orchestrator: ePCR {epcr_record.id} finalized, triggering integrations")
            
            # 1. Create billing record if it doesn't exist
            incident_id = epcr_record.incident_id or epcr_record.custom_fields.get('incident_id') if epcr_record.custom_fields else None
            
            if incident_id:
                existing_billing = db.query(BillingRecord).filter_by(
                    incident_id=incident_id,
                    epcr_id=epcr_record.id
                ).first()
                
                if not existing_billing:
                    billing_record = BillingRecord(
                        org_id=epcr_record.org_id,
                        incident_id=incident_id,
                        epcr_id=epcr_record.id,
                        patient_id=epcr_record.patient_id,
                        status='pending_review',
                        created_at=datetime.utcnow(),
                    )
                    db.add(billing_record)
                    db.commit()
                    logger.info(f"Orchestrator: Created billing record {billing_record.id} for ePCR {epcr_record.id}")
            
            # 2. Notify CAD backend via socket bridge
            try:
                bridge = get_socket_bridge()
                if bridge and bridge.connected:
                    import asyncio
                    billing_data = {
                        'epcr_id': epcr_record.id,
                        'patient_id': epcr_record.patient_id,
                        'incident_number': epcr_record.incident_number,
                    }
                    # Run async in sync context
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, schedule as task
                        asyncio.create_task(bridge.notify_transport_completed(
                            incident_id=str(incident_id) if incident_id else epcr_record.incident_number,
                            epcr_id=str(epcr_record.id),
                            billing_data=billing_data
                        ))
                    else:
                        loop.run_until_complete(bridge.notify_transport_completed(
                            incident_id=str(incident_id) if incident_id else epcr_record.incident_number,
                            epcr_id=str(epcr_record.id),
                            billing_data=billing_data
                        ))
                    logger.info(f"Orchestrator: Notified CAD backend of ePCR completion")
                else:
                    logger.warning(f"Orchestrator: Socket bridge not connected, skipping CAD notification")
            except Exception as e:
                logger.error(f"Orchestrator: Failed to notify CAD backend: {e}", exc_info=True)
            
            # 3. Emit internal event for other services
            emit_event(
                db=db,
                event_type="epcr.finalized",
                event_payload={
                    "epcr_id": epcr_record.id,
                    "patient_id": epcr_record.patient_id,
                    "incident_id": incident_id,
                    "incident_number": epcr_record.incident_number,
                },
                org_id=epcr_record.org_id,
                user_id=user_id,
            )
            
            # 4. Trigger claims workflow if auto-claim enabled
            from core.config import settings
            if getattr(settings, 'AUTO_CLAIM_AFTER_FINALIZE', False):
                try:
                    from services.billing.claims_router import _create_claim_from_epcr
                    _create_claim_from_epcr(db, epcr_record, user_id)
                    logger.info(f"Orchestrator: Auto-created claim for ePCR {epcr_record.id}")
                except Exception as e:
                    logger.error(f"Orchestrator: Failed to auto-create claim: {e}")
            
            logger.info(f"Orchestrator: Successfully processed ePCR {epcr_record.id} finalization")
            
        except Exception as e:
            logger.error(f"Orchestrator: Error processing ePCR finalization: {e}", exc_info=True)
            raise
    
    @staticmethod
    def on_cad_incident_created(db: Session, incident: CADIncident, user_id: int):
        """
        Called when CAD incident is created.
        Triggers:
        1. ePCR stub creation (optional)
        2. Notifications
        3. Assignment engine (if auto-dispatch enabled)
        """
        try:
            logger.info(f"Orchestrator: CAD incident {incident.id} created, triggering integrations")
            
            # 1. Create ePCR stub if configured
            # This pre-populates ePCR with incident data
            try:
                from models.epcr_core import EpcrRecord, EpcrRecordStatus
                from models.patient import Patient
                
                # Check if ePCR stub already exists
                existing_epcr = db.query(EpcrRecord).filter_by(
                    org_id=incident.org_id,
                    incident_number=str(incident.id),
                    status=EpcrRecordStatus.DRAFT
                ).first()
                
                if not existing_epcr:
                    # Create patient stub if needed
                    # Create ePCR stub with incident data
                    epcr_stub = EpcrRecord(
                        org_id=incident.org_id,
                        incident_number=str(incident.id),
                        status=EpcrRecordStatus.DRAFT,
                        custom_fields={
                            'cad_incident_id': incident.id,
                            'transport_type': incident.transport_type,
                            'requesting_facility': incident.requesting_facility,
                            'receiving_facility': incident.receiving_facility,
                        }
                    )
                    db.add(epcr_stub)
                    db.commit()
                    logger.info(f"Orchestrator: Created ePCR stub {epcr_stub.id} for incident {incident.id}")
            except Exception as e:
                logger.warning(f"Orchestrator: Could not create ePCR stub: {e}")
            
            # 2. Notify via socket bridge
            try:
                bridge = get_socket_bridge()
                if bridge and bridge.connected:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(bridge.emit('incident:new', {
                            'incidentId': str(incident.id),
                            'type': incident.transport_type,
                            'address': incident.requesting_facility or '',
                            'priority': incident.priority,
                        }))
                    else:
                        loop.run_until_complete(bridge.emit('incident:new', {
                            'incidentId': str(incident.id),
                            'type': incident.transport_type,
                            'address': incident.requesting_facility or '',
                            'priority': incident.priority,
                        }))
                    logger.info(f"Orchestrator: Notified CAD backend of new incident")
                else:
                    logger.warning(f"Orchestrator: Socket bridge not connected")
            except Exception as e:
                logger.error(f"Orchestrator: Failed to notify CAD backend: {e}", exc_info=True)
            
            logger.info(f"Orchestrator: Successfully processed CAD incident {incident.id} creation")
            
        except Exception as e:
            logger.error(f"Orchestrator: Error processing CAD incident creation: {e}", exc_info=True)
    
    @staticmethod
    def on_transport_completed(db: Session, incident_id: str, epcr_id: Optional[int] = None):
        """
        Called when transport is completed.
        Ensures billing record exists and triggers claims workflow.
        """
        try:
            logger.info(f"Orchestrator: Transport {incident_id} completed")
            
            # Ensure billing record exists
            existing = db.query(BillingRecord).filter_by(incident_id=incident_id).first()
            
            if not existing and epcr_id:
                epcr = db.query(EpcrRecord).filter_by(id=epcr_id).first()
                if epcr:
                    billing_record = BillingRecord(
                        org_id=epcr.org_id,
                        incident_id=incident_id,
                        epcr_id=epcr_id,
                        patient_id=epcr.patient_id,
                        status='pending_review',
                        created_at=datetime.utcnow(),
                    )
                    db.add(billing_record)
                    db.commit()
                    logger.info(f"Orchestrator: Created billing record {billing_record.id}")
            
            # Trigger claims workflow
            if existing or (existing is None and epcr_id):
                emit_event(
                    db=db,
                    event_type="billing.transport_completed",
                    event_payload={
                        "incident_id": incident_id,
                        "epcr_id": epcr_id,
                        "billing_record_id": existing.id if existing else None,
                    },
                    org_id=existing.org_id if existing else None,
                )
            
            logger.info(f"Orchestrator: Successfully processed transport completion")
            
        except Exception as e:
            logger.error(f"Orchestrator: Error processing transport completion: {e}", exc_info=True)
