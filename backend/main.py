from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from sqlalchemy import text

from core.database import Base, FireBase, HemsBase, TelehealthBase, engine, fire_engine, hems_engine, telehealth_engine
from utils.logger import logger
from utils.time import compute_drift_seconds, parse_device_time, utc_now
from models import (
    AiInsight,
    BillingRecord,
    BusinessOpsTask,
    Call,
    Dispatch,
    FounderMetric,
    InvestorMetric,
    Message,
    Patient,
    Shift,
    Unit,
    User,
)
from services.ai_console.ai_console_router import router as ai_console_router
from services.auth.auth_router import router as auth_router
from services.auth.oidc_router import router as oidc_router
from services.auth.device_router import router as device_router
from services.billing.billing_router import router as billing_router
from services.billing.stripe_router import router as stripe_router
from services.business_ops.business_ops_router import router as business_ops_router
from services.cad.cad_router import router as cad_router
from services.cad.tracking_router import router as tracking_router
from services.compliance.compliance_router import router as compliance_router
from services.epcr.epcr_router import router as epcr_router
from services.founder.founder_router import router as founder_router
from services.investor_demo.investor_demo_router import router as investor_demo_router
from services.mail.mail_router import router as mail_router
from services.email.email_router import router as email_router
from services.lob_webhook import router as lob_router
from services.fire.fire_router import router as fire_router
from services.telehealth.telehealth_router import router as telehealth_router
from services.schedule.schedule_router import router as schedule_router
from services.system.system_router import router as system_router
from services.automation.automation_router import router as automation_router
from services.validation.validation_router import router as validation_router
from services.events.event_router import router as event_router
from services.time.time_router import router as time_router
from services.workflows.workflow_router import router as workflow_router
from services.legal.legal_router import router as legal_router
from services.ai_registry.ai_registry_router import router as ai_registry_router
from services.consent.consent_router import router as consent_router
from services.training.training_router import router as training_router
from services.hems.hems_router import router as hems_router
from services.repair.repair_router import router as repair_router
from services.export.export_router import router as export_router
from services.documents.document_router import router as document_router
from services.documents.quantum_documents_router import router as quantum_documents_router
from services.builders.builder_router import router as builder_router
from services.search.search_router import router as search_router
from services.jobs.jobs_router import router as jobs_router
from services.analytics.analytics_router import router as analytics_router
from services.feature_flags.feature_flags_router import router as feature_flags_router
from services.qa.qa_router import router as qa_router
from services.communications.comms_router import router as comms_router, webhook_router as comms_webhook_router
from services.training.training_center_router import router as training_center_router
from services.narcotics.narcotics_router import router as narcotics_router
from services.medication.medication_router import router as medication_router
from services.inventory.inventory_router import router as inventory_router
from services.fleet.fleet_router import router as fleet_router
from services.founder_ops.founder_ops_router import router as founder_ops_router
from services.legal_portal.legal_portal_router import router as legal_portal_router
from services.patient_portal.patient_portal_router import router as patient_portal_router
from services.events.event_handlers import register_event_handlers

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
app.include_router(cad_router)
app.include_router(tracking_router)
app.include_router(epcr_router)
app.include_router(schedule_router)
app.include_router(system_router)
app.include_router(billing_router)
app.include_router(stripe_router)
app.include_router(mail_router)
app.include_router(email_router)
app.include_router(lob_router)
app.include_router(telehealth_router)
app.include_router(automation_router)
app.include_router(validation_router)
app.include_router(compliance_router)
app.include_router(fire_router)
app.include_router(event_router)
app.include_router(time_router)
app.include_router(workflow_router)
app.include_router(legal_router)
app.include_router(ai_registry_router)
app.include_router(consent_router)
app.include_router(training_router)
app.include_router(hems_router)
app.include_router(repair_router)
app.include_router(export_router)
app.include_router(document_router)
app.include_router(quantum_documents_router)
app.include_router(builder_router)
app.include_router(search_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(feature_flags_router)
app.include_router(qa_router)
app.include_router(comms_router)
app.include_router(comms_webhook_router)
app.include_router(training_center_router)
app.include_router(narcotics_router)
app.include_router(medication_router)
app.include_router(inventory_router)
app.include_router(fleet_router)
app.include_router(founder_ops_router)
app.include_router(legal_portal_router)
app.include_router(patient_portal_router)
app.include_router(ai_console_router)
app.include_router(founder_router)
app.include_router(investor_demo_router)
app.include_router(oidc_router)
app.include_router(device_router)
app.include_router(auth_router)
app.include_router(business_ops_router)


@app.on_event("startup")
def startup() -> None:
    register_event_handlers()
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Startup DB initialization failed: %s", exc)
    try:
        TelehealthBase.metadata.create_all(bind=telehealth_engine)
    except Exception as exc:
        logger.warning("Telehealth DB initialization failed: %s", exc)
    try:
        FireBase.metadata.create_all(bind=fire_engine)
    except Exception as exc:
        logger.warning("Fire DB initialization failed: %s", exc)
    try:
        if not settings.DATABASE_URL.startswith("sqlite"):
            with hems_engine.begin() as connection:
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS hems"))
        HemsBase.metadata.create_all(bind=hems_engine)
    except Exception as exc:
        logger.warning("HEMS DB initialization failed: %s", exc)

@app.get("/")
def root():
    return {"status": "online", "system": "FusonEMS Quantum Platform"}
