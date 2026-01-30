from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from jinja2 import Template
from models.wisconsin_billing import (
    PatientStatementTemplate, WisconsinBillingConfig, BillingHealthSnapshot,
    StatementDeliveryLog, TaxExemptionRecord, CollectionsEscalationRecord,
    AIBillingActionLog, TemplateType, BillingHealthStatus, DeliveryFormat
)
from models.founder_billing import PatientStatement, StatementLifecycleState
import lob

from core.config import settings
from services.email.email_transport_service import send_smtp_email_simple

logger = logging.getLogger(__name__)


class WisconsinBillingService:
    """
    Wisconsin Sole Biller Mode - AI-managed billing with full autonomy.
    
    Authoritative Rules:
    - Wisconsin is the jurisdiction
    - Medical transport is tax-exempt by default
    - Collections follow time-based rules (0/15/30/60/90 days)
    - Templates are pre-approved and versioned
    - All actions are auditable and reversible
    - Founder has ultimate authority
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config = db.query(WisconsinBillingConfig).filter_by(enabled=True, state="WI").first()
        if not self.config:
            self.config = self._create_default_config()
        
        self.lob_client = None
    
    def _create_default_config(self) -> WisconsinBillingConfig:
        """Create default Wisconsin configuration."""
        config = WisconsinBillingConfig(
            state="WI",
            enabled=True,
            medical_transport_tax_rate=0.0,
            tax_exempt_by_default=True,
            company_name="FusionEMS",
            footer_disclaimer="Medical transport services are tax-exempt in Wisconsin."
        )
        self.db.add(config)
        self.db.flush()
        return config
    
    def calculate_tax(
        self,
        service_type: str,
        revenue_amount: float,
        charge_id: int
    ) -> Dict:
        """
        Calculate tax for Wisconsin billing.
        Default: Medical transport is tax-exempt.
        """
        exempt = True
        exemption_reason = "Medical transport is sales-tax exempt in Wisconsin"
        tax_rate = 0.0
        tax_amount = 0.0
        
        # Check if service type is taxable
        if service_type == "membership" and self.config.taxable_memberships:
            exempt = False
            exemption_reason = "Membership is taxable per configuration"
            tax_rate = 0.05  # Example rate
        elif service_type == "subscription" and self.config.taxable_subscriptions:
            exempt = False
            exemption_reason = "Subscription is taxable per configuration"
            tax_rate = 0.05
        elif service_type == "event_standby" and self.config.taxable_event_standby:
            exempt = False
            exemption_reason = "Event standby is taxable per configuration"
            tax_rate = 0.05
        elif service_type == "non_medical" and self.config.taxable_non_medical:
            exempt = False
            exemption_reason = "Non-medical service is taxable per configuration"
            tax_rate = 0.05
        
        if not exempt:
            tax_amount = revenue_amount * tax_rate
        
        # Record exemption
        record = TaxExemptionRecord(
            charge_id=charge_id,
            state="WI",
            service_type=service_type,
            exempt=exempt,
            exemption_reason=exemption_reason,
            revenue_amount=revenue_amount,
            tax_rate_applied=tax_rate,
            tax_amount=tax_amount,
            rule_reference="Wisconsin medical transport tax exemption"
        )
        self.db.add(record)
        
        self._log_action(
            action_type="tax_calculated",
            description=f"Calculated tax for {service_type}: ${revenue_amount:.2f}. "
                       f"Exempt: {exempt}. Tax: ${tax_amount:.2f}",
            metadata={
                "service_type": service_type,
                "exempt": exempt,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount
            }
        )
        
        return {
            "exempt": exempt,
            "exemption_reason": exemption_reason,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_with_tax": revenue_amount + tax_amount
        }
    
    def get_template(self, template_type: TemplateType) -> Optional[PatientStatementTemplate]:
        """Get active approved template for given type."""
        return self.db.query(PatientStatementTemplate).filter(
            PatientStatementTemplate.template_type == template_type,
            PatientStatementTemplate.active == True,
            PatientStatementTemplate.approved == True,
            PatientStatementTemplate.state == "WI"
        ).order_by(PatientStatementTemplate.version.desc()).first()
    
    def render_template(
        self,
        template: PatientStatementTemplate,
        statement: PatientStatement,
        format: DeliveryFormat
    ) -> Dict:
        """Render template with patient and billing data."""
        patient = statement.patient
        
        merge_data = {
            "PatientName": f"{patient.first_name} {patient.last_name}",
            "ServiceDate": statement.statement_date.strftime("%B %d, %Y"),
            "BalanceDue": f"${statement.balance_due:.2f}",
            "DueDate": statement.due_date.strftime("%B %d, %Y"),
            "CompanyName": self.config.company_name,
            "CompanyPhone": self.config.company_phone or "",
            "CompanyEmail": self.config.company_email or "",
            "StatementNumber": statement.statement_number,
            "TotalCharges": f"${statement.total_charges:.2f}",
            "InsurancePaid": f"${statement.insurance_paid:.2f}",
            "Adjustments": f"${statement.adjustments:.2f}",
            "PaymentAmount": "",
            "RemainingBalance": f"${statement.balance_due:.2f}"
        }
        
        subject_template = Template(template.subject_line)
        body_template = Template(template.body_content)
        
        subject = subject_template.render(**merge_data)
        body = body_template.render(**merge_data)
        
        # Add branding for print format
        if format == DeliveryFormat.LOB_PHYSICAL or format == DeliveryFormat.PRINT_PDF:
            body = self._add_print_branding(body)
        
        return {
            "subject": subject,
            "body": body,
            "merge_data": merge_data
        }
    
    def _add_print_branding(self, body: str) -> str:
        """Add print-safe branding to document."""
        header = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1>{self.config.company_name}</h1>
            <p>{self.config.company_phone} | {self.config.company_email}</p>
        </div>
        """
        
        footer = f"""
        <div style="margin-top: 40px; font-size: 0.9em; color: #666;">
            <p>{self.config.footer_disclaimer or ''}</p>
        </div>
        """
        
        return f"<html><body>{header}<div>{body}</div>{footer}</body></html>"
    
    def send_statement(
        self,
        statement: PatientStatement,
        template_type: TemplateType,
        force_channel: Optional[str] = None
    ) -> StatementDeliveryLog:
        """
        Send statement using Wisconsin rules.
        AI selects channel: Email → Physical Mail → SMS notification.
        """
        template = self.get_template(template_type)
        if not template:
            raise ValueError(f"No approved template found for {template_type}")
        
        patient = statement.patient
        
        # AI channel selection
        if force_channel:
            channel = DeliveryFormat(force_channel)
            reason = "Forced by caller"
        elif patient.email and template.supports_email:
            channel = DeliveryFormat.EMAIL
            reason = "Email available and preferred"
        elif patient.address and template.supports_lob_print:
            channel = DeliveryFormat.LOB_PHYSICAL
            reason = "Physical mail available (email unavailable)"
        else:
            channel = DeliveryFormat.EMAIL
            reason = "Fallback to email"
        
        # Render template
        rendered = self.render_template(template, statement, channel)
        
        # Create delivery log
        log = StatementDeliveryLog(
            statement_id=statement.id,
            delivery_format=channel,
            template_id=template.id,
            template_version=template.version,
            subject_line=rendered["subject"],
            rendered_content=rendered["body"],
            ai_selected=True,
            selection_rationale=reason
        )
        
        # Execute delivery
        success = False
        if channel == DeliveryFormat.EMAIL:
            success = self._send_via_email(log, patient.email, rendered)
        elif channel == DeliveryFormat.LOB_PHYSICAL:
            success = self._send_via_lob(log, patient, rendered)
        
        log.success = success
        if success:
            log.delivered_at = datetime.utcnow()
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
        
        self.db.add(log)
        
        self._log_action(
            action_type="statement_sent",
            description=f"Sent statement #{statement.statement_number} via {channel.value}. "
                       f"Template: {template.template_name} v{template.version}. Success: {success}",
            statement_id=statement.id,
            policy_reference="Wisconsin communication channel logic",
            outcome="success" if success else "failed",
            metadata={
                "channel": channel.value,
                "template_type": template_type.value,
                "reason": reason
            }
        )
        
        return log
    
    def _send_via_email(self, log: StatementDeliveryLog, email: str, rendered: Dict) -> bool:
        """Send via SMTP (Mailu/self-hosted)."""
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            log.failure_reason = "SMTP settings not configured"
            return False

        try:
            from_addr = getattr(self.config, "company_email", None) or settings.BILLING_FROM_EMAIL or settings.SMTP_USERNAME
            send_smtp_email_simple(
                to=email,
                subject=rendered["subject"],
                html_body=rendered["body"],
                from_addr=from_addr,
            )
            log.recipient_email = email
            log.postmark_message_id = None
            return True
        except Exception as e:
            log.failure_reason = str(e)
            return False
    
    def _send_via_lob(self, log: StatementDeliveryLog, patient, rendered: Dict) -> bool:
        """Send via Lob physical mail."""
        if not self.lob_client:
            log.failure_reason = "Lob client not configured"
            log.corrective_action = "Email will be attempted as fallback"
            return False
        
        try:
            letter = self.lob_client.Letter.create(
                description=f"Patient Statement - Wisconsin",
                to_address={
                    "name": f"{patient.first_name} {patient.last_name}",
                    "address_line1": patient.address_line1,
                    "address_line2": patient.address_line2 or "",
                    "address_city": patient.city,
                    "address_state": patient.state or "WI",
                    "address_zip": patient.zip_code
                },
                from_address={
                    "name": self.config.company_name,
                    "address_line1": "123 Medical Plaza",
                    "address_city": "Madison",
                    "address_state": "WI",
                    "address_zip": "53703"
                },
                file=rendered["body"],
                color=True,
                double_sided=True,
                mail_type="usps_first_class"
            )
            
            log.lob_mail_id = letter.id
            log.lob_tracking_number = letter.tracking_number if hasattr(letter, 'tracking_number') else None
            log.lob_proof_url = letter.url
            log.recipient_address = letter.to_address
            
            return True
        
        except Exception as e:
            log.failure_reason = str(e)
            log.corrective_action = "Will retry or escalate"
            return False
    
    def process_collections_escalations(self):
        """
        Process Wisconsin collections escalations.
        Time-based rules: 0/15/30/60/90 days.
        """
        overdue_statements = self.db.query(PatientStatement).filter(
            PatientStatement.balance_due > 0,
            PatientStatement.due_date < datetime.utcnow(),
            PatientStatement.lifecycle_state != StatementLifecycleState.PAID
        ).all()
        
        for statement in overdue_statements:
            days_overdue = (datetime.utcnow() - statement.due_date).days
            
            # Check if small balance should stop
            if (self.config.stop_small_balances_early and 
                statement.balance_due < self.config.small_balance_threshold and 
                days_overdue > 30):
                continue
            
            # Determine escalation stage
            escalation_day = None
            stage = None
            template_type = None
            
            if days_overdue >= 90:
                escalation_day = 90
                stage = self.config.escalation_day_90
                template_type = TemplateType.FINAL_NOTICE
            elif days_overdue >= 60:
                escalation_day = 60
                stage = self.config.escalation_day_60
                template_type = TemplateType.FINAL_NOTICE
            elif days_overdue >= 30:
                escalation_day = 30
                stage = self.config.escalation_day_30
                template_type = TemplateType.SECOND_NOTICE
            elif days_overdue >= 15:
                escalation_day = 15
                stage = self.config.escalation_day_15
                template_type = TemplateType.FRIENDLY_REMINDER
            
            if escalation_day:
                # Check if already escalated at this level
                existing = self.db.query(CollectionsEscalationRecord).filter(
                    CollectionsEscalationRecord.statement_id == statement.id,
                    CollectionsEscalationRecord.escalation_day == escalation_day,
                    CollectionsEscalationRecord.resolved == False
                ).first()
                
                if not existing:
                    self._create_escalation(statement, escalation_day, stage, template_type, days_overdue)
    
    def _create_escalation(
        self,
        statement: PatientStatement,
        escalation_day: int,
        stage: str,
        template_type: TemplateType,
        days_overdue: int
    ):
        """Create escalation record and send communication."""
        template = self.get_template(template_type)
        
        record = CollectionsEscalationRecord(
            statement_id=statement.id,
            escalation_day=escalation_day,
            escalation_stage=stage,
            balance_at_escalation=statement.balance_due,
            days_overdue=days_overdue,
            action_taken=f"Sent {template_type.value} communication",
            template_used=template.id if template else None,
            policy_reference="Wisconsin escalation schedule"
        )
        self.db.add(record)
        
        # Send communication
        if template:
            self.send_statement(statement, template_type)
        
        self._log_action(
            action_type="escalation_triggered",
            description=f"Triggered {stage} for statement #{statement.statement_number}. "
                       f"{days_overdue} days overdue. Balance: ${statement.balance_due:.2f}",
            statement_id=statement.id,
            policy_reference=f"Wisconsin escalation day {escalation_day}",
            metadata={
                "escalation_day": escalation_day,
                "stage": stage,
                "days_overdue": days_overdue
            }
        )
    
    def generate_health_snapshot(self, period: str = "monthly") -> BillingHealthSnapshot:
        """
        Generate Founder's Billing Health Dashboard snapshot.
        Answers: Is billing healthy, stable, and under control?
        """
        from sqlalchemy import func
        
        # Calculate metrics
        total_charges = self.db.query(func.sum(PatientStatement.total_charges)).scalar() or 0
        total_collected = self.db.query(func.sum(PatientStatement.amount_paid)).scalar() or 0
        outstanding = self.db.query(func.sum(PatientStatement.balance_due)).filter(
            PatientStatement.balance_due > 0
        ).scalar() or 0
        
        collection_rate = (total_collected / total_charges * 100) if total_charges > 0 else 0
        
        # Statement delivery health
        statements_generated = self.db.query(func.count(PatientStatement.id)).scalar() or 0
        
        deliveries = self.db.query(StatementDeliveryLog).all()
        emails_delivered = sum(1 for d in deliveries if d.delivery_format == DeliveryFormat.EMAIL and d.success)
        emails_bounced = sum(1 for d in deliveries if d.delivery_format == DeliveryFormat.EMAIL and not d.success)
        mail_sent = sum(1 for d in deliveries if d.delivery_format == DeliveryFormat.LOB_PHYSICAL)
        mail_delivered = sum(1 for d in deliveries if d.delivery_format == DeliveryFormat.LOB_PHYSICAL and d.success)
        delivery_failures = sum(1 for d in deliveries if not d.success)
        
        # Aging
        aging = self._calculate_aging()
        
        # Risk metrics
        high_risk = self.db.query(func.count(PatientStatement.id)).filter(
            PatientStatement.balance_due > 1000,
            PatientStatement.due_date < datetime.utcnow() - timedelta(days=60)
        ).scalar() or 0
        
        active_escalations = self.db.query(func.count(CollectionsEscalationRecord.id)).filter(
            CollectionsEscalationRecord.resolved == False
        ).scalar() or 0
        
        # Tax metrics
        tax_records = self.db.query(TaxExemptionRecord).all()
        tax_collected = sum(r.tax_amount for r in tax_records)
        revenue_exempt = sum(r.revenue_amount for r in tax_records if r.exempt)
        
        # Determine overall status
        status, reason = self._determine_health_status(
            collection_rate, delivery_failures, high_risk, active_escalations
        )
        
        snapshot = BillingHealthSnapshot(
            period=period,
            overall_status=status,
            status_reason=reason,
            total_charges_billed=total_charges,
            total_payments_collected=total_collected,
            net_outstanding_balance=outstanding,
            collection_rate=collection_rate,
            statements_generated=statements_generated,
            emails_delivered=emails_delivered,
            emails_bounced=emails_bounced,
            physical_mail_sent=mail_sent,
            physical_mail_delivered=mail_delivered,
            delivery_failures=delivery_failures,
            aging_0_30_days=aging["0-30"],
            aging_31_60_days=aging["31-60"],
            aging_61_90_days=aging["61-90"],
            aging_over_90_days=aging["90+"],
            high_risk_balances=high_risk,
            active_escalations=active_escalations,
            tax_collected_total=tax_collected,
            revenue_tax_exempt=revenue_exempt,
            ai_explanation=self._generate_ai_explanation(status, reason)
        )
        
        self.db.add(snapshot)
        return snapshot
    
    def _calculate_aging(self) -> Dict[str, float]:
        """Calculate aging buckets."""
        now = datetime.utcnow()
        
        buckets = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        
        statements = self.db.query(PatientStatement).filter(
            PatientStatement.balance_due > 0
        ).all()
        
        for stmt in statements:
            days_old = (now - stmt.statement_date).days
            
            if days_old <= 30:
                buckets["0-30"] += stmt.balance_due
            elif days_old <= 60:
                buckets["31-60"] += stmt.balance_due
            elif days_old <= 90:
                buckets["61-90"] += stmt.balance_due
            else:
                buckets["90+"] += stmt.balance_due
        
        return buckets
    
    def _determine_health_status(
        self,
        collection_rate: float,
        delivery_failures: int,
        high_risk: int,
        escalations: int
    ) -> tuple:
        """Determine overall billing health status."""
        if collection_rate > 85 and delivery_failures < 5 and high_risk < 10:
            return BillingHealthStatus.HEALTHY, "Billing performance is strong and stable"
        elif collection_rate > 70 and delivery_failures < 10:
            return BillingHealthStatus.ATTENTION_NEEDED, "Minor issues detected, monitoring required"
        else:
            return BillingHealthStatus.AT_RISK, "Collection rate or delivery issues require attention"
    
    def _generate_ai_explanation(self, status: BillingHealthStatus, reason: str) -> str:
        """Generate concise one-sentence AI explanation."""
        return f"Status: {status.value}. {reason}."
    
    def _log_action(
        self,
        action_type: str,
        description: str,
        statement_id: Optional[int] = None,
        policy_reference: Optional[str] = None,
        outcome: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log AI action for Wisconsin operations."""
        log = AIBillingActionLog(
            action_type=action_type,
            action_description=description,
            statement_id=statement_id,
            policy_reference=policy_reference,
            outcome=outcome,
            outcome_details=metadata
        )
        self.db.add(log)
