# Verify & Activate Lob from Platform Email

## 🎯 Quick Steps

### Step 1: Fetch Email into Platform

**Option A: Via Platform UI** (Recommended)
1. Log into your platform dashboard
2. Navigate to **Email Dashboard** or **Communications**
3. Click **"Poll Inbox"** or **"Fetch Emails"** button
4. Wait for emails to be fetched

**Option B: Via API**
```bash
curl -X POST http://localhost:8000/api/email/poll-inbound \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

**Option C: Direct Email Access**
- Log into: `joshua.j.wendorf@fusionemsquantum.com`
- Search for "Lob" in your inbox

### Step 2: Find Lob Email in Platform

1. **In Email Dashboard**:
   - Search for: `Lob` or `lob.com`
   - Filter by sender: `lob.com`, `noreply@lob.com`, `support@lob.com`
   - Look for subjects containing: "verify", "verification", "activate", "welcome"

2. **Check Recent Emails**:
   - Go to: `/api/founder/email/recent`
   - Or view in Email Dashboard widget

### Step 3: Extract Verification Link

When you find the Lob email:

1. **Open the email** in platform
2. **Look for links** in the email body:
   - Usually blue/underlined text
   - URLs starting with `https://`
   - Often says "Click here to verify" or "Activate account"

3. **Common link formats**:
   ```
   https://dashboard.lob.com/verify?token=...
   https://lob.com/verify?email=...
   https://dashboard.lob.com/activate?token=...
   ```

### Step 4: Click Verification Link

1. **Copy the link** from the email
2. **Open in browser** (or click if platform supports it)
3. **Complete verification**:
   - Verify your email address
   - Set up your account
   - Complete any required steps

### Step 5: Get API Key

After verification:

1. **Go to**: https://dashboard.lob.com/settings/api-keys
2. **Create API Key** (if needed):
   - Click "Create API Key"
   - Name it: "FusionEMS Quantum"
   - Select environment: Test (for development)
3. **Copy the API key** (starts with `test_` or `live_`)

### Step 6: Configure Platform

Add to your `.env` file:

```bash
LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LOB_ENABLED=true
LOB_FROM_ADDRESS_NAME=Fusion EMS Billing
LOB_FROM_ADDRESS_LINE1=Your Street Address
LOB_FROM_ADDRESS_CITY=Your City
LOB_FROM_ADDRESS_STATE=Your State
LOB_FROM_ADDRESS_ZIP=Your ZIP
```

### Step 7: Test Connection

```bash
python3 scripts/test_lob.py
```

## 🔍 Finding the Email in Platform

### Via API Endpoints

**Get Recent Emails:**
```bash
GET /api/founder/email/recent?limit=50
```

**Search Messages:**
```bash
GET /api/email/messages?search=Lob
```

**Get Email Threads:**
```bash
GET /api/email/threads
```

### Via Platform UI

1. **Email Dashboard**: Shows recent emails
2. **Search Bar**: Search for "Lob"
3. **Filters**: Filter by sender or subject
4. **Email Details**: Click email to view full content and links

## 🔗 Common Verification Links

If you can't find the email, try these direct links:

### Email Verification
```
https://dashboard.lob.com/verify
```

### Account Activation
```
https://dashboard.lob.com/activate
```

### API Keys (After Verification)
```
https://dashboard.lob.com/settings/api-keys
```

### Address Verification
```
https://dashboard.lob.com/addresses
```

## 🚀 Alternative: Direct Access (No Email Needed)

You can verify and activate **without the email**:

1. **Go to**: https://dashboard.lob.com
2. **Sign up/Log in** with: `joshua.j.wendorf@fusionemsquantum.com`
3. **Complete account setup**
4. **Verify email** (if prompted)
5. **Get API key** from Settings → API Keys
6. **Add to .env** and enable

## 📧 Email Search Tips

### Search Terms
- `Lob`
- `lob.com`
- `verify`
- `verification`
- `activate`
- `API key`
- `welcome`

### Sender Addresses
- `noreply@lob.com`
- `support@lob.com`
- `hello@lob.com`
- `notifications@lob.com`

### Check These Folders
- Inbox
- Spam/Junk
- All Mail
- Unread

## ✅ Verification Checklist

- [ ] Email fetched into platform (via poll-inbound)
- [ ] Lob email found in platform
- [ ] Verification link extracted from email
- [ ] Link clicked and verification completed
- [ ] API key obtained from Lob dashboard
- [ ] API key added to `.env`
- [ ] `LOB_ENABLED=true` set
- [ ] Billing address configured
- [ ] Connection tested successfully

## 🆘 Troubleshooting

### Can't Find Email in Platform
1. **Poll inbox first**: Use `/api/email/poll-inbound`
2. **Check spam folder**: Lob emails sometimes marked as spam
3. **Search all folders**: Not just inbox
4. **Use direct access**: Go to Lob dashboard directly

### Verification Link Not Working
1. **Check if expired**: Links may expire after 24-48 hours
2. **Request new link**: Go to Lob dashboard → Resend verification
3. **Use direct access**: Verify through dashboard instead

### Can't Access Platform Email
1. **Check IMAP settings**: Verify `.env` has correct IMAP credentials
2. **Test IMAP connection**: Use email client to verify
3. **Use direct email**: Check email directly instead

---

**Tip**: The fastest way is often to just go directly to https://dashboard.lob.com and verify there - you don't need the email!
