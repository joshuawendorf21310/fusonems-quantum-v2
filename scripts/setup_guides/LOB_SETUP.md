# Lob Setup Guide - Paper Statement Mailing

## Overview

Lob.com provides physical mail services for sending paper statements to patients. This is essential for solo biller operations where AI assistance automates the billing process.

## 🎯 Why Lob?

- **Automated Paper Statements**: AI automatically sends paper statements when email fails or for high-balance accounts
- **Professional Appearance**: High-quality printed and mailed statements
- **Tracking**: Full USPS tracking for all mailings
- **Compliance**: HIPAA-compliant secure printing and mailing
- **Cost-Effective**: ~$1.00-$1.50 per first-class letter

## 📋 Setup Steps

### 1. Create Lob Account

1. **Sign Up**: Go to https://lob.com and create an account
2. **Verify Email**: Verify your email address
3. **Add Payment Method**: Add a credit card for billing

### 2. Get API Key

1. **Navigate to Settings**: Dashboard → Settings → API Keys
2. **Create Test Key** (for development):
   - Click "Create API Key"
   - Name: "FusionEMS Quantum - Test"
   - Environment: Test
   - Copy the key (starts with `test_...`)

3. **Create Live Key** (for production):
   - Name: "FusionEMS Quantum - Production"
   - Environment: Live
   - Copy the key (starts with `live_...`)

### 3. Configure in .env

Add to your `.env` file:

```bash
# ============================================================================
# LOB (PHYSICAL MAIL - PAPER STATEMENTS)
# ============================================================================
LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Use test_ for dev, live_ for production
LOB_ENABLED=true
LOB_FROM_ADDRESS_NAME=Fusion EMS Billing
LOB_FROM_ADDRESS_LINE1=123 Medical Plaza
LOB_FROM_ADDRESS_CITY=Healthcare City
LOB_FROM_ADDRESS_STATE=CA
LOB_FROM_ADDRESS_ZIP=90210
```

**Important**: Replace with your actual billing address!

### 4. Verify Address

Lob requires a verified "from" address. You can verify it in the Lob dashboard:
- Dashboard → Addresses → Verify Address
- Enter your billing address
- Lob will send a verification postcard
- Once verified, use that address in your config

## 🤖 AI Billing Assistance

The system includes AI-powered billing assistance that automatically:

### Automatic Actions

1. **Statement Generation**: AI generates patient statements automatically
2. **Channel Selection**: AI chooses email → physical mail → SMS based on:
   - Patient preferences
   - Previous delivery success rates
   - Balance amount (high balance → certified mail)
   - Configuration preferences

3. **Failover Logic**: 
   - If email fails, automatically sends paper statement after 48 hours
   - Tracks delivery success rates per channel
   - Learns which channel works best for each patient

4. **Escalation**: 
   - Automatically escalates overdue statements
   - Sends certified mail for high-balance accounts (>$1000)
   - Offers payment plans automatically

### AI Decision Making

The AI considers:
- **Balance Amount**: High balances get certified mail
- **Delivery History**: Uses success rates to choose best channel
- **Patient Preferences**: Respects configured channel order
- **Compliance**: Ensures HIPAA-compliant delivery

### Safety Boundaries

The AI **CANNOT**:
- ❌ Alter balances or charges
- ❌ Modify clinical documentation
- ❌ Submit legal filings
- ❌ Forgive balances without configuration
- ❌ Access or modify patient medical records

All actions are logged with full audit trail.

## 🔧 Configuration Options

### In Database (SoleBillerConfig)

Configure via API or database:

```python
{
    "enabled": true,
    "ai_autonomous_approval_threshold": 500.0,  # Auto-approve statements under $500
    "auto_send_statements": true,
    "auto_escalate_overdue": true,
    "auto_offer_payment_plans": true,
    "preferred_channel_order": ["email", "physical_mail", "sms"],
    "email_failover_to_mail": true,
    "failover_delay_hours": 48,  # Wait 48h before sending paper statement
    "escalation_schedule_days": [30, 60, 90],  # Escalate at these intervals
    "payment_plan_min_balance": 200.0,
    "payment_plan_max_months": 12
}
```

## 📊 Monitoring

### Check Lob Dashboard

1. **Letters**: View all sent letters
2. **Tracking**: See delivery status and tracking numbers
3. **Costs**: Monitor spending per statement
4. **Webhooks**: Receive delivery status updates

### In Application

- View all statements in billing dashboard
- See delivery status and tracking numbers
- Review AI decisions and audit logs
- Monitor failover events

## 🧪 Testing

### Test Statement Sending

```bash
# Test via API
curl -X POST http://localhost:8000/api/billing/statements/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "statement_id": 123,
    "channel": "physical_mail"
  }'
```

### Test Lob Connection

```bash
python scripts/test_lob.py
```

## 💰 Pricing

- **First Class Mail**: ~$1.00-$1.50 per letter
- **Certified Mail**: ~$7.00-$9.00 per letter
- **Postcards**: ~$0.50-$0.75 per postcard

**Recommendation**: Use first-class for regular statements, certified for high-balance or overdue accounts.

## 🔐 Security

- **API Keys**: Store securely, never commit to git
- **Address Verification**: Required by Lob for compliance
- **HIPAA Compliance**: Lob is HIPAA-compliant
- **Audit Trail**: All actions logged with timestamps

## 📝 Webhook Setup

Lob can send webhooks for delivery status updates:

1. **Create Webhook**: Dashboard → Settings → Webhooks
2. **URL**: `https://api.fusionemsquantum.com/api/lob/webhook`
3. **Events**: Select "letter.created", "letter.delivered", "letter.failed"
4. **Secret**: Store webhook secret securely

## ✅ Verification Checklist

- [ ] Lob account created
- [ ] API key obtained (test and live)
- [ ] API key added to `.env`
- [ ] From address configured
- [ ] Address verified in Lob dashboard
- [ ] `LOB_ENABLED=true` set
- [ ] Test statement sent successfully
- [ ] Webhook configured (optional)
- [ ] AI billing service enabled in database

## 🆘 Troubleshooting

### "Lob API key not configured"
- Check `.env` has `LOB_API_KEY` set
- Verify key starts with `test_` or `live_`
- Restart application after adding key

### "Address not verified"
- Verify address in Lob dashboard
- Wait for verification postcard
- Use verified address in config

### "Letter creation failed"
- Check patient address is complete
- Verify from address is valid
- Check Lob account has sufficient balance
- Review Lob dashboard for error details

### AI Not Sending Statements
- Check `SoleBillerConfig.enabled = true`
- Verify `auto_send_statements = true`
- Check AI autonomous threshold settings
- Review audit logs for AI decisions

## 📚 Additional Resources

- **Lob Documentation**: https://docs.lob.com
- **Lob API Reference**: https://docs.lob.com/#letters
- **Lob Dashboard**: https://dashboard.lob.com
- **Support**: support@lob.com

---

**Status**: Ready for configuration! Add your Lob API key to `.env` and enable the service.
