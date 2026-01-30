"""
Founder AI Billing Assistant Endpoints

FastAPI endpoints for billing analytics and AI assistance in the founder dashboard.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from services.founder.billing_service import FounderBillingService
from utils.logger import logger


router = APIRouter(prefix="/api/founder/billing", tags=["founder-billing"])

# Pydantic models
class BillingStatsResponse(BaseModel):
    unpaid_claims_value: float
    overdue_claims_value: float
    avg_days_to_payment: float
    billing_accuracy_score: float
    claims_out_for_review: int
    payer_responses_pending: int
    draft_invoices_count: int
    draft_invoices_value: float
    potential_billing_issues: int
    ai_suggestions_available: int


class RecentBillingActivityResponse(BaseModel):
    id: str
    date: str
    type: str
    payer: str
    amount: float
    status: str
    ai_flagged: bool


class AIInsightResponse(BaseModel):
    category: str
    title: str
    description: str
    impact: str
    related_claims: Optional[List[str]] = Field(default_factory=list)
    suggested_action: str
    ai_confidence: float


class AIChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=5000)


class AIChatResponse(BaseModel):
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplainRequest(BaseModel):
    """Ask for a plain-language explanation of a billing term, concept, or screen."""
    topic: str = Field(..., min_length=1, max_length=500, description="e.g. 'denial', 'claim status', 'EOB', 'what to do next'")
    context: Optional[str] = Field(None, max_length=2000, description="Optional: where you are in the app or what you're looking at")


class ExplainResponse(BaseModel):
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Service instance
billing_service = FounderBillingService()


@router.get("/stats", response_model=BillingStatsResponse)
async def get_founder_billing_stats(
    org_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> BillingStatsResponse:
    """
    Get comprehensive billing statistics for the founder dashboard.
    
    Returns:
        - Unpaid and overdue claims values
        - Average days to payment
        - Billing accuracy score
        - Counts of claims in various states
        - AI suggestions available
    """
    try:
        stats_data = await billing_service.get_founder_billing_stats(org_id)
        return BillingStatsResponse(**stats_data)
    except Exception as e:
        logger.error(f"Error in get_founder_billing_stats endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing statistics"
        )


@router.get("/recent-activity", response_model=List[RecentBillingActivityResponse])
async def get_recent_billing_activity(
    limit: int = 10,
    org_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> List[RecentBillingActivityResponse]:
    """
    Get recent billing activity for display in the founder dashboard.
    
    Args:
        limit: Maximum number of activities to return (default: 10)
        org_id: Optional organization ID to filter by
    
    Returns:
        List of recent billing activities with payer info, amounts, and AI flags
    """
    try:
        if limit > 50:
            limit = 50  # Cap at 50 items
            
        activities = await billing_service.get_recent_billing_activity(limit, org_id)
        return [RecentBillingActivityResponse(**activity) for activity in activities]
    except Exception as e:
        logger.error(f"Error in get_recent_billing_activity endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent billing activity"
        )


@router.get("/ai-insights", response_model=List[AIInsightResponse])
async def get_billing_ai_insights(
    org_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> List[AIInsightResponse]:
    """
    Get AI-generated billing insights and suggestions for the founder.
    
    Returns:
        List of AI insights categorized by type (billing_issue, optimization, urgent_action)
        with confidence scores and suggested actions.
    """
    try:
        insights = await billing_service.get_billing_ai_insights(org_id)
        return [AIInsightResponse(**insight) for insight in insights]
    except Exception as e:
        logger.error(f"Error in get_billing_ai_insights endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI billing insights"
        )


@router.post("/ai-chat", response_model=AIChatResponse)
async def generate_billing_ai_chat_response(
    request: AIChatRequest,
    org_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> AIChatResponse:
    """
    Generate AI response to billing-related questions using current billing context.
    
    The AI assistant will consider:
    - Current billing statistics
    - Recent billing activity
    - Pending AI insights
    - NEMSIS compliance requirements
    - Best practices for EMS billing
    
    Args:
        request: Contains the billing question
        org_id: Optional organization ID for context
    
    Returns:
        AI-generated response with billing guidance
    """
    try:
        if len(request.question) < 3 or len(request.question) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question must be between 3 and 5000 characters"
            )
        
        response_text = await billing_service.generate_billing_ai_chat_response(
            request.question, org_id
        )
        
        return AIChatResponse(response=response_text)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_billing_ai_chat_response endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI billing response"
        )


@router.post("/explain", response_model=ExplainResponse)
async def explain_billing_topic(request: ExplainRequest):
    """
    Get a plain-language explanation of a billing term, concept, or "what to do next".
    Designed for someone new to billing — AI explains everything and suggests next steps.
    """
    try:
        explanation = await billing_service.explain_billing_topic(request.topic, request.context)
        return ExplainResponse(explanation=explanation)
    except Exception as e:
        logger.error(f"Error in explain_billing_topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get explanation"
        )


@router.get("/health")
async def get_billing_system_health(db: Session = Depends(get_db)):
    """
    Get billing system health status for the founder dashboard.
    
    Returns combined health information including:
    - Database connectivity
    - Billing service availability
    - AI service status
    - Recent error rates
    """
    try:
        # Test database connectivity
        db.execute("SELECT 1")
        
        # Check if we can get basic stats (indicates service health)
        await billing_service.get_founder_billing_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "service": "available",
            "ai_service": "available",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Billing system health check failed: {e}")
        return {
            "status": "degraded",
            "database": "error",
            "service": "unavailable",
            "ai_service": "unavailable",
            "last_updated": datetime.utcnow().isoformat(),
            "error": str(e)
        }