"""
Fire MDT Offline Queue Service

Handles offline event queue processing with idempotency and retry logic.

Features:
- Idempotent event replay using client_event_id
- Order preservation with out-of-order detection
- Exponential backoff retry logic
- Event deduplication
- Comprehensive error handling
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import asyncio

from models.fire_mdt import (
    FireMDTOfflineQueue,
    FireIncident,
    TimelineEventType,
    TimelineEventSource,
)
from .incident_service import FireIncidentService

logger = logging.getLogger(__name__)


class OfflineQueueService:
    """Offline Queue Service - Process offline events with idempotency"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.incident_service = FireIncidentService(db)

    # ========================================================================
    # Queue Management
    # ========================================================================

    async def enqueue_offline_event(
        self,
        client_event_id: UUID,
        org_id: UUID,
        unit_id: UUID,
        device_id: UUID,
        event_type: str,
        event_time: datetime,
        payload: Dict[str, Any],
    ) -> FireMDTOfflineQueue:
        """
        Add event to offline queue.
        
        Uses client_event_id as idempotency key to prevent duplicates.
        """
        try:
            # Check if event already exists
            existing = await self.get_queue_event_by_client_id(client_event_id)
            if existing:
                logger.info(f"Event {client_event_id} already in queue, skipping")
                return existing

            # Create queue entry
            queue_event = FireMDTOfflineQueue(
                client_event_id=client_event_id,
                org_id=org_id,
                unit_id=unit_id,
                device_id=device_id,
                event_type=event_type,
                event_time=event_time,
                payload=payload,
                retry_count=0,
                processed=False,
            )
            self.db.add(queue_event)
            await self.db.commit()
            await self.db.refresh(queue_event)

            logger.info(f"Enqueued offline event {client_event_id}")
            return queue_event

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to enqueue offline event: {e}")
            raise

    async def get_queue_event_by_client_id(
        self, client_event_id: UUID
    ) -> Optional[FireMDTOfflineQueue]:
        """Get queue event by client event ID (idempotency check)"""
        try:
            result = await self.db.execute(
                select(FireMDTOfflineQueue).where(
                    FireMDTOfflineQueue.client_event_id == client_event_id
                )
            )
            return result.scalar_one_or_none()
        except (SQLAlchemyError, DatabaseError) as e:
            logger.error("Database error while getting queue event by client_id %s: %s", client_event_id, e, exc_info=True)
            return None
        except Exception as e:
            logger.error("Unexpected error while getting queue event by client_id %s: %s", client_event_id, e, exc_info=True)
            return None

    async def get_pending_events(
        self, org_id: Optional[UUID] = None, limit: int = 100
    ) -> List[FireMDTOfflineQueue]:
        """
        Get pending unprocessed events for replay.
        
        Returns events ordered by event_time to preserve chronological order.
        """
        try:
            query = select(FireMDTOfflineQueue).where(
                FireMDTOfflineQueue.processed == False
            )
            
            if org_id:
                query = query.where(FireMDTOfflineQueue.org_id == org_id)
            
            query = query.order_by(FireMDTOfflineQueue.event_time.asc()).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except (SQLAlchemyError, DatabaseError) as e:
            logger.error("Database error while getting pending events (org_id=%s): %s", org_id, e, exc_info=True)
            return []
        except Exception as e:
            logger.error("Unexpected error while getting pending events (org_id=%s): %s", org_id, e, exc_info=True)
            return []

    # ========================================================================
    # Event Processing
    # ========================================================================

    async def process_offline_queue(
        self, org_id: Optional[UUID] = None, batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Process offline event queue with idempotency and retry logic.
        
        Returns processing summary with success/failure counts.
        """
        try:
            pending_events = await self.get_pending_events(org_id, batch_size)

            if not pending_events:
                return {
                    "processed": 0,
                    "success": 0,
                    "failed": 0,
                    "message": "No pending events to process"
                }

            success_count = 0
            failed_count = 0

            for event in pending_events:
                try:
                    # Process individual event
                    success = await self._process_single_event(event)
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        await self._handle_failed_event(event)

                except Exception as e:
                    logger.error(f"Failed to process event {event.client_event_id}: {e}")
                    failed_count += 1
                    await self._handle_failed_event(event, str(e))

            return {
                "processed": len(pending_events),
                "success": success_count,
                "failed": failed_count,
            }

        except Exception as e:
            logger.error(f"Failed to process offline queue: {e}")
            return {"error": str(e)}

    async def _process_single_event(self, queue_event: FireMDTOfflineQueue) -> bool:
        """
        Process a single offline event.
        
        Returns True if successful, False if failed.
        """
        try:
            payload = queue_event.payload
            event_type = queue_event.event_type

            # Get incident ID from payload
            incident_id = payload.get("incident_id")
            if not incident_id:
                logger.error(f"No incident_id in payload for event {queue_event.client_event_id}")
                return False

            # Parse event type
            try:
                timeline_event_type = TimelineEventType(event_type)
            except ValueError:
                logger.error(f"Invalid event type: {event_type}")
                return False

            # Determine source from payload
            source_str = payload.get("source", "manual")
            try:
                source = TimelineEventSource(source_str)
            except ValueError:
                source = TimelineEventSource.MANUAL

            # Record timeline event
            await self.incident_service.record_timeline_event(
                incident_id=UUID(incident_id),
                org_id=queue_event.org_id,
                unit_id=queue_event.unit_id,
                event_type=timeline_event_type,
                event_time=queue_event.event_time,
                source=source,
                lat=payload.get("lat"),
                lng=payload.get("lng"),
                confidence=payload.get("confidence", 90),  # Lower confidence for offline events
                notes=payload.get("notes", "Offline event replayed from queue"),
            )

            # Mark as processed
            queue_event.processed = True
            queue_event.processed_at = datetime.utcnow()
            await self.db.commit()

            logger.info(f"Successfully processed offline event {queue_event.client_event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to process single event: {e}")
            await self.db.rollback()
            return False

    async def _handle_failed_event(
        self, queue_event: FireMDTOfflineQueue, error_message: Optional[str] = None
    ):
        """
        Handle failed event processing with exponential backoff.
        
        Max retries: 5
        Backoff: 2^retry_count minutes
        """
        try:
            queue_event.retry_count += 1
            queue_event.last_attempt_time = datetime.utcnow()
            
            if error_message:
                queue_event.last_error = error_message

            # If max retries exceeded, mark as failed but keep for manual review
            if queue_event.retry_count >= 5:
                logger.warning(
                    f"Event {queue_event.client_event_id} exceeded max retries, "
                    f"marking for manual review"
                )
                queue_event.last_error = (
                    f"{queue_event.last_error or 'Unknown error'} - Max retries exceeded"
                )

            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to handle failed event: {e}")
            await self.db.rollback()

    # ========================================================================
    # Order Detection & Validation
    # ========================================================================

    async def detect_out_of_order_events(
        self, incident_id: UUID, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Detect out-of-order events in timeline.
        
        Compares event_time vs received_time to identify events
        that were recorded after they occurred.
        """
        try:
            from models.fire_mdt import FireIncidentTimeline

            result = await self.db.execute(
                select(FireIncidentTimeline)
                .where(
                    and_(
                        FireIncidentTimeline.incident_id == incident_id,
                        FireIncidentTimeline.org_id == org_id,
                    )
                )
                .order_by(FireIncidentTimeline.event_time.asc())
            )
            events = list(result.scalars().all())

            out_of_order = []
            
            for i in range(len(events)):
                event = events[i]
                
                # Check if event_time is significantly before received_time
                time_diff = (event.received_time - event.event_time).total_seconds()
                
                # Flag if difference is more than 5 minutes
                if time_diff > 300:
                    out_of_order.append({
                        "event_id": str(event.id),
                        "event_type": event.event_type.value,
                        "event_time": event.event_time.isoformat(),
                        "received_time": event.received_time.isoformat(),
                        "delay_seconds": int(time_diff),
                        "likely_offline_replay": True,
                    })

            return out_of_order

        except Exception as e:
            logger.error(f"Failed to detect out-of-order events: {e}")
            return []

    # ========================================================================
    # Retry & Cleanup
    # ========================================================================

    async def retry_failed_events(self, org_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Retry events that failed with exponential backoff.
        
        Only retries events where enough time has passed based on retry count.
        """
        try:
            current_time = datetime.utcnow()
            
            # Get failed events ready for retry
            query = select(FireMDTOfflineQueue).where(
                and_(
                    FireMDTOfflineQueue.processed == False,
                    FireMDTOfflineQueue.retry_count > 0,
                    FireMDTOfflineQueue.retry_count < 5,
                )
            )
            
            if org_id:
                query = query.where(FireMDTOfflineQueue.org_id == org_id)
            
            result = await self.db.execute(query)
            failed_events = list(result.scalars().all())

            retry_count = 0
            
            for event in failed_events:
                # Calculate backoff time: 2^retry_count minutes
                backoff_minutes = 2 ** event.retry_count
                next_retry_time = event.last_attempt_time + timedelta(minutes=backoff_minutes)
                
                # Check if enough time has passed
                if current_time >= next_retry_time:
                    try:
                        success = await self._process_single_event(event)
                        if success:
                            retry_count += 1
                        else:
                            await self._handle_failed_event(event)
                    except Exception as e:
                        logger.error(f"Failed to retry event {event.client_event_id}: {e}")
                        await self._handle_failed_event(event, str(e))

            return {
                "retried": retry_count,
                "total_failed": len(failed_events),
            }

        except Exception as e:
            logger.error(f"Failed to retry failed events: {e}")
            return {"error": str(e)}

    async def cleanup_processed_events(
        self, days_old: int = 30, org_id: Optional[UUID] = None
    ) -> int:
        """
        Clean up old processed events from queue.
        
        Removes events processed more than N days ago.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            query = select(FireMDTOfflineQueue).where(
                and_(
                    FireMDTOfflineQueue.processed == True,
                    FireMDTOfflineQueue.processed_at < cutoff_date,
                )
            )
            
            if org_id:
                query = query.where(FireMDTOfflineQueue.org_id == org_id)
            
            result = await self.db.execute(query)
            old_events = list(result.scalars().all())

            for event in old_events:
                await self.db.delete(event)

            await self.db.commit()
            
            logger.info(f"Cleaned up {len(old_events)} processed events older than {days_old} days")
            return len(old_events)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup processed events: {e}")
            return 0
