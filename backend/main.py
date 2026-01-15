from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import Base, engine
from utils.logger import logger
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
from services.billing.billing_router import router as billing_router
from services.business_ops.business_ops_router import router as business_ops_router
from services.cad.cad_router import router as cad_router
from services.cad.tracking_router import router as tracking_router
from services.epcr.epcr_router import router as epcr_router
from services.founder.founder_router import router as founder_router
from services.investor_demo.investor_demo_router import router as investor_demo_router
from services.mail.mail_router import router as mail_router
from services.schedule.schedule_router import router as schedule_router

app = FastAPI(title="FusonEMS Quantum Platform", version="2.0")
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
app.include_router(billing_router)
app.include_router(mail_router)
app.include_router(ai_console_router)
app.include_router(founder_router)
app.include_router(investor_demo_router)
app.include_router(auth_router)
app.include_router(business_ops_router)


@app.on_event("startup")
def startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Startup DB initialization failed: %s", exc)

@app.get("/")
def root():
    return {"status": "online", "system": "FusonEMS Quantum Platform"}
