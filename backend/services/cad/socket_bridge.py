"""
Socket.io Bridge Service
Connects FastAPI backend to CAD Node.js backend for unified real-time communication.
"""
import asyncio
import socketio
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from utils.logger import logger
from core.config import settings


class SocketBridge:
    """
    Socket.io client bridge for FastAPI backend.
    Connects to CAD backend and manages bidirectional event flow.
    """
    
    def __init__(self):
        self.sio: Optional[socketio.AsyncClient] = None
        self.connected: bool = False
        self.reconnect_task: Optional[asyncio.Task] = None
        self.event_handlers: Dict[str, list[Callable]] = {}
        self.connection_attempts: int = 0
        self.max_reconnect_attempts: int = 10
        self.reconnect_delay: int = 5
        self.last_connection_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
        # CAD backend configuration
        self.cad_url = getattr(settings, 'CAD_BACKEND_URL', 'http://localhost:3000')
        self.auth_token = getattr(settings, 'CAD_BACKEND_AUTH_TOKEN', '')
        
    async def initialize(self):
        """Initialize the Socket.io client"""
        if self.sio is not None:
            logger.warning("Socket bridge already initialized")
            return
            
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=self.max_reconnect_attempts,
            reconnection_delay=self.reconnect_delay,
            logger=False,
            engineio_logger=False
        )
        
        # Register internal event handlers
        self._register_internal_handlers()
        
        logger.info(f"Socket bridge initialized, targeting {self.cad_url}")
        
    def _register_internal_handlers(self):
        """Register internal Socket.io event handlers"""
        
        @self.sio.event
        async def connect():
            self.connected = True
            self.connection_attempts = 0
            self.last_connection_time = datetime.utcnow()
            self.last_error = None
            logger.info(f"✓ Socket bridge connected to CAD backend at {self.cad_url}")
            
            # Authenticate with CAD backend
            if self.auth_token:
                await self.emit('fastapi:authenticate', {'token': self.auth_token})
                
        @self.sio.event
        async def connect_error(data):
            self.connected = False
            self.last_error = str(data)
            self.connection_attempts += 1
            logger.error(f"Socket bridge connection error (attempt {self.connection_attempts}): {data}")
            
        @self.sio.event
        async def disconnect():
            self.connected = False
            logger.warning("Socket bridge disconnected from CAD backend")
            
        # CAD Backend → FastAPI events
        @self.sio.on('unit:location:updated')
        async def on_unit_location_updated(data):
            logger.debug(f"Unit location updated: {data.get('unitId')}")
            await self._dispatch_event('unit:location:updated', data)
            
        @self.sio.on('unit:status:updated')
        async def on_unit_status_updated(data):
            logger.info(f"Unit status updated: {data.get('unitId')} -> {data.get('status')}")
            await self._dispatch_event('unit:status:updated', data)
            
        @self.sio.on('incident:status:updated')
        async def on_incident_status_updated(data):
            logger.info(f"Incident status updated: {data.get('incidentId')} -> {data.get('status')}")
            await self._dispatch_event('incident:status:updated', data)
            
        @self.sio.on('incident:timestamp:updated')
        async def on_incident_timestamp_updated(data):
            logger.debug(f"Incident timestamp updated: {data.get('incidentId')}")
            await self._dispatch_event('incident:timestamp:updated', data)
            
        @self.sio.on('incident:new')
        async def on_incident_new(data):
            logger.info(f"New incident created: {data.get('incidentId')}")
            await self._dispatch_event('incident:new', data)
            
        @self.sio.on('assignment:received')
        async def on_assignment_received(data):
            logger.info(f"Assignment received: {data.get('assignmentId')}")
            await self._dispatch_event('assignment:received', data)
            
        # Billing events
        @self.sio.on('transport:completed')
        async def on_transport_completed(data):
            logger.info(f"Transport completed: {data.get('incidentId')}")
            await self._dispatch_event('transport:completed', data)
            
        # Founder dashboard events
        @self.sio.on('metrics:updated')
        async def on_metrics_updated(data):
            logger.debug("Real-time metrics updated")
            await self._dispatch_event('metrics:updated', data)
            
    async def _dispatch_event(self, event_name: str, data: Any):
        """Dispatch event to registered handlers"""
        handlers = self.event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error dispatching event {event_name}: {e}", exc_info=True)
                
    def on(self, event_name: str, handler: Callable):
        """Register an event handler"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
        logger.debug(f"Registered handler for event: {event_name}")
        
    def off(self, event_name: str, handler: Optional[Callable] = None):
        """Unregister an event handler"""
        if handler is None:
            # Remove all handlers for this event
            if event_name in self.event_handlers:
                del self.event_handlers[event_name]
        else:
            # Remove specific handler
            handlers = self.event_handlers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)
                
    async def connect(self):
        """Connect to CAD backend"""
        if not self.sio:
            await self.initialize()
            
        if self.connected:
            logger.warning("Socket bridge already connected")
            return
            
        try:
            logger.info(f"Connecting to CAD backend at {self.cad_url}...")
            # Add timeout to prevent hanging
            import asyncio
            await asyncio.wait_for(
                self.sio.connect(
                    self.cad_url,
                    auth={'token': self.auth_token} if self.auth_token else None,
                    transports=['websocket', 'polling'],
                    wait_timeout=10  # 10 second timeout
                ),
                timeout=15.0  # Overall timeout
            )
            logger.info(f"✓ Successfully connected to CAD backend at {self.cad_url}")
        except asyncio.TimeoutError:
            self.last_error = "Connection timeout"
            logger.error(f"Connection to CAD backend timed out after 15 seconds")
            raise
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect to CAD backend: {e}", exc_info=True)
            # Don't raise - allow graceful degradation
            logger.warning("Application will continue without CAD backend connection")
            
    async def disconnect(self):
        """Disconnect from CAD backend"""
        if self.sio and self.connected:
            await self.sio.disconnect()
            self.connected = False
            logger.info("Socket bridge disconnected")
            
    async def emit(self, event: str, data: Any = None):
        """Emit an event to CAD backend"""
        if not self.connected:
            logger.warning(f"Cannot emit event {event}: not connected")
            return False
            
        try:
            await self.sio.emit(event, data)
            logger.debug(f"Emitted event: {event}")
            return True
        except Exception as e:
            logger.error(f"Error emitting event {event}: {e}", exc_info=True)
            return False
            
    # High-level API methods for common operations
    
    async def send_assignment(self, unit_id: str, incident_data: Dict[str, Any]):
        """Send new assignment from FastAPI to CAD backend"""
        return await self.emit('assignment:sent', {
            'unitId': unit_id,
            'incident': incident_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    async def update_unit_location(self, unit_id: str, location: Dict[str, Any], heading: Optional[float] = None, speed: Optional[float] = None):
        """Update unit GPS location"""
        return await self.emit('unit:location', {
            'unitId': unit_id,
            'location': location,
            'heading': heading,
            'speed': speed
        })
        
    async def update_unit_status(self, unit_id: str, status: str, incident_id: Optional[str] = None):
        """Update unit availability status"""
        return await self.emit('unit:status', {
            'unitId': unit_id,
            'status': status,
            'incidentId': incident_id
        })
        
    async def update_incident_status(self, incident_id: str, status: str, user_id: str):
        """Update incident status"""
        return await self.emit('incident:status', {
            'incidentId': incident_id,
            'status': status,
            'userId': user_id
        })
        
    async def record_incident_timestamp(self, incident_id: str, field: str, timestamp: str, location: Optional[Dict[str, Any]] = None, source: str = 'manual'):
        """Record incident timestamp (enroute, onscene, etc.)"""
        return await self.emit('incident:timestamp', {
            'incidentId': incident_id,
            'field': field,
            'timestamp': timestamp,
            'location': location,
            'source': source
        })
        
    async def notify_transport_completed(self, incident_id: str, epcr_id: str, billing_data: Dict[str, Any]):
        """Notify billing system when transport completes"""
        return await self.emit('transport:completed', {
            'incidentId': incident_id,
            'epcrId': epcr_id,
            'billingData': billing_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    async def broadcast_metrics_update(self, metrics: Dict[str, Any]):
        """Broadcast real-time metrics to founder dashboard"""
        return await self.emit('metrics:updated', {
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    async def join_room(self, room: str):
        """Join a Socket.io room for targeted messaging"""
        if room.startswith('unit:'):
            await self.emit('join:unit', room.replace('unit:', ''))
        elif room.startswith('incident:'):
            await self.emit('join:incident', room.replace('incident:', ''))
            
    async def leave_room(self, room: str):
        """Leave a Socket.io room"""
        if room.startswith('unit:'):
            await self.emit('leave:unit', room.replace('unit:', ''))
        elif room.startswith('incident:'):
            await self.emit('leave:incident', room.replace('incident:', ''))
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the socket bridge"""
        return {
            'connected': self.connected,
            'cad_url': self.cad_url,
            'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'connection_attempts': self.connection_attempts,
            'last_error': self.last_error,
            'event_handlers_registered': len(self.event_handlers),
            'uptime_seconds': (datetime.utcnow() - self.last_connection_time).total_seconds() if self.last_connection_time and self.connected else 0
        }
        

# Global singleton instance
_socket_bridge: Optional[SocketBridge] = None


def get_socket_bridge() -> SocketBridge:
    """Get the global socket bridge instance"""
    global _socket_bridge
    if _socket_bridge is None:
        _socket_bridge = SocketBridge()
    return _socket_bridge


async def initialize_socket_bridge():
    """Initialize and connect the socket bridge"""
    bridge = get_socket_bridge()
    await bridge.initialize()
    
    try:
        await bridge.connect()
        logger.info("✓ Socket bridge initialized and connected")
    except Exception as e:
        logger.error(f"Failed to connect socket bridge: {e}")
        # Don't fail startup if CAD backend is not available
        logger.warning("Socket bridge will retry connection in background")


async def shutdown_socket_bridge():
    """Shutdown the socket bridge"""
    global _socket_bridge
    if _socket_bridge:
        await _socket_bridge.disconnect()
        _socket_bridge = None
        logger.info("Socket bridge shutdown complete")
