from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.guards import require_founders
from core.security import get_current_user
from core.database import get_db
from services.founder.email_service import FounderEmailService
from models.user import User  
from models.organization import Organization
from utils.logger import logger

router = APIRouter(prefix="/api/founder/email", tags=["founder_email"])


# ========= REQUEST/RESPONSE MODELS =========

class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body_text: str
    body_html: Optional[str] = ""
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    reply_to: Optional[EmailStr] = None
    urgent: Optional[bool] = False

class SendEmailResponse(BaseModel):
    success: bool
    message_id: int
    postmark_id: str
    thread_id: int

class EmailDraftRequest(BaseModel):
    writer_email: EmailStr
    recipient_email: EmailStr
    subject_context: str
    context: str
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"

class EmailDraftResponse(BaseModel):
    success: bool
    subject: str
    body_text: str
    confidence: float

class EmailSuggestionRequest(BaseModel):
    recipient_email: EmailStr
    subject_line: str
    context: str
    tone: Optional[str] = "professional"

class CommunicationScoreRequest(BaseModel):
    recipient_email: EmailStr


@router.get("/stats")
def get_founder_email_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get email statistics for founder dashboard - HIGH PRIORITY"""
    try:
        service = FounderEmailService(db, user.org_id)
        stats = service.get_founder_email_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email stats: {str(e)}")

@router.get("/recent")
def get_recent_emails(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get recent emails for founder dashboard"""
    try:
        service = FounderEmailService(db, user.org_id)
        emails = service.get_recent_emails(limit=limit)
        
        return {
            "success": True,
            "emails": emails,
            "count": len(emails)
        }
    except Exception as e:
        logger.error(f"Error getting recent emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent emails: {str(e)}")

@router.get("/needs-response")
def get_emails_needing_response(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get emails needing founder response - VERY IMPORTANT"""
    try:
        service = FounderEmailService(db, user.org_id)
        emails = service.get_inbound_emails_needing_response(limit=limit)
        
        if len(emails) > 0:
            # Audit log when we show emails needing response
            audit_and_event(
                db=db,
                request=request,
                user=user,
                action="read",
                resource="founder_email_needs_response",
                classification="OPS",
                after_state={"count": len(emails)},
                event_type="founder.email.needs_response.viewed",
                event_payload={"count": len(emails)}
            )
        
        return {
            "success": True,
            "emails": emails,
            "count": len(emails),
            "has_urgent": any(e.get('urgency') == 'high' for e in emails)
        }
    except Exception as e:
        logger.error(f"Error getting emails needing response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get emails needing response: {str(e)}")

@router.post("/send")
def send_email_as_founders(
    payload: SendEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Send email as founder - CRITICAL functionality"""
    try:
        service = FounderEmailService(db, user.org_id)
        
        result = service.send_email(
            sender=user,
            to_email=str(payload.to),
            subject=payload.subject,
            body_text=payload.body_text,
            body_html=payload.body_html,
            cc_emails=[str(email) for email in payload.cc] if payload.cc else None,
            bcc_emails=[str(email) for email in payload.bcc] if payload.bcc else None,
            reply_to=str(payload.reply_to) if payload.reply_to else None,
            urgent=payload.urgent,
            request=request
        )
        
        return SendEmailResponse(
            success=True,
            message_id=result['message_id'],
            postmark_id=result['postmark_id'],
            thread_id=result['thread_id']
        )
        
    except RuntimeError as e:
        if "Email not configured" in str(e):
            raise HTTPException(status_code=422, detail="Email not configured for this organization")
        raise e
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/draft")
def generate_email_draft(
    payload: EmailDraftRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """AI generate email draft for founder - AI Billing Assistant"""
    try:
        service = FounderEmailService(db, user.org_id)
        
        draft = service.generate_email_draft(
            sender=user,
            recipient_email=str(payload.recipient_email),
            subject_context=payload.subject_context,
            context=payload.context,
            tone=payload.tone,
            length=payload.length,
            request=request
        )
        
        return EmailDraftResponse(
            success=True,
            subject=draft['subject'],
            body_text=draft['body_text'],
            confidence=draft['confidence']
        )
        
    except Exception as e:
        logger.error(f"Error generating email draft: {e}")
        return EmailDraftResponse(
            success=False,
            subject="Error generating draft",
            body_text="AI generation failed. Please draft manually.",
            confidence=0.0
        )

@router.post("/suggest-improvements")
def suggest_email_improvements(
    payload: EmailSuggestionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """AI suggest email improvements"""
    try:
        service = FounderEmailService(db, user.org_id)
        suggestions = service.suggest_email_content(
            recipient_email=str(payload.recipient_email),
            subject_line=payload.subject_line,
            context=payload.context,
            tone=payload.tone
        )
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error suggesting improvements: {e}")
        return {
            "success": False,
            "suggestions": []
        }

@router.get("/tracking-score/{recipient_email}")
def get_communication_score(
    recipient_email: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get communication effectiveness tracking for recipient"""
    try:
        service = FounderEmailService(db, user.org_id)
        score = service.track_communication_outreach(recipient_email)
        
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="read",
            resource="founder_communication_tracking",
            classification="OPS",
            after_state={"recipient": recipient_email, "score": score.get('score', 0)},
            event_type="founder.communication.tracking.viewed",
            event_payload={"recipient": recipient_email}
        )
        
        return {
            "success": True,
            "recipient": recipient_email,
            "score": score
        }
        
    except Exception as e:
        logger.error(f"Error getting communication score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get communication score: {str(e)}")

# MONITORING ENDPOINTS

@router.get("/failed-deliveries")
def get_failed_deliveries(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get failed email deliveries for founder dashboard"""
    try:
        service = FounderEmailService(db, user.org_id)
        failed = service.get_failed_deliveries(limit=limit)
        
        return {
            "success": True,
            "failed_deliveries": failed,
            "count": len(failed)
        }
    except Exception as e:
        logger.error(f"Error getting failed deliveries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get failed deliveries: {str(e)}")

# INBOUND EMAIL WEBHOOK HANDLER (optional when using Postmark)

@router.post("/webhook/inbound", include_in_schema=False)
def postmark_inbound_webhook(
    payload: Dict[str, Any],
    request: Request,
    db: Session = Depends(get_db)
):
    """Postmark inbound webhook. When using SMTP/IMAP only, use POST /api/email/poll-inbound instead."""
    from core.config import settings
    if not settings.POSTMARK_SERVER_TOKEN:
        raise HTTPException(
            status_code=501,
            detail="Postmark not configured. Inbound mail: use SMTP/IMAP and POST /api/email/poll-inbound.",
        )
    try:
        from services.email.email_ingest_service import verify_postmark_signature
        raw_body = b""  # Would need request.body() in async; signature check uses headers
        verify_postmark_signature(raw_body, request)
        
        # Extract org from to address
        to_address = payload.get('ToFull', [{}])[0].get('Email', '')
        org = extract_org_from_email(to_address)
        
        if not org:
            logger.error(f"No org found for email: {to_address}")
            return JSONResponse(content={"error": "Unknown organization"}, status_code=400)
        
        # Process inbound email
        service = FounderEmailService(db, org.id)
        result = service.process_inbound_postmark(payload, sender_org=org)
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        logger.exception("Full webhook error:")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    except Exception as e:
        logger.error(f"Bulk import processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import processing failed: {str(e)}")


# FILE IMPORT ENDPOINTS (ImageTrend/ZOLL)

@router.post("/import/epcr")
def import_epcr_from_vendor(
    request: Request,
    source: str = Query(..., description="Source vendor: imagetrend or zoll"),
    payload: dict = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Import ePCR data from external vendors (ImageTrend/ZOLL)"""
    try:
        from services.epcr.imports.import_service import EPCRImportService
        
        if source not in ['imagetrend', 'zoll']:
            raise HTTPException(status_code=400, detail="Invalid source. Must be 'imagetrend' or 'zoll'")
        
        if not payload or 'xml_content' not in payload:
            raise HTTPException(status_code=400, detail="XML content required in payload")
        
        service = EPCRImportService(db, user.org_id)
        result = service.import_from_vendor(
            source=source,
            xml_content=payload['xml_content'],
            user_id=user.id,
            request=request
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ePCR import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/import/history")
def get_epcr_import_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get ePCR import history for founder dashboard"""
    try:
        from services.epcr.imports.import_service import EPCRImportService
        service = EPCRImportService(db, user.org_id)
        history = service.get_import_history(limit=limit)
        
        return {
            "success": True,
            "history": [
                {
                    "id": import_job.id,
                    "source": import_job.source,
                    "status": import_job.status,
                    "created_at": import_job.created_at.isoformat(),
                    "successful_records": import_job.successful_records,
                    "failed_records": import_job.failed_records,
                    "total_records": import_job.total_records
                }
                for import_job in history
            ],
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting import history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get import history: {str(e)}")


@router.get("/import/stats")
def get_epcr_import_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_founders)
):
    """Get ePCR import statistics for founder dashboard"""
    try:
        from services.epcr.imports.import_service import EPCRImportService
        service = EPCRImportService(db, user.org_id)
        stats = service.get_import_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting import stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get import stats: {str(e)}")
