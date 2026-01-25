from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional

from sqlalchemy.orm import Session

from models.event import EventLog

EventHandler = Callable[[EventLog], None]


@dataclass
class EventBus:
    handlers: Dict[str, list[EventHandler]] = field(default_factory=dict)

    def register(self, event_type: str, handler: EventHandler) -> None:
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(
        self,
        db: Session,
        org_id: str,
        event_type: str,
        payload: dict[str, Any],
        actor_id: Optional[str] = None,
        actor_role: str = "",
        idempotency_key: Optional[str] = None,
        device_id: str = "",
        server_time=None,
        drift_seconds: int = 0,
        drifted: bool = False,
        training_mode: bool = False,
        schema_name: str = "public",
    ) -> EventLog:
        if idempotency_key:
            existing = (
                db.query(EventLog)
                .filter(EventLog.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                return existing
        record = EventLog(
            org_id=str(org_id),
            event_type=event_type,
            payload=payload,
            actor_id=str(actor_id) if actor_id is not None else None,
            actor_role=actor_role,
            idempotency_key=idempotency_key,
            device_id=device_id,
            server_time=server_time,
            drift_seconds=drift_seconds,
            drifted=drifted,
            training_mode=training_mode,
            schema_name=schema_name,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        for handler in self.handlers.get(event_type, []):
            handler(record)
        return record

    def replay(
        self,
        db: Session,
        org_id: str,
        event_types: Optional[Iterable[str]] = None,
        training_mode: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        query = db.query(EventLog).filter(EventLog.org_id == org_id)
        if training_mode is not None:
            query = query.filter(EventLog.training_mode == training_mode)
        if event_types:
            query = query.filter(EventLog.event_type.in_(list(event_types)))
        events = query.order_by(EventLog.created_at.asc()).all()
        results = []
        for event in events:
            for handler in self.handlers.get(event.event_type, []):
                handler(event)
            results.append({"event_id": event.id, "event_type": event.event_type, "status": "replayed"})
        return results


event_bus = EventBus()
