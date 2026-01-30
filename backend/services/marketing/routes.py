from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timezone
import re
from sqlalchemy.orm import Session
from core.database import get_db
from core.logger import logger
from core.config import settings

router = APIRouter(prefix="/api/v1", tags=["marketing"])

# Simple in-memory storage for contact submissions
_contact_submissions: list[dict] = []


class DemoRequest(BaseModel):
    name: str
    email: EmailStr
    organization: str
    phone: str
    role: str
    challenges: Optional[str] = None
    timestamp: Optional[str] = None
    status: str = "pending"
    source: str = "website"


class BillingLookup(BaseModel):
    account_number: str
    zip_code: str


@router.post("/demo-requests")
async def create_demo_request(
    request: DemoRequest,
    db: Session = Depends(get_db)
):
    """
    Receive and store demo request from website.
    """
    try:
        logger.info(f"Demo request received: {request.organization} - {request.email}")
        
        demo_data = {
            "name": request.name,
            "email": request.email,
            "organization": request.organization,
            "phone": request.phone,
            "role": request.role,
            "challenges": request.challenges,
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            "status": request.status,
            "source": request.source,
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"Demo request stored: {demo_data}")
        
        return {
            "success": True,
            "message": "Demo request received",
            "request_id": f"DR-{int(datetime.utcnow().timestamp())}"
        }
        
    except Exception as e:
        logger.error(f"Error processing demo request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/billing/lookup")
async def lookup_billing_account(
    request: BillingLookup,
    db: Session = Depends(get_db)
):
    """
    Lookup billing account by account number and ZIP code.
    """
    try:
        logger.info(f"Billing lookup: {request.account_number}")
        
        # Placeholder for actual database lookup
        # In production, query the billing database
        account = None
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return {
            "account_number": request.account_number,
            "balance": 0.00,
            "patient_name": "Demo Patient",
            "service_date": "2024-01-15",
            "status": "open"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error looking up billing account: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health/marketing")
async def marketing_health_check():
    """
    Health check endpoint for marketing APIs.
    """
    return {
        "status": "healthy",
        "service": "marketing-api",
        "timestamp": datetime.utcnow().isoformat()
    }


class ContactSubmission(BaseModel):
    name: str
    email: str
    organization: Optional[str] = None
    subject: Optional[str] = None
    message: str
    timestamp: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = str(v or '').strip()[:100]
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = str(v or '').strip().lower()[:254]
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            raise ValueError('Invalid email address')
        return v
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = str(v or '').strip()[:5000]
        if len(v) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v


# Also register as /api/contact for frontend compatibility
@router.post("/contact")
async def submit_contact_v1(
    submission: ContactSubmission,
    request: Request,
):
    """
    Handle public contact form submissions.
    """
    return await _process_contact_submission(submission, request)


# Primary contact endpoint at /api/contact
contact_router = APIRouter(prefix="/api/contact", tags=["Contact"])

@contact_router.post("")
async def submit_contact(
    submission: ContactSubmission,
    request: Request,
):
    """
    Handle public contact form submissions.
    """
    return await _process_contact_submission(submission, request)


async def _process_contact_submission(submission: ContactSubmission, request: Request):
    """Process contact form submission."""
    
    # Rate limiting check (simple IP-based)
    client_ip = request.client.host if request.client else "unknown"
    recent_from_ip = sum(
        1 for s in _contact_submissions[-100:]
        if s.get("client_ip") == client_ip
    )
    if recent_from_ip >= 5:
        raise HTTPException(
            status_code=429,
            detail="Too many submissions. Please try again later."
        )
    
    # Create submission record
    submission_record = {
        "id": len(_contact_submissions) + 1,
        "name": submission.name,
        "email": submission.email,
        "organization": submission.organization,
        "subject": submission.subject,
        "message": submission.message,
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent", "")[:500],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    _contact_submissions.append(submission_record)
    
    # Log submission
    logger.info(
        f"[CONTACT FORM] New submission from {submission.name} <{submission.email}> "
        f"(org: {submission.organization or 'N/A'})"
    )
    
    return {
        "ok": True,
        "message": "Thank you for your message. We'll get back to you soon.",
        "reference_id": submission_record["id"],
    }
