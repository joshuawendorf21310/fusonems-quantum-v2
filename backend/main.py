from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi import Depends

from core.auth import (
    get_current_user,
    get_current_user_from_request,
    require_compliance,
    require_founder,
    require_role,
)
from core.config import settings, validate_settings_runtime
from core.database import Base, SessionLocal, engine
from models.audit_event import AuditEvent
from models.organization import Organization
from models.session import Session as UserSession
from models.setting import Setting
from models.user import User, UserRole
from services.cad.cad_router import router as cad_router
from services.cad.live_router import router as cad_live_router
from services.cad.tracking_router import router as cad_tracking_router
from services.core.audit_router import router as audit_router
from services.core.auth_router import router as auth_router
from services.core.settings_router import router as settings_router
from utils.logger import logger
from utils.time import compute_drift_seconds, parse_device_time, utc_now

app = FastAPI(title="FusonEMS Quantum Platform", version="2.0")


@app.middleware("http")
async def server_time_middleware(request: Request, call_next):
    server_time = utc_now()
    device_time = parse_device_time(request.headers.get("x-device-time"))
    drift_seconds, drifted = compute_drift_seconds(device_time, server_time)
    request.state.server_time = server_time
    request.state.device_time = device_time
    request.state.drift_seconds = drift_seconds
    request.state.drifted = drifted
    response = await call_next(request)
    response.headers["x-server-time"] = server_time.isoformat()
    response.headers["x-drift-seconds"] = str(drift_seconds)
    response.headers["x-drifted"] = str(drifted).lower()
    return response


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if (
            request.url.path.startswith("/api/auth")
            or request.url.path.startswith("/api/comms/webhooks")
            or request.url.path.startswith("/api/email/inbound/postmark")
        ):
            return await call_next(request)
        session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
        auth_header = request.headers.get("authorization", "")
        if session_cookie and not auth_header:
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            csrf_header = request.headers.get("x-csrf-token")
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse(status_code=403, content={"detail": "CSRF_CHECK_FAILED"})
    return await call_next(request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(settings_router)
app.include_router(cad_router)
app.include_router(cad_tracking_router)
app.include_router(cad_live_router)


@app.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "id": str(current_user.id),
        "orgId": str(current_user.org_id),
        "email": current_user.email,
        "role": current_user.role,
    }


@app.on_event("startup")
def startup() -> None:
    logger.warning("DATABASE_URL host: %s", settings.DATABASE_URL)
    validate_settings_runtime(settings)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Startup DB initialization failed: %s", exc)


@app.middleware("http")
async def rbac_middleware(request: Request, call_next):
    path = request.url.path
    if not (
        path.startswith("/founder")
        or path.startswith("/billing")
        or path.startswith("/clinical")
        or path.startswith("/compliance")
    ):
        return await call_next(request)
    db = SessionLocal()
    try:
        current_user = get_current_user_from_request(request, db)
        if path.startswith("/founder"):
            require_founder(user=current_user)
        if path.startswith("/billing"):
            require_role(UserRole.billing, UserRole.admin, UserRole.founder)(user=current_user)
        if path.startswith("/clinical"):
            require_role(UserRole.crew, UserRole.admin, UserRole.founder)(user=current_user)
        if path.startswith("/compliance"):
            require_compliance(user=current_user)
    finally:
        db.close()
    return await call_next(request)

@app.get("/")
def root():
    return {"status": "online", "system": "FusonEMS Quantum Platform"}
