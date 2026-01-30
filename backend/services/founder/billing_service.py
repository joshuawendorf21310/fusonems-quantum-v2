"""
Founder AI Billing Assistant Service

Provides centralized billing intelligence and AI assistance for single-biller workflows.
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from clients.ollama_client import OllamaClient
from core.database import get_db
from models import (
    BillingRecord,
    BillingPayment,
    BillingClaim,
    BillingInvoice,
    BillingAiInsight,
)
from utils.logger import logger


class FounderBillingService:
    """Service for founder-level billing analytics and AI assistance."""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.db = next(get_db())
        
    async def get_founder_billing_stats(self, org_id: Optional[int] = None) -> Dict:
        """Get comprehensive billing statistics for founder dashboard."""
        try:
            query_filters = []
            if org_id:
                query_filters.append(BillingRecord.org_id == org_id)
            
            # Unpaid claims value
            unpaid_claims_query = self.db.query(
                func.coalesce(func.sum(BillingRecord.amount), 0)
            ).join(Claim).filter(
                and_(
                    Claim.status.in_([ClaimStatus.NEW, ClaimStatus.SUBMITTED, ClaimStatus.PENDING]),
                    *query_filters
                )
            )
            unpaid_claims_value = float(unpaid_claims_query.first()[0] or 0)
            
            # Overdue claims value (over 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            overdue_claims_query = self.db.query(
                func.coalesce(func.sum(BillingRecord.amount), 0)
            ).join(Claim).filter(
                and_(
                    Claim.created_at < thirty_days_ago,
                    Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.PENDING]),
                    *query_filters
                )
            )
            overdue_claims_value = float(overdue_claims_query.first()[0] or 0)
            
            # Average days to payment
            days_to_payment_query = self.db.query(
                func.avg(
                    func.extract('days', Payment.created_at - BillingRecord.created_at)
                )
            ).join(Payment, Payment.claim_id == BillingRecord.claim_id).filter(
                and_(
                    Payment.status == "completed",
                    *query_filters
                )
            )
            avg_days_to_payment = float(days_to_payment_query.first()[0] or 45)
            
            # Billing accuracy score (based on claim acceptance rate)
            claims_last_30_days = self.db.query(Claim).filter(
                and_(
                    Claim.created_at >= datetime.utcnow() - timedelta(days=30),
                    *query_filters
                )
            )
            total_claims = claims_last_30_days.count()
            
            accepted_claims = claims_last_30_days.filter(
                Claim.status == ClaimStatus.PAID
            ).count()
            
            billing_accuracy_score = (accepted_claims / max(total_claims, 1)) * 100
            
            # Claims out for review
            claims_out_review = self.db.query(Claim).filter(
                and_(
                    Claim.status.in_([ClaimStatus.UNDER_REVIEW, ClaimStatus.PENDED]),
                    *query_filters
                )
            ).count()
            
            # Payer responses pending (>7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            payer_pending = self.db.query(Claim).filter(
                and_(
                    or_(Claim.status == ClaimStatus.PENDING, Claim.status == ClaimStatus.SUBMITTED),
                    Claim.updated_at < seven_days_ago,
                    *query_filters
                )
            ).count()
            
            # Draft invoices
            draft_invoices_query = self.db.query(
                func.count(Invoice.id),
                func.coalesce(func.sum(Invoice.amount), 0)
            ).filter(
                and_(
                    Invoice.status == InvoiceStatus.DRAFT,
                    *query_filters
                )
            ).first()
            
            draft_invoices_count = draft_invoices_query[0] or 0
            draft_invoices_value = float(draft_invoices_query[1] or 0)
            
            # Potential billing issues (based on AI insights)
            potential_issues = self.db.query(BillingAiInsight).filter(
                and_(
                    BillingAiInsight.resolved == False,
                    BillingAiInsight.severity.in_(["high", "critical"]),
                    *query_filters
                )
            ).count()
            
            # AI suggestions available
            ai_suggestions_available = self.db.query(BillingAiInsight).filter(
                and_(
                    BillingAiInsight.resolved == False,
                    BillingAiInsight.insight_type == "suggestion",
                    *query_filters
                )
            ).count()
            
            return {
                "unpaid_claims_value": unpaid_claims_value,
                "overdue_claims_value": overdue_claims_value,
                "avg_days_to_payment": round(avg_days_to_payment, 1),
                "billing_accuracy_score": round(billing_accuracy_score, 1),
                "claims_out_for_review": claims_out_for_review,
                "payer_responses_pending": payer_pending,
                "draft_invoices_count": draft_invoices_count,
                "draft_invoices_value": draft_invoices_value,
                "potential_billing_issues": potential_issues,
                "ai_suggestions_available": ai_suggestions_available
            }
            
        except Exception as e:
            logger.error(f"Error getting founder billing stats: {e}")
            # Return fallback data
            return {
                "unpaid_claims_value": 0,
                "overdue_claims_value": 0,
                "avg_days_to_payment": 45,
                "billing_accuracy_score": 85,
                "claims_out_for_review": 0,
                "payer_responses_pending": 0,
                "draft_invoices_count": 0,
                "draft_invoices_value": 0,
                "potential_billing_issues": 0,
                "ai_suggestions_available": 0
            }
    
    async def get_recent_billing_activity(self, limit: int = 10, org_id: Optional[int] = None) -> List[Dict]:
        """Get recent billing activity for display."""
        try:
            query_filters = []
            if org_id:
                query_filters.append(BillingRecord.org_id == org_id)
            
            recent_billing = self.db.query(
                BillingRecord,
                Patient,
                InsurancePayer.name.label("payer_name"),
                Claim.status.label("claim_status"),
                Claim.created_at.label("claim_date")
            ).join(
                Patient, Patient.id == BillingRecord.patient_id
            ).join(
                Claim, Claim.id == BillingRecord.claim_id
            ).join(
                InsurancePayer, InsurancePayer.id == Claim.insurance_payer_id
            ).filter(
                and_(*query_filters)
            ).order_by(
                BillingRecord.created_at.desc()
            ).limit(limit).all()
            
            activities = []
            for billing_record, patient, payer_name, claim_status, claim_date in recent_billing:
                # Check if there are any AI insights for this billing record
                ai_insights = self.db.query(BillingAiInsight).filter(
                    and_(
                        BillingAiInsight.billing_record_id == billing_record.id,
                        BillingAiInsight.resolved == False
                    )
                ).count() > 0
                
                activity_type = self._get_activity_type(claim_status)
                
                activities.append({
                    "id": str(billing_record.id),
                    "date": claim_date.isoformat() if claim_date else datetime.utcnow().isoformat(),
                    "type": activity_type,
                    "payer": payer_name or "Unknown Payer",
                    "amount": float(billing_record.amount),
                    "status": claim_status.value if hasattr(claim_status, 'value') else str(claim_status),
                    "ai_flagged": ai_insights
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent billing activity: {e}")
            return []
    
    def _get_activity_type(self, claim_status) -> str:
        """Determine activity type based on claim status."""
        status_map = {
            "new": "New Claim",
            "submitted": "Claim Submitted",
            "pending": "Claim Pending",
            "under_review": "Claim Under Review",
            "denied": "Claim Denied",
            "paid": "Payment Received",
            "partial": "Partial Payment",
            "appealed": "Claim Appealed"
        }
        return status_map.get(str(claim_status).lower(), "Billing Activity")
    
    async def get_billing_ai_insights(self, org_id: Optional[int] = None) -> List[Dict]:
        """Get AI-generated billing insights and suggestions."""
        try:
            query_filters = [BillingAiInsight.resolved == False]
            if org_id:
                query_filters.append(BillingAiInsight.org_id == org_id)
            
            insights = self.db.query(BillingAiInsight).filter(
                and_(*query_filters)
            ).order_by(
                BillingAiInsight.severity.desc(),
                BillingAiInsight.created_at.desc()
            ).limit(5).all()
            
            results = []
            for insight in insights:
                # Categorize the insight
                category = self._categorize_insight(insight.insight_type, insight.severity)
                
                # Get related claim IDs if applicable
                related_claims = []
                if insight.claim_id:
                    related_claims.append(str(insight.claim_id))
                
                results.append({
                    "category": category,
                    "title": insight.title,
                    "description": insight.description,
                    "impact": insight.severity,
                    "related_claims": related_claims,
                    "suggested_action": insight.recommended_action,
                    "ai_confidence": insight.confidence_score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting billing AI insights: {e}")
            return []
    
    def _categorize_insight(self, insight_type: str, severity: str) -> str:
        """Categorize insight for frontend display."""
        if severity == "critical":
            return "urgent_action"
        elif insight_type in ["denial", "rejection", "error"]:
            return "billing_issue"
        else:
            return "optimization"
    
    async def generate_billing_ai_chat_response(self, question: str, org_id: Optional[int] = None) -> str:
        """Generate AI response to billing-related questions."""
        try:
            # Get current billing context
            stats = await self.get_founder_billing_stats(org_id)
            recent_activity = await self.get_recent_billing_activity(5, org_id)
            insights = await self.get_billing_ai_insights(org_id)
            
            # Build context for the AI
            context = {
                "billing_stats": stats,
                "recent_activity": recent_activity,
                "ai_insights": insights,
                "current_date": datetime.utcnow().isoformat()
            }
            
            # Solo biller, new to billing: AI does as much as possible and explains everything in plain language
            system_prompt = """You are a friendly billing coach for a solo biller who is new to medical billing.
            Your job is to:
            1. Do as much of the thinking and next-step planning as possible so they can focus on following your guidance.
            2. Explain everything in plain language. Define any jargon (e.g. denial, EOB, 837P, NEMSIS) the first time you use it.
            3. Give clear "what to do next" steps when relevant. Keep answers practical and actionable.
            4. Be encouraging and concise. Use short paragraphs. If something is optional or advanced, say so.
            5. Base advice on the billing context provided. When you suggest an action, say where to click or what to do in the system when possible."""
            
            user_prompt = f"""Current billing context: {json.dumps(context, default=str, indent=2)}
            
            Question: {question}
            
            Answer in plain language, explain any terms, and say what to do next if relevant."""
            
            response = await self.ollama_client.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="llama3.2"
            )
            
            return response or "I'm sorry, I couldn't process your billing question. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating billing AI chat response: {e}")
            return "I'm experiencing an issue. Please try asking your billing question again."

    async def explain_billing_topic(self, topic: str, context: Optional[str] = None) -> str:
        """Explain a billing term or concept in plain language for someone new to billing."""
        try:
            system_prompt = """You are a billing coach for someone brand new to medical/EMS billing.
            Explain the topic in plain language. Define any jargon. Use 1–3 short paragraphs.
            If the topic is a screen or workflow (e.g. 'denials page', 'what to do next'), say what each part means and what they should do step by step.
            Be encouraging and practical. No fluff."""
            user_prompt = f"Explain this for someone new to billing: {topic}"
            if context:
                user_prompt += f"\n\nThey are currently: {context}"
            user_prompt += "\n\nGive a clear, short explanation."
            response = await self.ollama_client.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="llama3.2",
            )
            return response or f"I don't have an explanation for '{topic}' right now. Try asking in the billing chat."
        except Exception as e:
            logger.error(f"Error in explain_billing_topic: {e}")
            return "Explanation unavailable. Try the billing AI chat with your question."