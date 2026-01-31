import os
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.database import (
    Base,
    FireBase,
    HemsBase,
    TelehealthBase,
    get_engine,
    get_fire_engine,
    get_hems_engine,
    get_telehealth_engine,
)
from core.config import settings, validate_settings_runtime
from core.logger import logger
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
from services.auth.sso_router import router as sso_router
from services.billing.ai_assist_router import router as ai_assist_router
from services.billing.billing_router import router as billing_router
from services.billing.console_router import router as console_router
from services.billing.facesheet_router import router as facesheet_router
from services.billing.office_ally_router import router as office_ally_router
from services.billing.prior_auth_router import router as prior_auth_router
from services.billing.stripe_router import router as stripe_router
from services.business_ops.business_ops_router import router as business_ops_router
from services.cad.cad_router import router as cad_router
from services.cad.incident_router import router as cad_incident_router
from services.cad.tracking_router import router as tracking_router
from services.cad.socket_router import router as socket_bridge_router
from services.compliance.compliance_router import router as compliance_router
from services.compliance.fedramp_router import router as fedramp_router
from services.physical.physical_router import router as physical_router
from services.planning.planning_router import router as planning_router
from services.assessment.assessment_router import router as assessment_router
from services.risk.risk_router import router as risk_router
from services.acquisition.acquisition_router import router as acquisition_router
from services.epcr.epcr_router import router as epcr_router
from services.epcr.master_patient_router import router as master_patient_router
from services.epcr.rule_builder_router import router as epcr_rule_builder_router
from services.epcr.ems_router import router as epcr_ems_router
from services.epcr.fire_epcr_router import router as epcr_fire_router
from services.epcr.hems_router import router as epcr_hems_router
from services.epcr.dashboard_router import router as epcr_dashboard_router
from services.founder.founder_router import router as founder_router
from services.founder.email_endpoints import router as founder_email_router
from services.founder.billing_endpoints import router as founder_billing_router
from services.founder.phone_endpoints import router as founder_phone_router
from services.founder.accounting_endpoints import router as founder_accounting_router
from services.founder.epcr_import_endpoints import router as founder_epcr_import_router
from services.founder.expenses_endpoints import router as founder_expenses_router
from services.founder.marketing_endpoints import router as founder_marketing_router
from services.founder.reporting_endpoints import router as founder_reporting_router
from services.protocols.protocols_router import router as protocols_router
from services.founder.fax_endpoints import router as founder_fax_router
from services.fax.fax_router import router as intelligent_fax_router
from services.agency_portal.agency_router import router as agency_portal_router
from services.agency_portal.reports_router import router as agency_reports_router
from services.investor_demo.investor_demo_router import router as investor_demo_router
from services.mail.mail_router import router as mail_router
from services.email.email_router import router as email_router
from services.telnyx.telnyx_router import router as telnyx_router
from services.telnyx.ivr_router import router as telnyx_ivr_router
from services.lob_webhook import router as lob_router
from services.fire.fire_router import router as fire_router
from services.fire.fire_911_transport_router import router as fire_911_transport_router
from services.fire.fire_scheduling_router import router as fire_scheduling_router
from services.fire.fire_rms_router import router as fire_rms_router
from services.telehealth.telehealth_router import router as telehealth_router
from services.telehealth.jitsi_router import router as jitsi_video_router
from services.schedule.schedule_router import router as schedule_router
from services.scheduling.scheduling_router import router as scheduling_module_router
from services.scheduling.predictive_router import router as predictive_scheduling_router
from services.system.system_router import router as system_router
from services.automation.automation_router import router as automation_router
from services.validation.validation_router import router as validation_router
from services.events.event_router import router as event_router
from services.time.time_router import router as time_router
from services.weather.weather_router import router as weather_router
from services.workflows.workflow_router import router as workflow_router
from services.legal.legal_router import router as legal_router
from services.ai_registry.ai_registry_router import router as ai_registry_router
from services.consent.consent_router import router as consent_router
from services.training.training_router import router as training_router
from services.personnel.personnel_router import router as personnel_security_router
from services.training.awareness.awareness_router import router as awareness_training_router
from services.hems.hems_router import router as hems_router
from services.hems.hems_aviation_router import router as hems_aviation_router
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
from services.communications.sms_webhook import router as sms_webhook_router
from services.notifications.notification_router import router as notifications_router
from services.epcr.ocr_router import router as ocr_router
from services.ai_chat import router as ai_chat_router
# from services.training.training_center_router import router as training_center_router  # Temporarily disabled
from services.narcotics.narcotics_router import router as narcotics_router
from services.medication.medication_router import router as medication_router
from services.inventory.inventory_router import router as inventory_router
from services.fleet.fleet_router import router as fleet_router
from services.founder_ops.founder_ops_router import router as founder_ops_router
from services.legal_portal.legal_portal_router import router as legal_portal_router
from services.patient_portal.patient_portal_router import router as patient_portal_router
from services.patient_portal.patient_billing_router import router as patient_billing_router
from services.carefusion.patient_router import router as carefusion_patient_router
from services.carefusion.provider_router import router as carefusion_provider_router
from services.marketing.routes import router as marketing_router, contact_router
from services.storage.storage_router import router as storage_router
from services.founder_documents_router import router as founder_documents_router
from services.metriport.metriport_router import router as metriport_router
from services.metriport.metriport_webhooks import router as metriport_webhooks_router
from services.routing.routes import router as routing_router
from services.recommendations.routes import router as recommendations_router
from services.intelligence.routes import router as intelligence_router
from services.phases.routes import router as phases_router
from services.complete_platform_routes import router as complete_platform_router
from services.founder_billing.routes import router as founder_billing_ai_router
from services.founder_billing.wisconsin_routes import router as wisconsin_billing_router
from services.founder_billing.collections_governance_routes import router as collections_governance_router
from services.agency_portal.reports_router import router as agency_reports_router
from services.agency_portal.agency_messaging_router import router as agency_messaging_router
from services.billing.patient_balance_router import router as patient_balance_router
from services.billing.payment_plan_router import router as payment_plan_router
from services.billing.denial_alert_router import router as denial_alert_router
from services.founder.briefing_router import router as briefing_router
from services.founder.terminology_router import router as founder_terminology_router
from services.founder.import_export_router import router as founder_import_export_router
from services.media.media_router import router as media_router
from services.maintenance.maintenance_router import router as maintenance_router

from services.transportlink import transport_ai_router
from services.crewlink.crewlink_router import router as crewlink_router
from services.events.event_handlers import register_event_handlers
from services.cad.socket_bridge import initialize_socket_bridge, shutdown_socket_bridge
from services.cad.bridge_handlers import register_bridge_event_handlers
from services.screen_share import router as screen_share_router

app = FastAPI(title="FusonEMS Quantum Platform", version="2.0")
app.include_router(ai_chat_router)
app.include_router(screen_share_router)


def _should_bootstrap_schema() -> bool:
    db_url = (settings.DATABASE_URL or "").lower()
    return settings.ENV.lower() == "test" or db_url.startswith("sqlite")


def _running_under_pytest() -> bool:
    return os.environ.get("PYTEST_CURRENT_TEST") is not None


def _ensure_database_schema() -> None:
    import models  # noqa: F401 - register all SQLAlchemy models

    logger.info("Ensuring database schema for %s", settings.DATABASE_URL)
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("Base schema created")
    except Exception as exc:
        logger.warning("Startup DB initialization failed: %s", exc)
    try:
        TelehealthBase.metadata.create_all(bind=get_telehealth_engine())
        logger.info("Telehealth schema created")
    except Exception as exc:
        logger.warning("Telehealth DB initialization failed: %s", exc)
    try:
        FireBase.metadata.create_all(bind=get_fire_engine())
        logger.info("Fire schema created")
    except Exception as exc:
        logger.warning("Fire DB initialization failed: %s", exc)
    try:
        hems_engine = get_hems_engine()
        if not settings.DATABASE_URL.startswith("sqlite"):
            with hems_engine.begin() as connection:
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS hems"))
        HemsBase.metadata.create_all(bind=hems_engine)
        logger.info("HEMS schema created")
    except Exception as exc:
        logger.warning("HEMS DB initialization failed: %s", exc)

@app.middleware("http")
async def server_time_middleware(request: Request, call_next):
    if settings.ENV.lower() == "test":
        return await call_next(request)
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
    if settings.ENV.lower() == "test":
        return await call_next(request)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if (
            request.url.path.startswith("/api/auth")
            or request.url.path.startswith("/api/sso")
            or request.url.path.startswith("/api/comms/webhooks")
            or request.url.path.startswith("/api/email/inbound/postmark")
            or request.url.path.startswith("/api/metriport/webhooks")
            or request.url.path.startswith("/api/founder/fax/webhook")
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
    # Restrict to only the HTTP methods we actually use
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    # Restrict to only the headers we need
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Device-ID",
        "X-Client-Time",
    ],
    # Expose headers that the frontend needs to read
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)
app.include_router(socket_bridge_router)
app.include_router(cad_router)
app.include_router(cad_incident_router)
app.include_router(tracking_router)
app.include_router(epcr_router)
app.include_router(master_patient_router)
app.include_router(epcr_rule_builder_router)
app.include_router(epcr_ems_router)
app.include_router(epcr_fire_router)
app.include_router(epcr_hems_router)
app.include_router(epcr_dashboard_router)
app.include_router(schedule_router)
app.include_router(scheduling_module_router)
app.include_router(predictive_scheduling_router)
app.include_router(system_router)
app.include_router(billing_router)
app.include_router(console_router)
app.include_router(office_ally_router)
app.include_router(facesheet_router)
app.include_router(ai_assist_router)
app.include_router(prior_auth_router)
app.include_router(stripe_router)
app.include_router(mail_router)
app.include_router(email_router)
app.include_router(telnyx_router)
app.include_router(telnyx_ivr_router)
app.include_router(lob_router)
app.include_router(telehealth_router)
app.include_router(jitsi_video_router)
app.include_router(automation_router)
app.include_router(validation_router)
app.include_router(compliance_router)
app.include_router(fedramp_router)
app.include_router(physical_router)
app.include_router(planning_router)
app.include_router(assessment_router)
app.include_router(risk_router)
app.include_router(acquisition_router)
app.include_router(system_integrity_router)
app.include_router(fire_router)
app.include_router(fire_911_transport_router)
app.include_router(fire_scheduling_router)
app.include_router(fire_rms_router)
app.include_router(event_router)
app.include_router(time_router)
app.include_router(weather_router)
app.include_router(workflow_router)
app.include_router(legal_router)
app.include_router(ai_registry_router)
app.include_router(consent_router)
app.include_router(training_router)
app.include_router(personnel_security_router)
app.include_router(awareness_training_router)
app.include_router(hems_router)
app.include_router(hems_aviation_router)
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
app.include_router(sms_webhook_router)
# app.include_router(training_center_router)  # Temporarily disabled
app.include_router(narcotics_router)
app.include_router(medication_router)
app.include_router(inventory_router)
app.include_router(fleet_router)
app.include_router(founder_ops_router)
app.include_router(legal_portal_router)
app.include_router(patient_portal_router)
app.include_router(patient_billing_router)
app.include_router(carefusion_patient_router)
app.include_router(carefusion_provider_router)
app.include_router(notifications_router)
app.include_router(marketing_router)
app.include_router(contact_router)
app.include_router(ocr_router)
app.include_router(ai_console_router)
app.include_router(founder_email_router)
app.include_router(founder_billing_router)
app.include_router(founder_phone_router)
app.include_router(founder_accounting_router)
app.include_router(founder_epcr_import_router)
app.include_router(founder_expenses_router)
app.include_router(founder_marketing_router)
app.include_router(founder_reporting_router)
app.include_router(founder_fax_router)
app.include_router(intelligent_fax_router)
app.include_router(founder_router)
app.include_router(founder_terminology_router)
app.include_router(founder_import_export_router)
# Note: cron_router integration is temporarily disabled until cron endpoints are implemented
app.include_router(investor_demo_router)
app.include_router(oidc_router)
app.include_router(device_router)
app.include_router(sso_router)
app.include_router(auth_router)
app.include_router(business_ops_router)
app.include_router(transport_ai_router)
app.include_router(crewlink_router)
app.include_router(storage_router)
app.include_router(founder_documents_router)
app.include_router(metriport_router)
app.include_router(metriport_webhooks_router)
app.include_router(routing_router)
app.include_router(recommendations_router)
app.include_router(intelligence_router)
app.include_router(phases_router)
app.include_router(complete_platform_router)
app.include_router(founder_billing_ai_router)
app.include_router(wisconsin_billing_router)
app.include_router(collections_governance_router)
app.include_router(agency_portal_router)
app.include_router(agency_reports_router)
app.include_router(agency_messaging_router)
app.include_router(patient_balance_router)
app.include_router(payment_plan_router)
app.include_router(denial_alert_router)
app.include_router(briefing_router)



@app.on_event("startup")
async def startup() -> None:
    try:
        register_event_handlers()
    except Exception as e:
        logger.warning("Failed to register event handlers: %s", e)
    
    # Initialize Socket.io bridge to CAD backend
    try:
        await initialize_socket_bridge()
        from services.cad.socket_bridge import get_socket_bridge
        bridge = get_socket_bridge()
        register_bridge_event_handlers(bridge)
        
        # Ensure connection is established
        if not bridge.connected:
            logger.warning("Socket bridge initialized but not connected - will retry in background")
        else:
            logger.info("✓ Socket.io bridge initialized and connected to CAD backend")
            
        # Start background reconnection task if not connected
        if not bridge.connected:
            async def reconnect_task():
                import asyncio
                for attempt in range(5):
                    await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                    try:
                        await bridge.connect()
                        if bridge.connected:
                            logger.info("✓ Socket bridge reconnected successfully")
                            break
                    except Exception as e:
                        logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
            
            asyncio.create_task(reconnect_task())
            
    except Exception as e:
        logger.error("Failed to initialize socket bridge: %s", e)
        logger.warning("Application will continue without real-time CAD integration - services will work independently")
    
    if settings.ENV.lower() == "test":
        if _running_under_pytest():
            logger.info("Skipping startup DB initialization while pytest is running")
        else:
            logger.info("Test environment detected, skipping startup DB initialization by default")
        return
    try:
        db_host = urlparse(settings.DATABASE_URL).hostname or "unknown"
    except Exception:
        db_host = "unknown"
    logger.warning("DATABASE_URL host: %s", db_host)
    validate_settings_runtime()
    if _should_bootstrap_schema() and not _running_under_pytest():
        _ensure_database_schema()

@app.on_event("shutdown")
async def shutdown() -> None:
    """Cleanup on application shutdown"""
    try:
        await shutdown_socket_bridge()
        logger.info("✓ Socket bridge shutdown complete")
    except Exception as e:
        logger.error("Error during socket bridge shutdown: %s", e)

@app.get("/")
def root():
    return {"status": "online", "system": "FusonEMS Quantum Platform"}


@app.get("/healthz")
def healthz():
    logger.info("healthz handler invoked")
    return {"status": "online"}


@app.get("/health")
def health():
    """Load balancer / monitoring health check (alias for healthz)."""
    return {"status": "ok"}


@app.get("/api/health/telnyx")
def health_telnyx():
    """Probe Telnyx API (no auth). Returns configured status and balance if API key is set."""
    configured = bool(settings.TELNYX_API_KEY and settings.TELNYX_FROM_NUMBER)
    out = {
        "configured": configured,
        "telnyx_number": settings.TELNYX_FROM_NUMBER or None,
        "status": "missing_credentials" if not configured else None,
        "probe": "telnyx_balance",
    }
    if not configured:
        return out
    try:
        import telnyx
        client = telnyx.Telnyx(api_key=settings.TELNYX_API_KEY)
        resp = client.balance.retrieve()
        data = getattr(resp, "data", resp)
        out["status"] = "ok"
        out["balance"] = getattr(data, "available_credit", getattr(data, "balance", None))
        out["record_type"] = getattr(data, "record_type", None)
    except ImportError as exc:
        out["status"] = "error"
        out["error"] = "telnyx package not installed"
        logger.warning("Telnyx health check: %s", exc)
    except Exception as exc:
        out["status"] = "error"
        out["error"] = str(exc)
        logger.warning("Telnyx API probe failed: %s", exc)
    return out
