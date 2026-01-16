import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import create_access_token, hash_password, verify_password, get_current_user
from core.config import settings
from core.modules import MODULE_DEPENDENCIES
from models.module_registry import ModuleRegistry
from models.organization import Organization
from models.user import User, UserRole
from utils.retention import seed_retention_policies
from utils.write_ops import audit_and_event, model_snapshot
from utils.rate_limit import check_rate_limit


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterPayload(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.dispatcher
    organization_name: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict | None = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    response: Response = None,
):
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LOCAL_AUTH_DISABLED")
    if request is not None and settings.ENV == "production":
        bucket = f"register:{request.client.host}"
        if not check_rate_limit(bucket, settings.AUTH_RATE_LIMIT_PER_MIN):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
    org = db.query(Organization).filter(Organization.name == payload.organization_name).first()
    org_created = False
    if not org:
        org = Organization(
            name=payload.organization_name,
            encryption_key=secrets.token_hex(32),
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        org_created = True
        for module_key, deps in MODULE_DEPENDENCIES.items():
            db.add(
                ModuleRegistry(
                    org_id=org.id,
                    module_key=module_key,
                    dependencies=deps,
                    enabled=True,
                    kill_switch=False,
                )
            )
        db.commit()
        seed_retention_policies(db, org.id)
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        org_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if request is not None:
        if org_created:
            audit_and_event(
                db=db,
                request=request,
                user=user,
                action="create",
                resource="organization",
                classification="NON_PHI",
                after_state=model_snapshot(org),
                event_type="auth.organization.created",
                event_payload={"organization_id": org.id},
            )
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="user",
            classification="NON_PHI",
            after_state=model_snapshot(user),
            event_type="auth.user.registered",
            event_payload={"user_id": user.id},
        )
    token = create_access_token({"sub": user.id, "org": user.org_id, "role": user.role, "mfa": False})
    if response is not None:
        response.set_cookie(
            settings.SESSION_COOKIE_NAME,
            token,
            httponly=True,
            secure=settings.ENV == "production",
            samesite="lax",
        )
        response.set_cookie(
            settings.CSRF_COOKIE_NAME,
            secrets.token_hex(16),
            httponly=False,
            secure=settings.ENV == "production",
            samesite="lax",
        )
    return TokenResponse(access_token=token, user=model_snapshot(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db), response: Response = None):
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LOCAL_AUTH_DISABLED")
    if settings.ENV == "production":
        bucket = f"login:{payload.email}"
        if not check_rate_limit(bucket, settings.AUTH_RATE_LIMIT_PER_MIN):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.id, "org": user.org_id, "role": user.role, "mfa": False})
    if response is not None:
        response.set_cookie(
            settings.SESSION_COOKIE_NAME,
            token,
            httponly=True,
            secure=settings.ENV == "production",
            samesite="lax",
        )
        response.set_cookie(
            settings.CSRF_COOKIE_NAME,
            secrets.token_hex(16),
            httponly=False,
            secure=settings.ENV == "production",
            samesite="lax",
        )
    return TokenResponse(access_token=token, user=model_snapshot(user))


@router.get("/me")
def me(user: User = Depends(get_current_user), request: Request = None):
    payload = model_snapshot(user)
    payload["mfa_verified"] = bool(getattr(request.state, "mfa_verified", False)) if request else False
    payload["device_trusted"] = bool(getattr(request.state, "device_trusted", True)) if request else True
    payload["on_shift"] = bool(getattr(request.state, "on_shift", True)) if request else True
    return {"user": payload, "config": {"smart_mode": settings.SMART_MODE}}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    return {"status": "ok"}
