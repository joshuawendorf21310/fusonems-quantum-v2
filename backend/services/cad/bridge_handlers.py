"""
Socket Bridge Event Handlers
Processes events from CAD backend and integrates with FastAPI services.
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_db
from models import Dispatch, Unit, BillingRecord
from utils.logger import logger
from services.notifications.notification_service import send_notification


async def handle_unit_location_updated(data: Dict[str, Any]):
    """
    Handle unit location updates from CAD backend.
    Store in database and trigger location-based rules.
    """
    try:
        unit_id = data.get('unitId')
        location = data.get('location')
        heading = data.get('heading')
        speed = data.get('speed')
        
        logger.debug(f"Processing location update for unit {unit_id}")
        
        # Update unit location in FastAPI database if needed
        # This allows FastAPI services to query unit locations
        
        # Trigger location-based automations
        # Example: ETA calculations, geofencing, etc.
        
    except Exception as e:
        logger.error(f"Error handling unit location update: {e}", exc_info=True)


async def handle_unit_status_updated(data: Dict[str, Any]):
    """
    Handle unit status updates from CAD backend.
    Update local records and trigger status-based workflows.
    """
    try:
        unit_id = data.get('unitId')
        status = data.get('status')
        incident_id = data.get('incidentId')
        
        logger.info(f"Processing status update for unit {unit_id}: {status}")
        
        # Update unit status in FastAPI database
        # Trigger workflows based on status changes
        # Example: When unit goes "available", check for pending assignments
        
        if status == 'available':
            logger.debug(f"Unit {unit_id} is now available for assignment")
            # Could trigger auto-dispatch logic here
            
    except Exception as e:
        logger.error(f"Error handling unit status update: {e}", exc_info=True)


async def handle_incident_status_updated(data: Dict[str, Any]):
    """
    Handle incident status updates from CAD backend.
    Sync with ePCR and billing systems.
    """
    try:
        incident_id = data.get('incidentId')
        status = data.get('status')
        
        logger.info(f"Processing incident status update: {incident_id} -> {status}")
        
        # Sync with ePCR system
        if status == 'completed':
            # Trigger ePCR finalization workflow and billing
            logger.info(f"Incident {incident_id} completed, triggering ePCR workflow")
            try:
                from services.integration.orchestrator import ServiceOrchestrator
                db = next(get_db())
                try:
                    ServiceOrchestrator.on_transport_completed(db, str(incident_id), None)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Orchestrator error: {e}", exc_info=True)
            
        elif status == 'cancelled':
            # Handle cancelled incidents
            logger.info(f"Incident {incident_id} cancelled")
            
    except Exception as e:
        logger.error(f"Error handling incident status update: {e}", exc_info=True)


async def handle_incident_timestamp_updated(data: Dict[str, Any]):
    """
    Handle incident timestamp updates from CAD backend.
    Store timestamps for billing and reporting.
    """
    try:
        incident_id = data.get('incidentId')
        field = data.get('field')
        timestamp = data.get('timestamp')
        location = data.get('location')
        
        logger.debug(f"Processing timestamp update: {incident_id}.{field} = {timestamp}")
        
        # Store timestamps for accurate billing
        # These timestamps are critical for claims
        
    except Exception as e:
        logger.error(f"Error handling incident timestamp update: {e}", exc_info=True)


async def handle_incident_new(data: Dict[str, Any]):
    """
    Handle new incident creation from CAD backend.
    Trigger notifications and initial workflows.
    """
    try:
        incident_id = data.get('incidentId')
        incident_type = data.get('type')
        address = data.get('address')
        priority = data.get('priority')
        
        logger.info(f"New incident created: {incident_id} ({incident_type}) at {address}")
        
        # Trigger incident notifications
        # Could notify supervisors, create ePCR stub, etc.
        
        if priority == 1:
            logger.warning(f"High priority incident: {incident_id}")
            # Send urgent notifications
            
    except Exception as e:
        logger.error(f"Error handling new incident: {e}", exc_info=True)


async def handle_assignment_received(data: Dict[str, Any]):
    """
    Handle assignment confirmation from CAD backend.
    Update assignment status and notify relevant parties.
    """
    try:
        assignment_id = data.get('assignmentId')
        unit_id = data.get('unitId')
        incident_id = data.get('incidentId')
        
        logger.info(f"Assignment confirmed: {assignment_id} (Unit: {unit_id}, Incident: {incident_id})")
        
        # Update assignment record
        # Notify crew and dispatch
        
    except Exception as e:
        logger.error(f"Error handling assignment received: {e}", exc_info=True)


async def handle_transport_completed(data: Dict[str, Any]):
    """
    Handle transport completion from CAD backend.
    Create billing record and trigger claims workflow.
    Uses ServiceOrchestrator to ensure all services work together.
    """
    # Validate required fields
    incident_id = data.get('incidentId')
    if not incident_id:
        logger.error("Missing incidentId in transport_completed event")
        return
    
    epcr_id = data.get('epcrId')
    billing_data = data.get('billingData', {})
    
    logger.info(
        "Transport completed",
        extra={
            "incident_id": incident_id,
            "epcr_id": epcr_id,
        }
    )
    
    # Use orchestrator to ensure all services work together
    db = None
    try:
        db = next(get_db())
        
        db = None
        try:
            from services.integration.orchestrator import ServiceOrchestrator
            ServiceOrchestrator.on_transport_completed(db, str(incident_id), epcr_id)
            logger.info(f"Orchestrator processed transport completion for incident {incident_id}")
        except Exception as orchestrator_error:
            logger.error(f"Orchestrator error: {orchestrator_error}", exc_info=True)
            # Fallback to direct billing record creation
            existing = db.query(BillingRecord).filter_by(incident_id=incident_id).first()
            if not existing:
                billing_record = BillingRecord(
                    incident_id=incident_id,
                    epcr_id=epcr_id,
                    status='pending_review',
                    created_at=datetime.utcnow(),
                    **billing_data
                )
                db.add(billing_record)
                db.commit()
                
                logger.info(f"Billing record created for incident {incident_id}")
                
                # Trigger billing workflow
                # This could include:
                # - Validation of billing data
                # - Insurance verification
                # - Claims submission preparation
                
            else:
                logger.info(f"Billing record already exists for incident {incident_id}")
                
        except Exception as db_error:
            logger.error(f"Database error creating billing record: {db_error}", exc_info=True)
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
            
    except Exception as e:
        logger.error(
            "Error handling transport completed",
            extra={"incident_id": incident_id, "error": str(e)},
            exc_info=True
        )
    finally:
        if db:
            db.close()


async def handle_metrics_updated(data: Dict[str, Any]):
    """
    Handle real-time metrics updates from CAD backend.
    Store and broadcast to founder dashboard.
    """
    try:
        metrics = data.get('metrics', {})
        timestamp = data.get('timestamp')
        
        logger.debug(f"Metrics updated: {len(metrics)} metrics at {timestamp}")
        
        # Store metrics in time-series database or cache
        # Broadcast to founder dashboard via WebSocket
        
        # Examples of metrics:
        # - Active incidents
        # - Available units
        # - Average response time
        # - Revenue today
        # - ePCRs completed
        
    except Exception as e:
        logger.error(f"Error handling metrics update: {e}", exc_info=True)


def register_bridge_event_handlers(bridge):
    """
    Register all event handlers with the socket bridge.
    Call this during application startup.
    """
    bridge.on('unit:location:updated', handle_unit_location_updated)
    bridge.on('unit:status:updated', handle_unit_status_updated)
    bridge.on('incident:status:updated', handle_incident_status_updated)
    bridge.on('incident:timestamp:updated', handle_incident_timestamp_updated)
    bridge.on('incident:new', handle_incident_new)
    bridge.on('assignment:received', handle_assignment_received)
    bridge.on('transport:completed', handle_transport_completed)
    bridge.on('metrics:updated', handle_metrics_updated)
    
    logger.info("✓ Socket bridge event handlers registered")
