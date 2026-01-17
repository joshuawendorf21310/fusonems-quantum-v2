import base64
import hashlib
import secrets
import uuid
from datetime import timedelta
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import create_access_token, get_current_user
from models.organization import Organization
from models.user import User
from services.auth.session_service import create_session, revoke_session
from utils.write_ops import audit_and_event, model_snapshot
from utils.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth/oidc", tags=["OIDC"])

_oidc_cache: dict[str, Any] = {}


def _get_oidc_config() -> dict:
    if _oidc_cache.get("config"):
        return _oidc_cache["config"]
    if not settings.OIDC_ISSUER_URL:
        raise HTTPException(status_code=400, detail="OIDC issuer not configured")
    resp = requests.get(f"{settings.OIDC_ISSUER_URL.rstrip('/')}/.well-known/openid-configuration", timeout=10)
    resp.raise_for_status()
    _oidc_cache["config"] = resp.json()
    return _oidc_cache["config"]


def _get_jwks() -> dict:
    if _oidc_cache.get("jwks"):
        return _oidc_cache["jwks"]
    config = _get_oidc_config()
    resp = requests.get(config["jwks_uri"], timeout=10)
    resp.raise_for_status()
    _oidc_cache["jwks"] = resp.json()
    return _oidc_cache["jwks"]


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _build_pkce() -> tuple[str, str]:
    verifier = _base64url(secrets.token_bytes(64))
    challenge = _base64url(hashlib.sha256(verifier.encode("utf-8")).digest())
    return verifier, challenge


def _frontend_redirect(path: str) -> str:
    base = settings.ALLOWED_ORIGINS.split(",")[0].strip().rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


@router.get("/login")
def oidc_login(request: Request):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OIDC_DISABLED")
    if settings.ENV == "production":
        bucket = f"oidc:{request.client.host}"
        if not check_rate_limit(bucket, settings.AUTH_RATE_LIMIT_PER_MIN):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
    config = _get_oidc_config()
    verifier, challenge = _build_pkce()
    nonce = secrets.token_hex(16)
    state = jwt.encode(
        {"nonce": nonce, "verifier": verifier, "redirect": request.query_params.get("redirect", "/dashboard")},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    params = {
        "response_type": "code",
        "client_id": settings.OIDC_CLIENT_ID,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "scope": settings.OIDC_SCOPES,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    response = RedirectResponse(url=requests.Request("GET", config["authorization_endpoint"], params=params).prepare().url)
    response.set_cookie(
        "oidc_state",
        state,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
    )
    return response


@router.get("/callback")
def oidc_callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OIDC_DISABLED")
    cookie_state = request.cookies.get("oidc_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OIDC_STATE_MISMATCH")
    try:
        state_payload = jwt.decode(state, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OIDC_STATE_INVALID") from exc
    verifier = state_payload.get("verifier")
    nonce = state_payload.get("nonce")
    redirect_path = state_payload.get("redirect", "/dashboard")
    config = _get_oidc_config()
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "client_id": settings.OIDC_CLIENT_ID,
        "code_verifier": verifier,
    }
    if settings.OIDC_CLIENT_SECRET:
        token_payload["client_secret"] = settings.OIDC_CLIENT_SECRET
    token_resp = requests.post(config["token_endpoint"], data=token_payload, timeout=10)
    token_resp.raise_for_status()
    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OIDC_ID_TOKEN_MISSING")
    jwks = _get_jwks()
    try:
        claims = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256", "ES256", "PS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER_URL,
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC_TOKEN_INVALID") from exc
    if claims.get("nonce") != nonce:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC_NONCE_MISMATCH")
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OIDC_EMAIL_REQUIRED")
    full_name = claims.get("name") or email.split("@")[0]
    oidc_sub = claims.get("sub")
    mfa_verified = "mfa" in (claims.get("amr") or []) or claims.get("acr") in {"urn:mace:incommon:iap:silver"}

    user = db.query(User).filter(User.email == email).first()
    if not user:
        org = (
            db.query(Organization)
            .filter(Organization.name == email.split("@")[-1])
            .first()
        )
        if not org:
            org = Organization(name=email.split("@")[-1], encryption_key=secrets.token_hex(32))
            db.add(org)
            db.commit()
            db.refresh(org)
        user = User(
            email=email,
            full_name=full_name,
            hashed_password="",
            role="dispatcher",
            org_id=org.id,
            auth_provider="oidc",
            oidc_sub=oidc_sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.auth_provider = "oidc"
        user.oidc_sub = oidc_sub
        db.commit()

    # Create JWT with session claims
    jti = str(uuid.uuid4())
    token, expires_at = create_access_token(
        {"sub": user.id, "org": user.org_id, "role": user.role, "mfa": mfa_verified, "jti": jti},
        expires_delta=timedelta(hours=1),
    )
    
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
    
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="login",
        resource="oidc_session",
        classification="NON_PHI",
        after_state={"session_id": session.id, "jti": jti, "user": model_snapshot(user)},
        event_type="auth.oidc.login",
        event_payload={"auth_provider": "oidc", "session_id": session.id},
    )
    redirect_response = RedirectResponse(_frontend_redirect(redirect_path))
    redirect_response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
    )
    redirect_response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        session.csrf_secret,
        httponly=False,
        secure=settings.ENV == "production",
        samesite="lax",
    )
    redirect_response.delete_cookie("oidc_state")
    return redirect_response


@router.post("/logout")
def oidc_logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OIDC_DISABLED")
    
    # Extract JWT from request to get jti
    token = request.cookies.get(settings.SESSION_COOKIE_NAME) if request else None
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            jti = payload.get("jti")
            if jti:
                # Revoke the session
                revoke_session(db=db, jwt_jti=jti, reason="oidc_logout")
                
                # Log session revocation
                if request is not None:
                    audit_and_event(
                        db=db,
                        request=request,
                        user=user,
                        action="revoke",
                        resource="oidc_session",
                        classification="NON_PHI",
                        after_state={"jti": jti, "reason": "oidc_logout"},
                        event_type="auth.oidc.session.revoked",
                        event_payload={"jti": jti, "user_id": user.id, "reason": "oidc_logout"},
                    )
        except Exception:
            # If we can't decode the token, still clear cookies
            pass
    
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    config = _get_oidc_config()
    end_session = config.get("end_session_endpoint")
    return {"status": "ok", "logout_url": end_session or settings.OIDC_POST_LOGOUT_REDIRECT_URI}
