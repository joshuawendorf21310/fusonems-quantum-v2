from datetime import datetime, timedelta
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from utils.audit import record_audit
from models.time import DeviceClockDrift
from models.device_trust import DeviceTrust
from models.scheduling import Shift
from models.organization import Organization
from models.user import User, UserRole
from models.auth_session import AuthSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Create JWT access token. Returns tuple of (token, expiration_datetime)"""
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    # sid and jti should be provided in data dict
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return token, expire


def _resolve_token(request: Request, token: Optional[str]) -> Optional[str]:
    if token:
        return token
    if request is None:
        return None
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    resolved_token = _resolve_token(request, token)
    if not resolved_token:
        raise credentials_exception
    try:
        payload = jwt.decode(resolved_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        token_org = payload.get("org")
        token_jti = payload.get("jti")
        request_mfa = payload.get("mfa", False)
        device_trusted = payload.get("device_trusted", True)
        on_shift = payload.get("on_shift", True)
        if user_id is None:
            raise credentials_exception
        try:
            user_id = uuid.UUID(str(user_id))
        except (TypeError, ValueError):
            user_id = str(user_id)
        
        # Validate session if jti is present
        if token_jti:
            session = db.query(AuthSession).filter(AuthSession.jwt_jti == token_jti).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if session is revoked
            if session.revoked_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if session is expired
            if session.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last_seen_at
            session.last_seen_at = datetime.utcnow()
            db.commit()
            
    except JWTError as exc:
        raise credentials_exception from exc
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    if user.org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization missing")
    org = db.query(Organization).filter(Organization.id == user.org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization missing")
    if request is not None:
        request.state.org_lifecycle = getattr(org, "lifecycle_state", "ACTIVE")
        org_training_mode = getattr(org, "training_mode", None)
        request.state.training_mode = (
            org_training_mode == "ENABLED" or getattr(user, "training_mode", False)
        )
        request.state.mfa_verified = bool(request_mfa)
        device_id = request.headers.get("x-device-id", "")
        trusted_flag = bool(device_trusted)
        if device_id:
            device = (
                db.query(DeviceTrust)
                .filter(
                    DeviceTrust.org_id == user.org_id,
                    DeviceTrust.user_id == user.id,
                    DeviceTrust.device_id == device_id,
                )
                .first()
            )
            if device:
                device.last_seen = datetime.utcnow()
                db.commit()
                trusted_flag = device.trusted
            else:
                trusted_flag = False
        request.state.device_trusted = trusted_flag
        shifts_exist = db.query(Shift).filter(Shift.org_id == user.org_id).count() > 0
        active_shift = None
        if shifts_exist:
            now = datetime.utcnow()
            active_shift = (
                db.query(Shift)
                .filter(
                    Shift.org_id == user.org_id,
                    Shift.shift_start <= now,
                    Shift.shift_end >= now,
                )
                .first()
            )
        request.state.on_shift = bool(active_shift) if shifts_exist else True
    lifecycle = getattr(org, "lifecycle_state", None) or "ACTIVE"
    if lifecycle == "TERMINATED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ORG_TERMINATED")
    if lifecycle == "SUSPENDED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ORG_SUSPENDED")
    if lifecycle in {"PAST_DUE", "READ_ONLY"} and request is not None:
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ORG_READ_ONLY")
        if token_org is not None and str(user.org_id) != str(token_org):
            if request is not None:
                record_audit(
                    db=db,
                    request=request,
                    user=user,
                    action="token-org-mismatch",
                    resource="auth",
                    outcome="Blocked",
                    classification="NON_PHI",
                    training_mode=getattr(request.state, "training_mode", False),
                    reason_code="TOKEN_ORG_MISMATCH",
                )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Org mismatch")
    if request is not None:
        request.state.user = user
        device_id = request.headers.get("x-device-id", "")
        drift_seconds = getattr(request.state, "drift_seconds", 0)
        drifted = getattr(request.state, "drifted", False)
        device_time = getattr(request.state, "device_time", None)
        server_time = getattr(request.state, "server_time", None)
        if device_id and drifted:
            db.add(
                DeviceClockDrift(
                    org_id=user.org_id,
                    device_id=device_id,
                    drift_seconds=drift_seconds,
                    device_time=device_time,
                    server_time=server_time,
                )
            )
            db.commit()
    return user


def require_roles(*roles: UserRole):
    def _require(user: User = Depends(get_current_user)) -> User:
        allowed = {role.value for role in roles}
        if roles and user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _require


def require_mfa(user: User = Depends(get_current_user), request: Request = None) -> User:
    if settings.ENV != "production":
        return user
    if request is not None and not getattr(request.state, "mfa_verified", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA_REQUIRED")
    return user


def require_trusted_device(user: User = Depends(get_current_user), request: Request = None) -> User:
    if request is not None and not getattr(request.state, "device_trusted", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="DEVICE_NOT_TRUSTED")
    return user


def require_on_shift(user: User = Depends(get_current_user), request: Request = None) -> User:
    if request is not None and not getattr(request.state, "on_shift", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OFF_SHIFT")
    return user
