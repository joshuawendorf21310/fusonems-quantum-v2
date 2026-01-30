from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from models.founder_billing import (
    PatientStatement, StatementDelivery, BillingAuditLog, StatementEscalation,
    LobMailJob, SoleBillerConfig, AIBillingDecision,
    StatementLifecycleState, DeliveryChannel, AIActionType
)
import lob
from jinja2 import Template

from core.config import settings
from services.email.email_transport_service import send_smtp_email_simple

logger = logging.getLogger(__name__)


class SoleBillerService:
    """
    AI-managed billing service that operates autonomously under Founder authority.
    
    Core Principles:
    - AI acts as agent with delegated authority from Founder
    - No per-action approval required within configured boundaries
    - Full audit trail: "Action executed by AI agent under Founder billing authority"
    - Autonomous channel selection with email → physical mail failover
    - Statement lifecycle management with AI state transitions
    - Hard safety boundaries enforced
    """
    
    def __init__(self, db: Session, config: SoleBillerConfig):
        self.db = db
        self.config = config
        self.lob_client = lob.Client(api_key=config.lob_api_key) if config.lob_api_key else None
    
    def generate_statement(
        self,
        patient_id: int,
        call_id: Optional[int],
        charges: List[Dict],
        insurance_paid: float,
        adjustments: float
    ) -> PatientStatement:
        """
        AI generates patient statement automatically.
        No approval needed if within autonomous threshold.
        """
        total_charges = sum(charge['amount'] for charge in charges)
        patient_responsibility = total_charges - insurance_paid - adjustments
        
        statement = PatientStatement(
            patient_id=patient_id,
            call_id=call_id,
            statement_number=self._generate_statement_number(),
            statement_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            total_charges=total_charges,
            insurance_paid=insurance_paid,
            adjustments=adjustments,
            patient_responsibility=patient_responsibility,
            balance_due=patient_responsibility,
            ai_generated=True,
            ai_approved_at=datetime.utcnow(),
            lifecycle_state=StatementLifecycleState.DRAFTED,
            itemized_charges=charges
        )
        
        self.db.add(statement)
        self.db.flush()
        
        # Log AI action
        self._log_audit(
            statement_id=statement.id,
            action_type=AIActionType.STATEMENT_GENERATED,
            description=f"AI generated statement #{statement.statement_number} for patient {patient_id}. "
                       f"Balance: ${patient_responsibility:.2f}",
            metadata={
                "total_charges": total_charges,
                "insurance_paid": insurance_paid,
                "patient_responsibility": patient_responsibility,
                "itemized_charges": charges
            }
        )
        
        # Auto-finalize if within autonomous threshold
        if patient_responsibility <= self.config.ai_autonomous_approval_threshold:
            self._finalize_statement(statement)
        
        return statement
    
    def _finalize_statement(self, statement: PatientStatement):
        """Finalize statement and prepare for sending."""
        statement.lifecycle_state = StatementLifecycleState.FINALIZED
        
        self._log_audit(
            statement_id=statement.id,
            action_type=AIActionType.STATEMENT_FINALIZED,
            description=f"AI finalized statement #{statement.statement_number}. Ready for delivery.",
            previous_state="drafted",
            new_state="finalized"
        )
        
        # Auto-send if enabled
        if self.config.auto_send_statements:
            self.send_statement(statement.id)
    
    def send_statement(self, statement_id: int) -> StatementDelivery:
        """
        AI autonomously selects delivery channel and sends statement.
        Implements email → physical mail failover logic.
        """
        statement = self.db.query(PatientStatement).filter_by(id=statement_id).first()
        if not statement:
            raise ValueError(f"Statement {statement_id} not found")
        
        # AI channel selection
        channel, reason = self._select_optimal_channel(statement)
        
        delivery = StatementDelivery(
            statement_id=statement.id,
            channel=channel,
            ai_selected_channel=True,
            channel_selection_reason=reason,
            attempted_at=datetime.utcnow()
        )
        
        self.db.add(delivery)
        self.db.flush()
        
        # Execute delivery
        success = False
        if channel == DeliveryChannel.EMAIL:
            success = self._send_via_email(statement, delivery)
        elif channel == DeliveryChannel.PHYSICAL_MAIL:
            success = self._send_via_lob(statement, delivery)
        elif channel == DeliveryChannel.SMS:
            success = self._send_via_sms(statement, delivery)
        
        delivery.success = success
        if success:
            delivery.delivered_at = datetime.utcnow()
            statement.lifecycle_state = StatementLifecycleState.SENT
        
        self._log_audit(
            statement_id=statement.id,
            delivery_id=delivery.id,
            action_type=AIActionType.STATEMENT_SENT,
            description=f"AI sent statement #{statement.statement_number} via {channel.value}. "
                       f"Success: {success}. Reason: {reason}",
            metadata={"channel": channel.value, "success": success, "reason": reason}
        )
        
        # Schedule failover if email failed
        if not success and channel == DeliveryChannel.EMAIL and self.config.email_failover_to_mail:
            delivery.next_retry_at = datetime.utcnow() + timedelta(hours=self.config.failover_delay_hours)
            logger.info(f"Scheduled physical mail failover for statement {statement.id} "
                       f"at {delivery.next_retry_at}")
        
        return delivery
    
    def _select_optimal_channel(self, statement: PatientStatement) -> Tuple[DeliveryChannel, str]:
        """
        AI selects optimal delivery channel based on:
        - Patient preferences
        - Previous delivery success rates
        - Balance amount (high balance → certified mail)
        - Configuration preferences
        """
        patient = statement.patient
        
        # Check previous delivery history
        prev_deliveries = self.db.query(StatementDelivery).join(PatientStatement).filter(
            PatientStatement.patient_id == patient.id
        ).order_by(StatementDelivery.created_at.desc()).limit(5).all()
        
        email_success_rate = self._calculate_success_rate(prev_deliveries, DeliveryChannel.EMAIL)
        mail_success_rate = self._calculate_success_rate(prev_deliveries, DeliveryChannel.PHYSICAL_MAIL)
        
        # Decision logic
        if email_success_rate > 0.8 and patient.email:
            return DeliveryChannel.EMAIL, f"Email success rate {email_success_rate:.1%} with valid email"
        
        if statement.balance_due > 1000 and patient.address:
            return DeliveryChannel.PHYSICAL_MAIL, f"High balance ${statement.balance_due:.2f} warrants certified mail"
        
        # Follow configured preference order
        for channel_name in self.config.preferred_channel_order:
            channel = DeliveryChannel(channel_name)
            if channel == DeliveryChannel.EMAIL and patient.email:
                return channel, "Configured preference: email first"
            elif channel == DeliveryChannel.PHYSICAL_MAIL and patient.address:
                return channel, "Configured preference: physical mail"
            elif channel == DeliveryChannel.SMS and patient.phone:
                return channel, "Configured preference: SMS"
        
        # Default fallback
        if patient.email:
            return DeliveryChannel.EMAIL, "Fallback: email available"
        elif patient.address:
            return DeliveryChannel.PHYSICAL_MAIL, "Fallback: physical address available"
        else:
            return DeliveryChannel.SMS, "Fallback: SMS only option"
    
    def _calculate_success_rate(self, deliveries: List[StatementDelivery], channel: DeliveryChannel) -> float:
        """Calculate success rate for a specific delivery channel."""
        channel_deliveries = [d for d in deliveries if d.channel == channel]
        if not channel_deliveries:
            return 0.5  # Neutral baseline
        
        successes = sum(1 for d in channel_deliveries if d.success)
        return successes / len(channel_deliveries)
    
    def _send_via_email(self, statement: PatientStatement, delivery: StatementDelivery) -> bool:
        """Send statement via SMTP (Mailu/self-hosted)."""
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.error("SMTP not configured")
            delivery.failure_reason = "SMTP settings not configured"
            return False

        patient = statement.patient
        if not patient.email:
            delivery.failure_reason = "Patient email not available"
            return False

        try:
            html_content = self._generate_statement_html(statement)
            subject = f"Statement #{statement.statement_number} - Balance Due: ${statement.balance_due:.2f}"
            from_addr = settings.BILLING_FROM_EMAIL or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
            send_smtp_email_simple(
                to=patient.email,
                subject=subject,
                html_body=html_content,
                from_addr=from_addr,
            )
            delivery.email_address = patient.email
            delivery.postmark_message_id = None  # SMTP; no external message ID
            return True
        except Exception as e:
            logger.error(f"Email send failed: {str(e)}")
            delivery.failure_reason = str(e)
            return False
    
    def _send_via_lob(self, statement: PatientStatement, delivery: StatementDelivery) -> bool:
        """Send statement via Lob physical mail."""
        if not self.lob_client:
            logger.error("Lob client not configured")
            delivery.failure_reason = "Lob API key not configured"
            return False
        
        patient = statement.patient
        if not patient.address:
            delivery.failure_reason = "Patient address not available"
            return False
        
        try:
            # Generate statement HTML for Lob
            html_content = self._generate_statement_html(statement, for_print=True)
            
            # Create Lob letter
            letter = self.lob_client.Letter.create(
                description=f"Patient Statement {statement.statement_number}",
                to_address={
                    "name": f"{patient.first_name} {patient.last_name}",
                    "address_line1": patient.address_line1,
                    "address_line2": patient.address_line2 or "",
                    "address_city": patient.city,
                    "address_state": patient.state,
                    "address_zip": patient.zip_code
                },
                from_address={
                    "name": "Fusion EMS Billing",
                    "address_line1": "123 Medical Plaza",
                    "address_city": "Healthcare City",
                    "address_state": "CA",
                    "address_zip": "90210"
                },
                file=html_content,
                color=self.config.lob_api_key and True,
                double_sided=True,
                mail_type="usps_first_class"
            )
            
            # Record Lob job
            lob_job = LobMailJob(
                delivery_id=delivery.id,
                lob_letter_id=letter.id,
                lob_url=letter.url,
                to_address=letter.to_address,
                from_address=letter.from_address,
                expected_delivery_date=letter.expected_delivery_date,
                tracking_number=letter.tracking_number if hasattr(letter, 'tracking_number') else None,
                status="created",
                cost=letter.get('price', 0)
            )
            self.db.add(lob_job)
            
            delivery.lob_mail_id = letter.id
            delivery.physical_address = letter.to_address
            
            return True
        
        except Exception as e:
            logger.error(f"Lob send failed: {str(e)}")
            delivery.failure_reason = str(e)
            return False
    
    def _send_via_sms(self, statement: PatientStatement, delivery: StatementDelivery) -> bool:
        """Send statement notification via SMS (Twilio)."""
        delivery.failure_reason = "SMS not yet implemented"
        return False
    
    def _generate_statement_html(self, statement: PatientStatement, for_print: bool = False) -> str:
        """Generate HTML content for statement."""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { text-align: center; margin-bottom: 30px; }
                .statement-info { margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .total { font-weight: bold; font-size: 1.2em; }
                .footer { margin-top: 40px; font-size: 0.9em; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Patient Statement</h1>
                <p>Fusion EMS</p>
            </div>
            
            <div class="statement-info">
                <p><strong>Statement #:</strong> {{ statement.statement_number }}</p>
                <p><strong>Statement Date:</strong> {{ statement.statement_date.strftime('%B %d, %Y') }}</p>
                <p><strong>Due Date:</strong> {{ statement.due_date.strftime('%B %d, %Y') }}</p>
                <p><strong>Patient:</strong> {{ patient.first_name }} {{ patient.last_name }}</p>
            </div>
            
            <h2>Charges</h2>
            <table>
                <tr>
                    <th>Service</th>
                    <th>Date</th>
                    <th>Amount</th>
                </tr>
                {% for charge in statement.itemized_charges %}
                <tr>
                    <td>{{ charge.description }}</td>
                    <td>{{ charge.date }}</td>
                    <td>${{ "%.2f"|format(charge.amount) }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <table>
                <tr>
                    <td>Total Charges:</td>
                    <td class="total">${{ "%.2f"|format(statement.total_charges) }}</td>
                </tr>
                <tr>
                    <td>Insurance Paid:</td>
                    <td>-${{ "%.2f"|format(statement.insurance_paid) }}</td>
                </tr>
                <tr>
                    <td>Adjustments:</td>
                    <td>-${{ "%.2f"|format(statement.adjustments) }}</td>
                </tr>
                <tr>
                    <td class="total">Balance Due:</td>
                    <td class="total">${{ "%.2f"|format(statement.balance_due) }}</td>
                </tr>
            </table>
            
            <div class="footer">
                <p>Please remit payment within 30 days. For payment arrangements, call (555) 123-4567.</p>
                <p><em>This statement was generated and sent by our AI billing system under authorized supervision.</em></p>
            </div>
        </body>
        </html>
        """)
        
        return template.render(statement=statement, patient=statement.patient)
    
    def process_failovers(self):
        """
        Process scheduled failovers (e.g., email → physical mail).
        Run this periodically as a background task.
        """
        pending_failovers = self.db.query(StatementDelivery).filter(
            StatementDelivery.success == False,
            StatementDelivery.next_retry_at <= datetime.utcnow(),
            StatementDelivery.retry_count < 3
        ).all()
        
        for delivery in pending_failovers:
            statement = delivery.statement
            
            # Escalate to physical mail
            new_delivery = StatementDelivery(
                statement_id=statement.id,
                channel=DeliveryChannel.PHYSICAL_MAIL,
                ai_selected_channel=True,
                channel_selection_reason=f"Automatic failover after {delivery.channel.value} failure",
                retry_count=delivery.retry_count + 1
            )
            self.db.add(new_delivery)
            self.db.flush()
            
            success = self._send_via_lob(statement, new_delivery)
            new_delivery.success = success
            
            self._log_audit(
                statement_id=statement.id,
                delivery_id=new_delivery.id,
                action_type=AIActionType.CHANNEL_SELECTED,
                description=f"AI escalated delivery to physical mail after {delivery.channel.value} failure",
                metadata={"original_channel": delivery.channel.value, "new_channel": "physical_mail"}
            )
    
    def process_escalations(self):
        """
        AI autonomously escalates overdue statements.
        Implements 30/60/90 day escalation schedule.
        """
        if not self.config.auto_escalate_overdue:
            return
        
        overdue_statements = self.db.query(PatientStatement).filter(
            PatientStatement.balance_due > 0,
            PatientStatement.due_date < datetime.utcnow(),
            PatientStatement.lifecycle_state != StatementLifecycleState.PAID
        ).all()
        
        for statement in overdue_statements:
            days_overdue = (datetime.utcnow() - statement.due_date).days
            
            # Check if escalation needed based on schedule
            should_escalate = False
            escalation_level = 1
            
            for level, threshold in enumerate(self.config.escalation_schedule_days, start=1):
                if days_overdue >= threshold:
                    # Check if we already escalated at this level
                    existing = self.db.query(StatementEscalation).filter(
                        StatementEscalation.statement_id == statement.id,
                        StatementEscalation.escalation_level == level,
                        StatementEscalation.resolved == False
                    ).first()
                    
                    if not existing:
                        should_escalate = True
                        escalation_level = level
                        break
            
            if should_escalate:
                self._create_escalation(statement, escalation_level, days_overdue)
    
    def _create_escalation(self, statement: PatientStatement, level: int, days_overdue: int):
        """Create escalation for overdue statement."""
        escalation = StatementEscalation(
            statement_id=statement.id,
            escalation_level=level,
            triggered_by="AI Agent",
            trigger_reason=f"Statement {days_overdue} days overdue",
            days_overdue=days_overdue,
            action_taken=f"Level {level} escalation: follow-up statement sent"
        )
        
        # Offer payment plan for eligible balances
        if (self.config.auto_offer_payment_plans and 
            statement.balance_due >= self.config.payment_plan_min_balance):
            escalation.payment_plan_offered = True
            escalation.payment_plan_terms = self._generate_payment_plan(statement.balance_due)
        
        self.db.add(escalation)
        self.db.flush()
        
        # Send follow-up
        delivery = self.send_statement(statement.id)
        
        self._log_audit(
            statement_id=statement.id,
            action_type=AIActionType.ESCALATION_TRIGGERED,
            description=f"AI triggered level {level} escalation for statement #{statement.statement_number}. "
                       f"{days_overdue} days overdue. Payment plan offered: {escalation.payment_plan_offered}",
            metadata={
                "escalation_level": level,
                "days_overdue": days_overdue,
                "payment_plan_offered": escalation.payment_plan_offered,
                "payment_plan_terms": escalation.payment_plan_terms
            }
        )
        
        statement.lifecycle_state = StatementLifecycleState.ESCALATED
    
    def _generate_payment_plan(self, balance: float) -> Dict:
        """Generate payment plan terms."""
        months = min(12, int(balance / 50))  # $50/month minimum
        monthly_payment = balance / months
        
        return {
            "total_balance": balance,
            "monthly_payment": round(monthly_payment, 2),
            "number_of_payments": months,
            "first_payment_due": (datetime.utcnow() + timedelta(days=15)).isoformat()
        }
    
    def _log_audit(
        self,
        action_type: AIActionType,
        description: str,
        statement_id: Optional[int] = None,
        delivery_id: Optional[int] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log AI action with full audit trail."""
        log = BillingAuditLog(
            statement_id=statement_id,
            delivery_id=delivery_id,
            action_type=action_type,
            action_description=description,
            executed_by="AI Agent under Founder billing authority",
            previous_state=previous_state,
            new_state=new_state,
            metadata=metadata or {}
        )
        self.db.add(log)
    
    def _generate_statement_number(self) -> str:
        """Generate unique statement number."""
        count = self.db.query(PatientStatement).count()
        return f"STMT-{datetime.utcnow().strftime('%Y%m')}-{count + 1:05d}"
