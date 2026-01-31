import uuid
import re
import base64
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.crypto import (
    is_fips_enabled,
    derive_key_pbkdf2,
    get_random_bytes,
    hash_sha256
)
from utils.audit import record_audit
from models.time import DeviceClockDrift
from models.device_trust import DeviceTrust
from models.scheduling import Shift
from models.organization import Organization
from models.user import User, UserRole
from models.auth_session import AuthSession
from services.auth.session_management_service import SessionManagementService
from services.auth.lockout_middleware import check_account_locked

# Initialize password context with multiple schemes for backward compatibility
# Priority: pbkdf2_sha256 (FIPS approved) > bcrypt > argon2
schemes = []
if getattr(settings, "PASSWORD_HASH_ALGORITHM", "auto") == "pbkdf2":
    schemes = ["pbkdf2_sha256"]
elif getattr(settings, "PASSWORD_HASH_ALGORITHM", "auto") == "argon2":
    schemes = ["argon2"]
elif getattr(settings, "PASSWORD_HASH_ALGORITHM", "auto") == "bcrypt":
    schemes = ["bcrypt"]
else:
    # Auto mode: prefer FIPS-compliant if available
    if is_fips_enabled():
        schemes = ["pbkdf2_sha256", "bcrypt"]
    else:
        schemes = ["bcrypt", "pbkdf2_sha256"]

pwd_context = CryptContext(schemes=schemes, deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def validate_password_complexity(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password complexity requirements (FedRAMP IA-5).
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    min_length = getattr(settings, "PASSWORD_MIN_LENGTH", 14)
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    require_upper = getattr(settings, "PASSWORD_REQUIRE_UPPERCASE", True)
    require_lower = getattr(settings, "PASSWORD_REQUIRE_LOWERCASE", True)
    require_digits = getattr(settings, "PASSWORD_REQUIRE_DIGITS", True)
    require_special = getattr(settings, "PASSWORD_REQUIRE_SPECIAL", True)
    
    if require_upper and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if require_lower and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if require_digits and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    
    return True, None


def hash_password(password: str) -> str:
    """
    Hash password using FIPS-compliant algorithm when available.
    
    Uses PBKDF2-SHA256 (FIPS approved) when FIPS mode is enabled,
    otherwise falls back to bcrypt for backward compatibility.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Validate password complexity (FedRAMP IA-5)
    is_valid, error_msg = validate_password_complexity(password)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Determine which algorithm to use
    algorithm = getattr(settings, "PASSWORD_HASH_ALGORITHM", "auto")
    fips_enabled = is_fips_enabled()
    
    if algorithm == "pbkdf2" or (algorithm == "auto" and fips_enabled):
        # Use PBKDF2-SHA256 (FIPS approved)
        return _hash_password_pbkdf2(password)
    elif algorithm == "argon2":
        # Use Argon2 (not FIPS approved, but secure)
        return pwd_context.hash(password)
    else:
        # Default to bcrypt (backward compatibility)
        return pwd_context.hash(password)


def _hash_password_pbkdf2(password: str) -> str:
    """
    Hash password using PBKDF2-SHA256 (FIPS approved).
    
    Format: $pbkdf2-sha256$<iterations>$<salt>$<hash>
    
    Args:
        password: Plain text password
        
    Returns:
        PBKDF2 hash string
    """
    iterations = getattr(settings, "PBKDF2_ITERATIONS", 100000)
    salt = get_random_bytes(16)  # 128-bit salt
    
    # Derive key using PBKDF2
    key = derive_key_pbkdf2(
        password.encode("utf-8"),
        salt,
        iterations=iterations,
        key_length=32,
        hash_algorithm="sha256"
    )
    
    # Format: $pbkdf2-sha256$<iterations>$<salt_b64>$<hash_b64>
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(key).decode("utf-8")
    
    return f"$pbkdf2-sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Supports multiple hash formats:
    - PBKDF2-SHA256 (FIPS approved)
    - bcrypt (backward compatibility)
    - Argon2
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password string
        
    Returns:
        True if password matches, False otherwise
    """
    # Check if it's a PBKDF2 hash
    if hashed_password.startswith("$pbkdf2-sha256$"):
        return _verify_password_pbkdf2(plain_password, hashed_password)
    
    # Use passlib for other formats (bcrypt, argon2)
    return pwd_context.verify(plain_password, hashed_password)


def _verify_password_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against PBKDF2-SHA256 hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: PBKDF2 hash string
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Parse format: $pbkdf2-sha256$<iterations>$<salt_b64>$<hash_b64>
        parts = hashed_password.split("$")
        if len(parts) != 5 or parts[1] != "pbkdf2-sha256":
            return False
        
        iterations = int(parts[2])
        salt = base64.b64decode(parts[3])
        stored_hash = base64.b64decode(parts[4])
        
        # Derive key using same parameters
        derived_key = derive_key_pbkdf2(
            plain_password.encode("utf-8"),
            salt,
            iterations=iterations,
            key_length=32,
            hash_algorithm="sha256"
        )
        
        # Constant-time comparison
        return hmac.compare_digest(derived_key, stored_hash)
    
    except (ValueError, IndexError, base64.binascii.Error):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Create JWT access token. Returns tuple of (token, expiration_datetime)"""
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + (
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
            
            # Check session timeout (FedRAMP AC-11/AC-12)
            is_valid, reason = SessionManagementService.check_session_timeout(session)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Session invalid: {reason}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update session activity (FedRAMP AC-11)
            SessionManagementService.update_session_activity(db=db, session=session, request=request)
            
    except JWTError as exc:
        raise credentials_exception from exc
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    
    # Check if account is locked (FedRAMP AC-7)
    check_account_locked(db, user.id)
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
                device.last_seen = datetime.now(timezone.utc)
                db.commit()
                trusted_flag = device.trusted
            else:
                trusted_flag = False
        request.state.device_trusted = trusted_flag
        shifts_exist = db.query(Shift).filter(Shift.org_id == user.org_id).count() > 0
        active_shift = None
        if shifts_exist:
            now = datetime.now(timezone.utc)
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


async def get_current_user_ws(websocket, db: Session) -> User:
    """
    Get current user from WebSocket connection. Raises exception on authentication failure.
    """
    token = websocket.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        try:
            user_id = uuid.UUID(str(user_id))
        except (TypeError, ValueError):
            user_id = str(user_id)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        ) from exc
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
