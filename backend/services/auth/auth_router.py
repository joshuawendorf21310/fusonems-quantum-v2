import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import create_access_token, hash_password, verify_password, get_current_user, require_roles
from core.config import settings
from core.logger import logger
from core.modules import MODULE_DEPENDENCIES
from models.module_registry import ModuleRegistry
from models.organization import Organization
from models.user import User, UserRole
from services.auth.session_service import create_session, revoke_session, revoke_all_sessions_for_user
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


class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict | None = None


def _maybe_emit_register_audit(
    db: Session,
    request: Request,
    user: User,
    org: Organization,
    org_created: bool,
) -> None:
    if not settings.ENABLE_AUTH_REGISTER_AUDIT_LOGGING or request is None:
        return
    try:
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
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.error("REGISTER_AUDIT_FAILED: %s", exc)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    response: Response = None,
):
    logger.info("REGISTER_START")
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LOCAL_AUTH_DISABLED")
    if request is not None and settings.ENV == "production":
        bucket = f"register:{request.client.host if request.client else 'unknown'}"
        if not check_rate_limit(bucket, settings.AUTH_RATE_LIMIT_PER_MIN):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
    result: TokenResponse | None = None
    try:
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
            db.flush()
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
            db.refresh(org)
            seed_retention_policies(db, org.id)
        logger.info("REGISTER_HASH_START")
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=payload.role.value,
            org_id=org.id,
        )
        db.add(user)
        db.flush()
        logger.info("REGISTER_DB_COMMIT_START")
        db.commit()
        db.refresh(user)
        _maybe_emit_register_audit(db, request, user, org, org_created)
        token = create_access_token(
            {"sub": user.id, "org": user.org_id, "role": user.role, "mfa": False}
        )
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
        result = TokenResponse(access_token=token, user=model_snapshot(user))
    except Exception:
        db.rollback()
        raise
    finally:
        logger.info("REGISTER_END")
    if result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")
    return result


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginPayload,
    db: Session = Depends(get_db),
    request: Request = None,
    response: Response = None,
):
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LOCAL_AUTH_DISABLED")
    if settings.ENV == "production":
        bucket = f"login:{payload.email}"
        if not check_rate_limit(bucket, settings.AUTH_RATE_LIMIT_PER_MIN):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Create JWT with session claims
    jti = str(uuid.uuid4())
    token, expires_at = create_access_token({
        "sub": user.id,
        "org": user.org_id,
        "role": user.role,
        "mfa": False,
        "jti": jti,
    })
    
    # Create session record
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    session = create_session(
        db=db,
        org_id=user.org_id,
        user_id=user.id,
        jwt_jti=jti,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Log session creation
    if request is not None:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="login",
            resource="auth_session",
            classification="NON_PHI",
            after_state={"session_id": session.id, "jti": jti},
            event_type="auth.session.created",
            event_payload={"session_id": session.id, "user_id": user.id},
        )
    
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
            session.csrf_secret,
            httponly=False,
            secure=settings.ENV == "production",
            samesite="lax",
        )
    return TokenResponse(access_token=token, user=model_snapshot(user))


@router.post("/change-password")
def change_password(
    payload: ChangePasswordPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Change password and clear must_change_password. Required when must_change_password is true."""
    current_hash = getattr(user, "hashed_password", None) or getattr(user, "password_hash", None)
    if not current_hash or not verify_password(payload.current_password, current_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    user.hashed_password = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return {"status": "ok", "message": "Password changed. You can continue."}


@router.get("/me")
def me(user: User = Depends(get_current_user), request: Request = None):
    payload = model_snapshot(user)
    payload["mfa_verified"] = bool(getattr(request.state, "mfa_verified", False)) if request else False
    payload["device_trusted"] = bool(getattr(request.state, "device_trusted", True)) if request else True
    payload["on_shift"] = bool(getattr(request.state, "on_shift", True)) if request else True
    return {"user": payload, "config": {"smart_mode": settings.SMART_MODE}}


@router.post("/logout")
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Extract JWT from request to get jti
    token = request.cookies.get(settings.SESSION_COOKIE_NAME) if request else None
    if token:
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            jti = payload.get("jti")
            if jti:
                # Revoke the session
                revoke_session(db=db, jwt_jti=jti, reason="logout")
                
                # Log session revocation
                if request is not None:
                    audit_and_event(
                        db=db,
                        request=request,
                        user=user,
                        action="revoke",
                        resource="auth_session",
                        classification="NON_PHI",
                        after_state={"jti": jti, "reason": "logout"},
                        event_type="auth.session.revoked",
                        event_payload={"jti": jti, "user_id": user.id, "reason": "logout"},
                    )
        except Exception:
            # If we can't decode the token, still clear cookies
            pass
    
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    return {"status": "ok"}


@router.post("/dev_seed", response_model=TokenResponse)
def dev_seed(response: Response = None, db: Session = Depends(get_db)):
    """Development helper: create a demo org + user and return a session.

    This endpoint is intentionally available only when ENV != 'production'.
    It helps local developers quickly get a valid session for manual testing.
    """
    if settings.ENV == "production":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="NOT_ALLOWED_IN_PRODUCTION")
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LOCAL_AUTH_DISABLED")
    demo_email = "dev@local"
    demo_password = "Pass1234"
    demo_org_name = "Dev Organization"
    user = db.query(User).filter(User.email == demo_email).first()
    if user:
        # Ensure existing dev user has founder role and must change password on next login
        changed = False
        if user.role != UserRole.founder.value:
            user.role = UserRole.founder.value
            changed = True
        if not getattr(user, "must_change_password", True):
            user.must_change_password = True
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
    else:
        org = db.query(Organization).filter(Organization.name == demo_org_name).first()
        org_created = False
        if not org:
            org = Organization(name=demo_org_name, encryption_key=secrets.token_hex(32))
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
            email=demo_email,
            full_name="Developer",
            hashed_password=hash_password(demo_password),
            role=UserRole.founder.value,
            org_id=org.id,
            must_change_password=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token, _ = create_access_token({"sub": user.id, "org": user.org_id, "role": user.role, "mfa": False})
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
