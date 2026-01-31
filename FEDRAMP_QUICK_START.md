# 🚀 FedRAMP Features - Quick Start Guide

**Status:** All features implemented and ready to use  
**Compliance Level:** 50%+ FedRAMP High Impact controls

---

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements-fedramp.txt
```

### 2. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This creates tables for:
- Multi-Factor Authentication
- Account Lockout
- Comprehensive Audit Logs
- Security Incidents
- Vulnerability Tracking
- Configuration Management
- And more...

### 3. Update Environment Variables

Add to `backend/.env`:

```bash
# Required - Generate with: openssl rand -hex 32
KEY_MANAGEMENT_MASTER_KEY=<64-char-random-string>
ACCOUNT_LIFECYCLE_CRON_SECRET=<64-char-random-string>
VULNERABILITY_SCAN_CRON_SECRET=<64-char-random-string>

# Optional - Customize as needed
MFA_REQUIRED_FOR_PRODUCTION=true
ACCOUNT_LOCKOUT_THRESHOLD=5
SESSION_INACTIVITY_TIMEOUT_MINUTES=15
FIPS_MODE_ENABLED=false
```

### 4. Restart Backend

```bash
# The backend will automatically load new routers and middleware
uvicorn main:app --reload
```

---

## 🎯 Key Features & How to Use

### 1. Multi-Factor Authentication (MFA)

**Enable MFA for Your Account:**
```bash
# Enroll a device
POST /api/auth/mfa/enroll
{
  "device_name": "My iPhone",
  "device_type": "totp"
}

# Returns QR code - scan with Google Authenticator, Authy, etc.

# Verify enrollment with a code from your app
POST /api/auth/mfa/verify-enrollment
{
  "device_id": 123,
  "verification_code": "123456"
}

# Generate backup codes (use if you lose your device)
POST /api/auth/mfa/generate-backup-codes
```

**MFA Status:**
```bash
GET /api/auth/mfa/status
# Returns whether MFA is required and enrolled
```

### 2. Account Lockout Protection

**Automatic Features:**
- 5 failed login attempts = 30-minute lockout
- Automatic unlocking after timeout
- Audit trail of all lockouts

**Admin Unlock:**
```bash
POST /api/auth/admin/unlock-account
{
  "user_id": 123
}
```

### 3. Session Management

**Automatic Features:**
- 15-minute inactivity timeout
- 12-hour maximum session lifetime
- Max 5 concurrent sessions per user

**Admin Controls:**
```bash
# Terminate specific session
POST /api/auth/admin/terminate-session
{
  "session_id": "abc123"
}

# Terminate all user sessions
POST /api/auth/admin/terminate-all-sessions
{
  "user_id": 123
}

# List user sessions
GET /api/auth/admin/user-sessions/123
```

### 4. Comprehensive Audit Logging

**Query Audit Logs:**
```bash
GET /api/audit/logs?event_type=authentication&outcome=failure&limit=100
```

**Export Audit Logs:**
```bash
# CSV export
GET /api/audit/export/csv?start_date=2026-01-01&end_date=2026-01-31

# JSON export
GET /api/audit/export/json?event_type=security_event

# FedRAMP compliance report
GET /api/audit/compliance/fedramp
```

### 5. Security Incident Management

**Create Incident:**
```bash
POST /api/incidents
{
  "title": "Suspicious login attempts",
  "description": "Multiple failed logins from unknown IP",
  "classification": "MODERATE"
}
```

**Track Incidents:**
```bash
GET /api/incidents?status=NEW&classification=HIGH
```

**Update Investigation:**
```bash
PUT /api/incidents/123/investigation
{
  "root_cause": "Compromised credentials",
  "containment_actions": "Account locked, password reset required",
  "remediation_plan": "Enable MFA, review access logs"
}
```

### 6. Vulnerability Scanning

**Run Scan:**
```bash
POST /api/v1/security/vulnerabilities/scans
{
  "scan_type": "full",
  "components": ["python_packages", "npm_packages"]
}
```

**View Vulnerabilities:**
```bash
GET /api/v1/security/vulnerabilities/?severity=HIGH&status=OPEN
```

**Update Remediation:**
```bash
PATCH /api/v1/security/vulnerabilities/456/remediation
{
  "status": "IN_PROGRESS",
  "remediation_notes": "Upgrading to latest version",
  "target_date": "2026-02-15"
}
```

### 7. Configuration Management

**Create Baseline:**
```bash
POST /api/compliance/configuration/baselines
{
  "name": "Production Baseline v1.0",
  "description": "Initial production configuration"
}
```

**Check for Drift:**
```bash
GET /api/compliance/configuration/compliance/drift-report
```

**Request Configuration Change:**
```bash
POST /api/compliance/configuration/change-requests
{
  "change_type": "SECURITY_SETTING",
  "description": "Update TLS minimum version to 1.3",
  "justification": "FedRAMP requirement",
  "risk_level": "LOW"
}
```

### 8. Security Monitoring

**View Security Dashboard:**
```bash
GET /api/v1/security/monitoring/dashboard
```

**Get Active Alerts:**
```bash
GET /api/v1/security/monitoring/alerts?status=NEW
```

**Acknowledge Alert:**
```bash
PATCH /api/v1/security/monitoring/alerts/789/acknowledge
{
  "acknowledged_by": 123,
  "notes": "Investigating with security team"
}
```

### 9. FedRAMP Compliance Dashboard

**Overall Status:**
```bash
GET /api/compliance/fedramp/dashboard
```

Returns:
- Overall compliance percentage
- Status by control family
- Security posture
- Continuous monitoring metrics
- Recommendations

**Monthly ConMon Report:**
```bash
GET /api/compliance/fedramp/conmon/monthly-report
```

**Time Sync Status:**
```bash
GET /api/compliance/fedramp/time-sync/status
```

**FIPS Status:**
```bash
GET /api/compliance/fedramp/fips/status
```

**Readiness Assessment:**
```bash
GET /api/compliance/fedramp/readiness-assessment
```

---

## 🔄 Automated Jobs (Cron Setup)

### Daily Jobs

**Account Lifecycle Check:**
```bash
# Daily at 2 AM
0 2 * * * curl -X POST -H "X-Cron-Secret: $ACCOUNT_LIFECYCLE_CRON_SECRET" \
  https://api.fusionemsquantum.com/api/cron/account-lifecycle
```

**Incident Detection Scan:**
```bash
# Every 6 hours
0 */6 * * * curl -X POST \
  https://api.fusionemsquantum.com/api/incidents/detection/scan
```

### Weekly Jobs

**Vulnerability Scan:**
```bash
# Every Sunday at 3 AM
0 3 * * 0 curl -X POST -H "X-Cron-Secret: $VULNERABILITY_SCAN_CRON_SECRET" \
  https://api.fusionemsquantum.com/api/cron/vulnerability-scan
```

**Configuration Drift Check:**
```bash
# Every Monday at 6 AM
0 6 * * 1 curl -X POST \
  https://api.fusionemsquantum.com/api/compliance/configuration/compliance/check
```

### Monthly Jobs

**Generate ConMon Report:**
```bash
# First day of each month
0 8 1 * * curl -X GET \
  https://api.fusionemsquantum.com/api/compliance/fedramp/conmon/monthly-report
```

---

## 📱 Frontend Integration

### System Banner

The system use notification banner is automatically displayed to all users on their first login. No additional integration needed - it's already in the app layout!

### MFA Enrollment

Users can enroll MFA devices from their account settings page. Admin users see a prompt to enroll MFA on first login (required for FedRAMP).

### Compliance Dashboard

Founders and compliance officers can access the FedRAMP compliance dashboard from the admin panel.

---

## 🔍 Monitoring & Alerts

### What Gets Monitored

1. **Authentication Events**
   - All login attempts
   - MFA verifications
   - Account lockouts

2. **Authorization Events**
   - Access denials
   - Privilege escalations
   - Cross-org access attempts

3. **Security Events**
   - Suspicious activity
   - Anomalies
   - Threat indicators

4. **Configuration Changes**
   - Security settings
   - Access controls
   - Baseline drift

5. **Incidents**
   - Security incidents
   - Investigation status
   - Resolution tracking

### Alert Channels

- In-app dashboard
- Email notifications (configured)
- API webhooks (extensible)
- SIEM integration (configurable)

---

## 📊 Compliance Reporting

### Available Reports

1. **Monthly ConMon Report**
   - Required for FedRAMP
   - Authentication metrics
   - Authorization metrics
   - Security events
   - Configuration changes
   - Incident summary

2. **Audit Compliance Report**
   - Audit log statistics
   - Event breakdown
   - Compliance status

3. **Vulnerability Report**
   - Open vulnerabilities by severity
   - Remediation status
   - POA&M items

4. **Configuration Drift Report**
   - Drift from baseline
   - Compliance violations
   - Remediation recommendations

5. **Incident Report**
   - Incident statistics
   - Response times
   - Resolution status

---

## 🎯 Testing Your Implementation

### 1. Test MFA Enrollment

```bash
# As a user, enroll MFA
curl -X POST https://api.fusionemsquantum.com/api/auth/mfa/enroll \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_name": "Test Device", "device_type": "totp"}'
```

### 2. Test Account Lockout

```bash
# Try 6 failed logins to trigger lockout
for i in {1..6}; do
  curl -X POST https://api.fusionemsquantum.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrong"}'
done
```

### 3. Test Audit Logging

```bash
# Check recent audit logs
curl https://api.fusionemsquantum.com/api/audit/logs?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Test Time Sync

```bash
# Check NTP sync status
curl https://api.fusionemsquantum.com/api/compliance/fedramp/time-sync/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Test Compliance Dashboard

```bash
# Get overall compliance status
curl https://api.fusionemsquantum.com/api/compliance/fedramp/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🏆 Success Criteria

You'll know it's working when:

✅ MFA enrollment works and generates QR codes  
✅ Account lockout triggers after 5 failed attempts  
✅ Sessions timeout after 15 minutes of inactivity  
✅ Audit logs capture all events  
✅ Time sync shows < 5 seconds drift  
✅ Compliance dashboard shows 50%+ compliance  
✅ Security incidents can be created and tracked  
✅ Vulnerability scans detect CVEs  

---

## 📞 Support & Resources

### Documentation
- `FEDRAMP_COMPLIANCE_ROADMAP.md` - Full roadmap
- `FEDRAMP_IMPLEMENTATION_STATUS.md` - Detailed status
- `FEDRAMP_ACHIEVEMENT.md` - What was achieved
- `FEDRAMP_QUICK_START.md` - This guide

### External Resources
- FedRAMP.gov - Official guidance
- NIST SP 800-53 - Control catalog
- FedRAMP PMO - Package templates
- FedRAMP Marketplace - 3PAO list

---

**You now have a FedRAMP-grade security platform! 🎉**

Next: Complete remaining controls and begin formal assessment process.
