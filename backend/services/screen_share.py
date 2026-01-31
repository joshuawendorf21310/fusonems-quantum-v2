
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List
import redis
import json
import os
import jwt
from jwt import PyJWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import require_roles
from models.user import User

router = APIRouter()

# Use Redis for session persistence
r = redis.Redis.from_url(settings.REDIS_URL)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        self.active_connections[session_id][user_id] = websocket

    def disconnect(self, session_id: str, user_id: str):
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            del self.active_connections[session_id][user_id]

    async def broadcast(self, session_id: str, message: str, sender_id: str):
        if session_id in self.active_connections:
            for user_id, connection in self.active_connections[session_id].items():
                if user_id != sender_id:
                    await connection.send_text(message)

manager = ConnectionManager()

async def get_current_user_from_query(token: str = Query(None), db: Session = Depends(get_db)) -> User:
    """Dependency to get user from a token in the query string for WebSockets."""
    credentials_exception = WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Could not validate credentials")
    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# Helper functions
def get_session_key(session_id):
    return f"screen_share:session:{session_id}"

def get_viewer_key(session_id):
    return f"screen_share:viewers:{session_id}"

def get_permissions_key(session_id):
    return f"screen_share:permissions:{session_id}"

# WebSocket signaling endpoint
@router.websocket("/ws/screen-share/{session_id}")
async def screen_share_ws(websocket: WebSocket, session_id: str, user: User = Depends(get_current_user_from_query)):
    user_identifier = user.email  # Use email as a consistent identifier
    await manager.connect(session_id, user_identifier, websocket)
    # Add viewer to Redis set
    r.sadd(get_viewer_key(session_id), user_identifier)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all viewers except sender
            await manager.broadcast(session_id, data, user_identifier)
    except WebSocketDisconnect:
        manager.disconnect(session_id, user_identifier)
        r.srem(get_viewer_key(session_id), user_identifier)

# REST endpoints for session management
class SessionInfo(BaseModel):
    session_id: str
    owner: str
    viewers: List[str] = []
    permissions: Dict[str, str] = {}

@router.post("/api/screen-share/session")
async def create_session(info: SessionInfo, user: User = Depends(require_roles())):
    # Set owner from authenticated user to prevent impersonation
    info.owner = user.email
    r.set(get_session_key(info.session_id), info.model_dump_json())
    r.sadd(get_viewer_key(info.session_id), info.owner)
    if info.permissions:
        r.hset(get_permissions_key(info.session_id), mapping=info.permissions)
    return {"status": "created", "session": info}

@router.get("/api/screen-share/session/{session_id}")
async def get_session(session_id: str, user: User = Depends(require_roles())):
    session = r.get(get_session_key(session_id))
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return json.loads(session)

@router.post("/api/screen-share/session/{session_id}/permissions")
async def update_permissions(session_id: str, perms: Dict[str, str], user: User = Depends(require_roles())):
    session_raw = r.get(get_session_key(session_id))
    if not session_raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session_info = SessionInfo.model_validate_json(session_raw)
    if session_info.owner != user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the session owner can update permissions")

    if perms:
        r.hset(get_permissions_key(session_id), mapping=perms)
    return {"status": "updated", "permissions": perms}

@router.get("/api/screen-share/session/{session_id}/viewers")
async def get_viewers(session_id: str, user: User = Depends(require_roles())):
    viewers = r.smembers(get_viewer_key(session_id))
    return [v.decode() for v in viewers]
