# Systems Setup & Improvement Required
**Date:** January 30, 2026  
**Status:** Comprehensive Platform Audit

---

## ✅ Already Configured

1. ✅ **DigitalOcean Spaces** - File storage configured
2. ✅ **Office Ally** - Billing clearinghouse configured
3. ✅ **Keycloak** - Authentication configured (dev mode)
4. ✅ **Document Storage** - Using DigitalOcean Spaces

---

## 🔴 CRITICAL - Must Configure for Production

### 1. **Security Keys** (CRITICAL - Production Blockers)

**Current Status:** Using default/weak values  
**Location:** `.env` lines 11-13

```bash
JWT_SECRET_KEY=change-me                    # ❌ MUST CHANGE
STORAGE_ENCRYPTION_KEY=change-me            # ❌ MUST CHANGE
DOCS_ENCRYPTION_KEY=change-me               # ❌ MUST CHANGE
```

**Action Required:**
- Generate strong, random 32+ character secrets
- Use different values for each key
- Store securely (password manager)

**Impact:** Platform will fail production validation if not changed.

---

### 2. **Email System (SMTP/IMAP)** (CRITICAL)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
SMTP_HOST=mail.fusionemsquantum.com
SMTP_PORT=587
SMTP_USERNAME=joshua.j.wendorf@fusionemsquantum.com
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true

IMAP_HOST=mail.fusionemsquantum.com
IMAP_PORT=993
IMAP_USERNAME=joshua.j.wendorf@fusionemsquantum.com
IMAP_PASSWORD=your-imap-password
IMAP_USE_TLS=true

FOUNDER_EMAIL=joshua.j.wendorf@fusionemsquantum.com
BILLING_FROM_EMAIL=billing@fusionemsquantum.com
SUPPORT_EMAIL=billing@fusionemsquantum.com
```

**Impact:** Cannot send/receive emails without this.

---

### 3. **Telnyx (Phone/SMS/Fax)** (HIGH PRIORITY)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
TELNYX_API_KEY=your-telnyx-api-key
TELNYX_FROM_NUMBER=+1234567890
TELNYX_CONNECTION_ID=your-connection-id
TELNYX_MESSAGING_PROFILE_ID=your-profile-id
TELNYX_PUBLIC_KEY=your-public-key
TELNYX_ENABLED=true
TELNYX_FAX_FROM_NUMBER=+1234567890
TELNYX_FAX_CONNECTION_ID=your-fax-connection-id
APP_BASE_URL=https://api.fusionemsquantum.com
```

**Impact:** Cannot make calls, send SMS, or send/receive faxes.

**Setup Steps:**
1. Create Telnyx account
2. Get API key
3. Purchase phone numbers
4. Configure webhooks
5. Add credentials to `.env`

---

### 4. **Stripe (Payments)** (HIGH PRIORITY)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_ENV=production
STRIPE_ENFORCE_ENTITLEMENTS=true

# Price IDs for each module
STRIPE_PRICE_ID_CORE_MONTHLY=price_...
STRIPE_PRICE_ID_CAD=price_...
STRIPE_PRICE_ID_EPCR=price_...
STRIPE_PRICE_ID_BILLING=price_...
# ... etc
```

**Impact:** Cannot process payments or manage subscriptions.

**Setup Steps:**
1. Create Stripe account
2. Get API keys
3. Create products/prices
4. Configure webhooks
5. Add credentials to `.env`

---

### 5. **CAD Backend Connection** (HIGH PRIORITY)

**Current Status:** Using defaults  
**Location:** `.env` - Missing

**Required Variables:**
```bash
CAD_BACKEND_URL=http://localhost:3000  # Update to production URL
CAD_BACKEND_AUTH_TOKEN=strong-random-token-32-chars-minimum
```

**Impact:** Real-time CAD integration won't work.

**Action:** Update URL and generate strong auth token.

---

## 🟡 IMPORTANT - Should Configure

### 6. **Metriport (Medical Records)** (OPTIONAL but Recommended)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
METRIPORT_ENABLED=true
METRIPORT_API_KEY=your-metriport-api-key
METRIPORT_BASE_URL=https://api.metriport.com/medical/v1
METRIPORT_FACILITY_ID=your-facility-id
METRIPORT_WEBHOOK_SECRET=your-webhook-secret
```

**Impact:** No patient history lookup, no EMR integration.

**Benefits:**
- Repeat patient detection
- Medical history access
- EMR data sync

---

### 7. **Ollama (AI Assistant)** (OPTIONAL)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
OLLAMA_ENABLED=true
OLLAMA_SERVER_URL=http://localhost:11434  # Or your Ollama server
OLLAMA_IVR_MODEL=llama3.2
```

**Impact:** No AI billing assistance, no IVR voice agent.

**Benefits:**
- AI-powered billing help
- Automated phone answering
- Smart suggestions

**Setup:** Install Ollama locally or on server.

---

### 8. **NEMSIS State Submission** (OPTIONAL)

**Current Status:** Not configured  
**Location:** Missing from `.env`

**Required Variables:**
```bash
NEMSIS_STATE_CODES=WI
NEMSIS_STATE_ENDPOINTS={"WI": "https://..."}
WISCONSIN_NEMSIS_ENDPOINT=https://...
```

**Impact:** Cannot submit ePCR data to state systems.

**Benefits:**
- Automated state reporting
- Compliance with regulations

---

### 9. **Office Ally - Complete Configuration** (MEDIUM)

**Current Status:** Partial (only FTP credentials)  
**Location:** `.env` lines 27-28

**Missing Variables:**
```bash
OFFICEALLY_ENABLED=true
OFFICEALLY_INTERCHANGE_ID=your-interchange-id
OFFICEALLY_TRADING_PARTNER_ID=your-trading-partner-id
OFFICEALLY_SUBMITTER_NAME=your-submitter-name
OFFICEALLY_SUBMITTER_ID=your-submitter-id
OFFICEALLY_CONTACT_PHONE=555-555-5555
OFFICEALLY_DEFAULT_NPI=1234567890
OFFICEALLY_FTP_HOST=ftp10.officeally.com
OFFICEALLY_FTP_PORT=22
OFFICEALLY_SFTP_DIRECTORY=inbound
OFFICEALLY_SFTP_OUTBOUND_DIRECTORY=outbound
```

**Action:** Get these values from Office Ally account.

---

## 🔧 CODE IMPROVEMENTS NEEDED

### High Priority Code Issues

1. **HTTP Client Timeouts** (CRITICAL)
   - **Issue:** Many `httpx.AsyncClient()` calls lack timeouts
   - **Files:** `metriport_service.py`, `telnyx_fax_provider.py`, `ollama_client.py`
   - **Fix:** Add `timeout=30.0` to all HTTP clients
   - **Impact:** Can cause hanging requests

2. **N+1 Query Problem** (HIGH)
   - **Location:** `backend/services/epcr/epcr_router.py:485`
   - **Issue:** Queries patient for each record individually
   - **Fix:** Use `joinedload` for eager loading
   - **Impact:** Performance degradation at scale

3. **Missing Pagination Limits** (HIGH)
   - **Location:** Multiple endpoints
   - **Issue:** `.all()` queries without limits
   - **Fix:** Add pagination with max limits (e.g., 500)
   - **Impact:** Memory exhaustion with large datasets

4. **Missing Retry Logic** (HIGH)
   - **Issue:** No retries on external API failures
   - **Fix:** Add retry with exponential backoff
   - **Impact:** Single network hiccup causes permanent failure

---

## 📋 Configuration Checklist

### Production Essentials

- [ ] **Security Keys** - Generate strong secrets (32+ chars each)
- [ ] **SMTP/IMAP** - Configure email sending/receiving
- [ ] **Telnyx** - Configure phone/SMS/fax
- [ ] **Stripe** - Configure payments
- [ ] **CAD Backend** - Update URL and auth token
- [ ] **Office Ally** - Complete configuration

### Optional but Recommended

- [ ] **Metriport** - Medical records integration
- [ ] **Ollama** - AI assistant
- [ ] **NEMSIS** - State submission endpoints

### Code Improvements

- [ ] **HTTP Timeouts** - Add to all clients
- [ ] **N+1 Queries** - Fix eager loading
- [ ] **Pagination** - Add limits to all queries
- [ ] **Retry Logic** - Add to external APIs

---

## 🎯 Priority Order

### Week 1 (Critical for Production)
1. ✅ Generate strong security keys
2. ✅ Configure SMTP/IMAP
3. ✅ Configure Telnyx
4. ✅ Configure Stripe
5. ✅ Update CAD backend URL/token

### Week 2 (Important Features)
6. ✅ Complete Office Ally config
7. ✅ Configure Metriport (if needed)
8. ✅ Set up Ollama (if using AI)

### Week 3 (Code Improvements)
9. ✅ Fix HTTP timeouts
10. ✅ Fix N+1 queries
11. ✅ Add pagination limits
12. ✅ Add retry logic

---

## 📊 Current Status Summary

| System | Status | Priority |
|--------|--------|----------|
| **Security Keys** | ❌ Using defaults | 🔴 CRITICAL |
| **Email (SMTP/IMAP)** | ❌ Not configured | 🔴 CRITICAL |
| **Telnyx** | ❌ Not configured | 🔴 CRITICAL |
| **Stripe** | ❌ Not configured | 🔴 CRITICAL |
| **CAD Backend** | ⚠️ Using defaults | 🔴 CRITICAL |
| **Office Ally** | ⚠️ Partial | 🟡 IMPORTANT |
| **Metriport** | ❌ Not configured | 🟡 OPTIONAL |
| **Ollama** | ❌ Not configured | 🟡 OPTIONAL |
| **DigitalOcean Spaces** | ✅ Configured | ✅ DONE |
| **Document Storage** | ✅ Configured | ✅ DONE |

---

## 🚀 Next Steps

1. **Immediate:** Generate production security keys
2. **This Week:** Configure email, Telnyx, Stripe
3. **Next Week:** Complete Office Ally, optional services
4. **Ongoing:** Code improvements (timeouts, queries, pagination)

---

**Last Updated:** January 30, 2026  
**Status:** 🔴 **CRITICAL SYSTEMS NEED CONFIGURATION**
