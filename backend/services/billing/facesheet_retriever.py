from __future__ import annotations

"""
When a facesheet (patient demographics from facility) is missing, we support:
- Call: AI-assisted request to the hospital (IVR/AI script; optional outbound call to facility).
- Fax: Inbound fax from facility is parsed (OCR/key:value), patient matched, demographics synced.
  Optional: outbound fax request to facility when we have FacilityContact.fax_number.
"""
import logging
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from core.config import settings
from models.epcr import Patient
from models.epcr_core import EpcrRecord
from models.fax import FacilityContact
from models.user import User
from services.telnyx.telnyx_service import TelnyxFaxHandler, TelnyxIVRService
from utils.time import utc_now


class FacesheetRetriever:
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
        self.ivr_service = TelnyxIVRService(db, org_id)
        self.fax_handler = TelnyxFaxHandler(db, org_id)

    def auto_fetch_facesheet(self, request: Request, user: User, patient: Patient) -> dict[str, Any]:
        if self._facesheet_present(patient):
            return {
                "status": "present",
                "message": "Demographics already available.",
                "patient_id": patient.id,
            }
        response = self.request_facesheet_from_facility(request, user, patient)
        return {"status": "requested", "details": response}

    def request_facesheet_from_facility(self, request: Request, user: User, patient: Patient) -> dict[str, Any]:
        payload = {
            "call_sid": f"facesheet-{patient.id}-{int(utc_now().timestamp())}",
            "from": settings.TELNYX_FROM_NUMBER or "billing@fusonems.local",
            "intent": "facesheet_request",
        }
        ai_response = self.ivr_service.route_to_ai_agent(
            transcript="Request facesheet and fax", intent="facesheet_request"
        )
        summary = self.ivr_service.record_call_summary(
            request=request,
            user=user,
            payload=payload,
            ai_response=ai_response,
            intent="facesheet_request",
            reason="auto_facesheet",
            resolution="awaiting_fax",
        )
        out = {"summary_id": summary.id, "next_step": "awaiting_fax"}
        facility = self._facility_for_facesheet_fax(patient)
        if facility:
            out["outbound_fax_available"] = True
            out["facility_fax"] = facility.fax_number
            out["facility_name"] = facility.facility_name
        return out

    def _facility_for_facesheet_fax(self, patient: Patient) -> FacilityContact | None:
        """Look up FacilityContact for outbound facesheet request (destination from latest record or org records dept)."""
        destination = None
        latest = (
            self.db.query(EpcrRecord)
            .filter(EpcrRecord.patient_id == patient.id, EpcrRecord.org_id == self.org_id)
            .order_by(EpcrRecord.id.desc())
            .first()
        )
        if latest and getattr(latest, "patient_destination", None):
            destination = (latest.patient_destination or "").strip()
        q = (
            self.db.query(FacilityContact)
            .filter(FacilityContact.org_id == self.org_id, FacilityContact.active == True)
            .filter(FacilityContact.fax_number != "", FacilityContact.fax_number.isnot(None))
        )
        if destination:
            fac = q.filter(FacilityContact.facility_name.ilike(f"%{destination}%")).first()
            if fac:
                return fac
        return q.filter(FacilityContact.department.in_(["records", "billing"])).first()

    def parse_facesheet_ocr(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.fax_handler.extract_facesheet(payload)

    def _facesheet_present(self, patient: Patient) -> bool:
        required = ("first_name", "last_name", "date_of_birth", "address", "phone")
        return all(getattr(patient, field, None) for field in required)

    def facesheet_status(self, patient: Patient) -> dict[str, Any]:
        required = ("first_name", "last_name", "date_of_birth", "address", "phone")
        missing = [field for field in required if not getattr(patient, field)]
        return {
            "present": not missing,
            "missing_fields": missing,
            "checked_at": utc_now().isoformat(),
        }

    def send_facesheet_request_fax(self, patient: Patient) -> dict[str, Any]:
        """Send an outbound fax request to the facility (records/billing) asking for facesheet. Requires FACESHEET_REQUEST_FAX_MEDIA_URL and Telnyx."""
        facility = self._facility_for_facesheet_fax(patient)
        if not facility or not (getattr(facility, "fax_number", None) or "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No facility fax number found for this patient. Add a FacilityContact with fax_number for the destination.",
            )
        media_url = (getattr(settings, "FACESHEET_REQUEST_FAX_MEDIA_URL", None) or "").strip()
        if not media_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FACESHEET_REQUEST_FAX_MEDIA_URL is not set. Set it to a public URL of a PDF template (e.g. facesheet request cover page).",
            )
        if not getattr(settings, "TELNYX_API_KEY", None):
            raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="Telnyx API key not configured")
        try:
            import telnyx
        except ImportError:
            raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="Telnyx SDK not installed")
        telnyx.api_key = settings.TELNYX_API_KEY
        connection_id = getattr(settings, "TELNYX_CONNECTION_ID", None) or getattr(settings, "TELNYX_FAX_CONNECTION_ID", None)
        if not connection_id:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="TELNYX_CONNECTION_ID or TELNYX_FAX_CONNECTION_ID not set for outbound fax.",
            )
        to_number = (facility.fax_number or "").strip()
        from_number = (getattr(settings, "TELNYX_FAX_FROM_NUMBER", None) or getattr(settings, "TELNYX_FROM_NUMBER", None) or "").strip()
        if not from_number:
            raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="TELNYX_FAX_FROM_NUMBER or TELNYX_FROM_NUMBER not set")
        try:
            response = telnyx.Fax.create(
                connection_id=connection_id,
                to=to_number,
                from_=from_number,
                media_url=media_url,
            )
            logger.info("Facesheet request fax sent to %s for patient_id=%s", to_number, patient.id)
            return {
                "status": "sent",
                "facility_name": getattr(facility, "facility_name", ""),
                "to": to_number,
                "provider_id": getattr(response, "id", None),
            }
        except Exception as e:
            logger.exception("Facesheet request fax failed for patient_id=%s", patient.id)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fax send failed: {e}") from e
