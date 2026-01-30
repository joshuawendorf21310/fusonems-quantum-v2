from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.epcr import Patient
from models.notifications import InAppNotification, NotificationSeverity, NotificationType
from models.telnyx import TelnyxCallSummary, TelnyxFaxRecord
from models.user import User
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot
from services.billing.assist_service import OllamaClient
from services.telnyx.helpers import billing_users, module_enabled


class TelnyxIVRService:
    # Dial 1 for billing questions, 2 for payment status, 3 for a person
    INTENT_MAP = {
        "1": "billing_questions",
        "2": "payment_status",
        "3": "speak_to_agent",
    }
    IVR_MENU_TEXT = (
        "Thanks for calling. "
        "Press 1 for billing questions. "
        "Press 2 for payment status. "
        "Press 3 to speak with a representative."
    )

    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
        self.ai_client = OllamaClient()

    def get_ivr_menu_text(self) -> str:
        return self.IVR_MENU_TEXT

    def detect_caller_intent(self, payload: dict[str, Any]) -> tuple[str, str]:
        digits = payload.get("digits") or payload.get("dtmf") or ""
        transcript = (payload.get("speech_text") or payload.get("text") or "").lower()
        if digits:
            intent = self.INTENT_MAP.get(str(digits)[0], "general_inquiry")
            reason = f"DTMF:{digits}"
        elif "payment" in transcript:
            intent, reason = "payment_status", "keyword:payment"
        elif "claim" in transcript:
            intent, reason = "claim_inquiry", "keyword:claim"
        elif "payer" in transcript:
            intent, reason = "payer_question", "keyword:payer"
        else:
            intent, reason = "general_inquiry", "keyword:fallback"
        return intent, reason

    def route_to_ai_biller_helper(self, transcript: str, intent: str) -> dict[str, Any]:
        """Ollama as AI biller helper: human-like, short answers for TTS (sounds like a real person)."""
        from core.config import settings
        model = getattr(settings, "OLLAMA_IVR_MODEL", None) or "llama3.2"
        system = (
            "You are a friendly billing specialist on a live phone call. "
            "Sound like a real human: use short sentences, a warm tone, and natural language. "
            "Never say you're an AI, a bot, or an assistant. "
            "Answer billing and payment questions briefly (1 to 3 sentences max) so it works well when read aloud. "
            "If you don't know something, say you'll have someone follow up. "
            "No bullet points, no markdown, no jargon."
        )
        user_part = transcript.strip() if transcript else "The caller just chose an option and may ask a question next."
        prompt = f"{system}\n\nCaller topic: {intent}. Caller said or selected: {user_part}\n\nYour brief, natural reply (one or two sentences):"
        return self.ai_client.generate(prompt, model, temperature=0.4)

    def route_to_ai_agent(self, transcript: str, intent: str) -> dict[str, Any]:
        """Route to AI biller helper (Ollama) for human-like voice responses."""
        result = self.route_to_ai_biller_helper(transcript, intent)
        if result.get("status") == "ok" and result.get("response"):
            text = (result["response"] or "").strip()
            if len(text) > 400:
                text = text[:397] + "..."
            result["response"] = text
        return result

    def record_call_summary(
        self,
        request: Any,
        user: User,
        payload: dict[str, Any],
        ai_response: dict[str, Any],
        intent: str,
        reason: str,
        resolution: str | None = None,
    ) -> TelnyxCallSummary:
        summary = TelnyxCallSummary(
            org_id=self.org_id,
            call_sid=payload.get("call_sid", payload.get("session_id", "")),
            caller_number=payload.get("from", ""),
            intent=intent,
            transcript={"payload": payload},
            ai_model=ai_response.get("model") or "",
            ai_response=ai_response.get("metadata") or ai_response,
            resolution=resolution or "queued",
            metadata={"reason": reason},
        )
        apply_training_mode(summary, request)
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        audit_and_event(
            db=self.db,
            request=request,
            user=user,
            action="create",
            resource="telnyx_call_summary",
            classification=summary.classification,
            after_state=model_snapshot(summary),
            event_type="telnyx.call.summary",
            event_payload={
                "call_id": summary.id,
                "intent": intent,
                "resolution": summary.resolution,
            },
        )
        return summary

    def handle_incoming_call(self, request: Any, user: User, payload: dict[str, Any]) -> dict[str, Any]:
        if not module_enabled(self.db, user.org_id):
            raise RuntimeError("Billing module disabled")
        intent, reason = self.detect_caller_intent(payload)
        transcript = payload.get("speech_text") or payload.get("text") or ""
        ai_response = self.route_to_ai_agent(transcript, intent)
        summary = self.record_call_summary(request, user, payload, ai_response, intent, reason)
        return {
            "intent": intent,
            "ai_response": ai_response,
            "summary_id": summary.id,
            "next_action": "connect_to_agent" if intent != "payment_status" else "share_payment_status",
        }


class TelnyxFaxHandler:
    """
    Inbound fax: Telnyx sends fax.received webhook to /api/telnyx/fax-received.
    We store the fax, match patient from OCR/facesheet, sync patient data, and notify billers.
    Outbound fax: Use comms API (POST /api/comms/send/fax) or mail_router send with channel=fax;
    configure TELNYX_FAX_FROM_NUMBER and TELNYX_CONNECTION_ID (or FAX) for outbound.
    """
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id

    def extract_facesheet(self, payload: dict[str, Any]) -> dict[str, Any]:
        ocr_text = payload.get("ocr_text") or payload.get("body") or ""
        data = {}
        lines = ocr_text.replace("\r", "\n").split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower().replace(" ", "_")] = value.strip()
        return data or {"note": "ocr data unavailable"}

    def match_patient(self, data: dict[str, Any]) -> Patient | None:
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        dob = data.get("date_of_birth") or data.get("dob")
        query = self.db.query(Patient).filter(Patient.org_id == self.org_id)
        if first_name and last_name:
            query = query.filter(Patient.first_name.ilike(f"%{first_name}%"), Patient.last_name.ilike(f"%{last_name}%"))
        if dob:
            query = query.filter(Patient.date_of_birth == dob)
        return query.order_by(Patient.created_at.desc()).first()

    def store_fax(self, request: Any, user: User, payload: dict[str, Any]) -> TelnyxFaxRecord:
        facesheet = self.extract_facesheet(payload)
        matched = self.match_patient(facesheet)
        record = TelnyxFaxRecord(
            org_id=self.org_id,
            fax_sid=payload.get("fax_sid", ""),
            sender_number=payload.get("from_number") or payload.get("from"),
            metadata=payload,
            parsed_facesheet=facesheet,
            matched_patient_id=matched.id if matched else None,
        )
        apply_training_mode(record, request)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        audit_and_event(
            db=self.db,
            request=request,
            user=user,
            action="create",
            resource="telnyx_fax_record",
            classification=record.classification,
            after_state=model_snapshot(record),
            event_type="telnyx.fax.received",
            event_payload={"fax_id": record.id, "matched_patient_id": record.matched_patient_id},
        )
        if matched:
            self._sync_patient(matched, facesheet, user, request)
        self._notify_biller(request, payload, record)
        return record

    def _sync_patient(self, patient: Patient, facesheet: dict[str, Any], user: User, request: Any) -> None:
        before = model_snapshot(patient)
        patient.address = patient.address or facesheet.get("address")
        patient.phone = patient.phone or facesheet.get("phone") or facesheet.get("primary_phone")
        patient.medications = patient.medications or []
        audit_and_event(
            db=self.db,
            request=request,
            user=user,
            action="update",
            resource="epcr_patient",
            classification=patient.classification,
            before_state=before,
            after_state=model_snapshot(patient),
            event_type="telnyx.fax.patient_synced",
            event_payload={"patient_id": patient.id},
        )
        self.db.commit()

    def _notify_biller(self, request: Any, payload: dict[str, Any], record: TelnyxFaxRecord) -> None:
        users = billing_users(self.db, self.org_id)
        metadata = {"fax_id": record.id, "sender": record.sender_number}
        for recipient in users:
            notification = InAppNotification(
                org_id=self.org_id,
                user_id=recipient.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                severity=NotificationSeverity.INFO,
                title="Telnyx fax received",
                body=f"Fax from {record.sender_number} contains a new facesheet.",
                linked_resource_type="telnyx_fax_record",
                linked_resource_id=record.id,
                metadata_payload=metadata,
            )
            apply_training_mode(notification, request)
            self.db.add(notification)
        if users:
            self.db.commit()
