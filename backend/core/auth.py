from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.session import Session as UserSession
from models.user import User, UserRole


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(
    subject: str,
    org_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, datetime]:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(subject),
        "org": str(org_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return token, expire


def _resolve_token(request: Request, token: Optional[str]) -> Optional[str]:
    if token:
        return token
    if request is None:
        return None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    resolved = _resolve_token(request, token)
    if not resolved:
        raise credentials_exception
    try:
        payload = jwt.decode(resolved, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
        try:
            user_id = uuid.UUID(str(user_id))
        except (TypeError, ValueError):
            user_id = str(user_id)
    except JWTError as exc:
        raise credentials_exception from exc
    session = db.query(UserSession).filter(UserSession.token == resolved).first()
    if not session or session.expires_at < datetime.utcnow():
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user


def get_current_user_from_request(request: Request, db: Session) -> User:
    return get_current_user(token=None, db=db, request=request)


def get_token_from_request(request: Request) -> Optional[str]:
    return _resolve_token(request, None)


def require_role(*roles: UserRole):
    def _require(user: User = Depends(get_current_user)) -> User:
        allowed = {role.value for role in roles}
        if roles and user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _require


def require_founder(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.founder.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Founder access required")
    return user


def require_compliance(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.compliance.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compliance access required")
    return user
