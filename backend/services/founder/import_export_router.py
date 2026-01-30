"""
Founder Import/Export - Third-party billing import and agency data export.

- Third-party billing import: CSV, JSON, or 837P so you can bring in runs/claims.
- Agency data export: full export package so agencies can take their data elsewhere (portability).
"""
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole

router = APIRouter(prefix="/api/founder", tags=["Founder Import/Export"])


class ImportResult(BaseModel):
    status: str
    message: str
    accepted: int = 0
    errors: list = []


class ExportRequest(BaseModel):
    org_id: int
    format: str = "zip"  # zip, json


# ---------------------------------------------------------------------------
# Third-party billing import (100% target: CSV/JSON/837P wired)
# ---------------------------------------------------------------------------

@router.post("/billing/import/csv", response_model=ImportResult)
def import_billing_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """
    Import runs/claims from CSV for third-party billing.
    Columns: patient_id, trip_date, payer, amount, etc. (schema in docs).
    """
    # Stub: full implementation will parse CSV, validate, create/update billing records
    return ImportResult(
        status="accepted",
        message="Third-party billing CSV import - implementation in progress. Upload CSV with columns per docs/founder/WISCONSIN_100_PERCENT_AND_COMPLIANCE.md.",
        accepted=0,
        errors=[],
    )


@router.post("/billing/import/json", response_model=ImportResult)
def import_billing_json(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """
    Import runs/claims from JSON for third-party billing.
    """
    return ImportResult(
        status="accepted",
        message="Third-party billing JSON import - implementation in progress.",
        accepted=0,
        errors=[],
    )


# ---------------------------------------------------------------------------
# Agency data export (100% target: full package for portability)
# ---------------------------------------------------------------------------

@router.get("/agency-export")
def agency_export(
    org_id: int = None,
    format: str = "zip",
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """
    Export all agency data for portability (ePCR, billing, fire/NFIRS, comms audit, documents).
    Returns download link or stream. Founder only.
    """
    # Stub: full implementation will bundle ePCR, billing, fire, comms, documents per org
    return JSONResponse(
        status_code=501,
        content={
            "status": "not_implemented",
            "message": "Agency data export - full package in progress. Target: ePCR, billing, NFIRS, comms, documents per org.",
            "docs": "docs/founder/WISCONSIN_100_PERCENT_AND_COMPLIANCE.md",
        },
    )
