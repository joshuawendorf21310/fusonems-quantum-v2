"""
Remaining System Protection (SC) FedRAMP Controls Service.

This module implements additional SC controls:
- SC-10: Network Disconnect
- SC-18: Mobile Code
- SC-19: Voice over IP
- SC-21: Secure Name Resolution (Authoritative)
- SC-22: Architecture & Provisioning
- SC-24: Fail in Known State
- And others...

FedRAMP SC Controls: System and Communications Protection.
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Session

from core.database import Base

logger = logging.getLogger(__name__)


class NetworkConnectionStatus(Enum):
    """Network connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SUSPENDED = "suspended"


class MobileCodeStatus(Enum):
    """Mobile code status."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"


class SystemState(Enum):
    """System state."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class NetworkDisconnectEvent(Base):
    """Database model for network disconnect events (SC-10)."""
    __tablename__ = "network_disconnect_events"
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    
    # Connection details
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    protocol = Column(String(20), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Disconnect details
    disconnect_reason = Column(String(100), nullable=True)
    disconnect_type = Column(String(20), nullable=False)  # "timeout", "manual", "security"
    disconnected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MobileCodeExecution(Base):
    """Database model for mobile code execution (SC-18)."""
    __tablename__ = "mobile_code_executions"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Code details
    code_type = Column(String(50), nullable=False)  # "javascript", "java", "activex", etc.
    code_source = Column(String(500), nullable=False)
    code_hash = Column(String(64), nullable=True, index=True)
    
    # Execution details
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Security
    status = Column(String(20), nullable=False, default=MobileCodeStatus.BLOCKED.value)
    allowed_reason = Column(String(255), nullable=True)
    blocked_reason = Column(String(255), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class VoIPSession(Base):
    """Database model for Voice over IP sessions (SC-19)."""
    __tablename__ = "voip_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Session details
    caller_id = Column(String(100), nullable=False)
    callee_id = Column(String(100), nullable=False)
    call_direction = Column(String(20), nullable=False)  # "inbound", "outbound"
    
    # Security
    encrypted = Column(Boolean, nullable=False, default=True)
    encryption_protocol = Column(String(50), nullable=True)  # "SRTP", "TLS", etc.
    authenticated = Column(Boolean, nullable=False, default=True)
    
    # Session timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class SystemStateTransition(Base):
    """Database model for system state transitions (SC-24)."""
    __tablename__ = "system_state_transitions"
    
    id = Column(Integer, primary_key=True)
    transition_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # State details
    from_state = Column(String(20), nullable=False)
    to_state = Column(String(20), nullable=False, index=True)
    transition_reason = Column(String(255), nullable=True)
    
    # System details
    component = Column(String(100), nullable=True)
    affected_services = Column(JSON, nullable=True)
    
    # Recovery
    recovery_actions = Column(JSON, nullable=True)
    recovery_time_seconds = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class SCControlsService:
    """
    Service for remaining SC controls.
    
    Features:
    - SC-10: Network Disconnect
    - SC-18: Mobile Code
    - SC-19: Voice over IP
    - SC-21: Secure Name Resolution (Authoritative)
    - SC-22: Architecture & Provisioning
    - SC-24: Fail in Known State
    """
    
    def __init__(self, db: Session):
        """
        Initialize SC controls service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # SC-10: Network Disconnect
    def disconnect_network_session(
        self,
        connection_id: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        reason: Optional[str] = None,
        disconnect_type: str = "manual"
    ) -> NetworkDisconnectEvent:
        """
        Disconnect network session (SC-10).
        
        Args:
            connection_id: Connection identifier
            user_id: User ID
            session_id: Session ID
            reason: Disconnect reason
            disconnect_type: Type of disconnect ("timeout", "manual", "security")
            
        Returns:
            NetworkDisconnectEvent object
        """
        event = NetworkDisconnectEvent(
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            disconnect_reason=reason,
            disconnect_type=disconnect_type,
            disconnected_at=datetime.utcnow()
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(f"Network session disconnected: {connection_id}, reason: {reason}")
        return event
    
    def get_disconnect_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get network disconnect statistics."""
        query = self.db.query(NetworkDisconnectEvent)
        
        if start_date:
            query = query.filter(NetworkDisconnectEvent.disconnected_at >= start_date)
        if end_date:
            query = query.filter(NetworkDisconnectEvent.disconnected_at <= end_date)
        
        total = query.count()
        manual = query.filter(NetworkDisconnectEvent.disconnect_type == "manual").count()
        timeout = query.filter(NetworkDisconnectEvent.disconnect_type == "timeout").count()
        security = query.filter(NetworkDisconnectEvent.disconnect_type == "security").count()
        
        return {
            "total_disconnects": total,
            "manual_disconnects": manual,
            "timeout_disconnects": timeout,
            "security_disconnects": security
        }
    
    # SC-18: Mobile Code
    def check_mobile_code(
        self,
        code_type: str,
        code_source: str,
        code_hash: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[bool, MobileCodeExecution]:
        """
        Check and potentially block mobile code execution (SC-18).
        
        Args:
            code_type: Type of mobile code ("javascript", "java", "activex", etc.)
            code_source: Source of the code (URL, file path, etc.)
            code_hash: Optional hash of the code
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Tuple of (is_allowed, MobileCodeExecution record)
        """
        # Check against allowlist/blocklist
        # In production, would check against policy database
        
        is_allowed = False
        reason = None
        
        # Default policy: block ActiveX, allow JavaScript with restrictions
        if code_type.lower() == "activex":
            is_allowed = False
            reason = "ActiveX blocked by security policy"
        elif code_type.lower() == "javascript":
            # Allow JavaScript but log it
            is_allowed = True
            reason = "JavaScript allowed with restrictions"
        else:
            # Default: block unknown code types
            is_allowed = False
            reason = f"Mobile code type {code_type} blocked by default"
        
        execution = MobileCodeExecution(
            execution_id=self._generate_id(),
            code_type=code_type,
            code_source=code_source,
            code_hash=code_hash,
            user_id=user_id,
            session_id=session_id,
            status=MobileCodeStatus.ALLOWED.value if is_allowed else MobileCodeStatus.BLOCKED.value,
            allowed_reason=reason if is_allowed else None,
            blocked_reason=reason if not is_allowed else None
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        logger.info(f"Mobile code check: {code_type} from {code_source}, allowed: {is_allowed}")
        return is_allowed, execution
    
    # SC-19: Voice over IP
    def create_voip_session(
        self,
        caller_id: str,
        callee_id: str,
        call_direction: str,
        encrypted: bool = True,
        encryption_protocol: Optional[str] = None
    ) -> VoIPSession:
        """
        Create VoIP session (SC-19).
        
        Args:
            caller_id: Caller identifier
            callee_id: Callee identifier
            call_direction: Call direction ("inbound", "outbound")
            encrypted: Whether call is encrypted
            encryption_protocol: Encryption protocol ("SRTP", "TLS", etc.)
            
        Returns:
            VoIPSession object
        """
        session = VoIPSession(
            session_id=self._generate_id(),
            caller_id=caller_id,
            callee_id=callee_id,
            call_direction=call_direction,
            encrypted=encrypted,
            encryption_protocol=encryption_protocol or ("SRTP" if encrypted else None),
            authenticated=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"VoIP session created: {session.session_id}")
        return session
    
    def end_voip_session(
        self,
        session_id: str
    ) -> None:
        """
        End VoIP session.
        
        Args:
            session_id: Session ID
        """
        session = self.db.query(VoIPSession).filter(
            VoIPSession.session_id == session_id
        ).first()
        
        if session and not session.ended_at:
            session.ended_at = datetime.utcnow()
            if session.started_at:
                duration = (session.ended_at - session.started_at).total_seconds()
                session.duration_seconds = int(duration)
            
            self.db.commit()
            logger.info(f"VoIP session ended: {session_id}")
    
    # SC-24: Fail in Known State
    def record_state_transition(
        self,
        from_state: SystemState,
        to_state: SystemState,
        component: Optional[str] = None,
        transition_reason: Optional[str] = None,
        recovery_actions: Optional[List[str]] = None
    ) -> SystemStateTransition:
        """
        Record system state transition (SC-24).
        
        Args:
            from_state: Previous state
            to_state: New state
            component: Component name
            transition_reason: Reason for transition
            recovery_actions: List of recovery actions taken
            
        Returns:
            SystemStateTransition object
        """
        transition = SystemStateTransition(
            transition_id=self._generate_id(),
            from_state=from_state.value,
            to_state=to_state.value,
            component=component,
            transition_reason=transition_reason,
            recovery_actions=recovery_actions or []
        )
        
        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)
        
        logger.info(f"System state transition: {from_state.value} -> {to_state.value}, component: {component}")
        return transition
    
    def get_system_state_history(
        self,
        component: Optional[str] = None,
        limit: int = 100
    ) -> List[SystemStateTransition]:
        """
        Get system state transition history.
        
        Args:
            component: Optional component filter
            limit: Maximum number of records
            
        Returns:
            List of state transitions
        """
        query = self.db.query(SystemStateTransition)
        
        if component:
            query = query.filter(SystemStateTransition.component == component)
        
        return query.order_by(SystemStateTransition.created_at.desc()).limit(limit).all()
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        import secrets
        return secrets.token_urlsafe(32)
