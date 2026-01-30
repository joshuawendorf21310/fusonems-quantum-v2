# How to Check Your Email for Lob Messages

## 🔍 Quick Check Options

### Option 1: Check Email Directly (Recommended)

Since the IMAP server may not be accessible from the development environment, check your email directly:

1. **Log into your email**: `joshua.j.wendorf@fusionemsquantum.com`
2. **Search for**: 
   - "Lob" or "lob.com" in subject
   - Emails from: `noreply@lob.com`, `support@lob.com`, `hello@lob.com`
3. **Check spam/junk folder** - Lob verification emails sometimes go there

### Option 2: Use Platform Email Polling

If your platform is running, you can use the built-in email polling:

**Via API:**
```bash
curl -X POST http://localhost:8000/api/email/poll-inbound \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This will:
- Connect to your IMAP server
- Fetch new emails
- Ingest them into the platform
- You can then view them in the email dashboard

### Option 3: Check Email Dashboard

If emails are already ingested:

1. **Log into platform**
2. **Navigate to**: Email Dashboard or Communications
3. **Search for**: "Lob" or filter by sender

## 📧 What to Look For

Lob typically sends emails for:

1. **Account Verification**:
   - Subject: "Verify your Lob account" or "Welcome to Lob"
   - Contains: Verification link or API key

2. **API Key Information**:
   - Subject: "Your API Keys" or "API Key Created"
   - Contains: Your test/live API keys

3. **Address Verification**:
   - Subject: "Verify your address" or "Address verification required"
   - Contains: Instructions to verify your billing address

4. **Account Setup**:
   - Subject: "Get started with Lob" or "Complete your setup"
   - Contains: Setup instructions

## 🔑 Finding Your Lob API Key

If you find a Lob email, look for:

- **Test API Key**: Starts with `test_...`
- **Live API Key**: Starts with `live_...`
- **API Key Location**: Usually in email body or dashboard link

## 📝 Next Steps After Finding Email

1. **Copy API Key** from email
2. **Add to .env**:
   ```bash
   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LOB_ENABLED=true
   ```
3. **Verify Address** in Lob dashboard (if required)
4. **Test Connection**:
   ```bash
   python3 scripts/test_lob.py
   ```

## 🆘 If You Can't Find the Email

1. **Check Spam/Junk Folder**
2. **Check All Mail** (not just inbox)
3. **Search All Folders** for "Lob"
4. **Check Lob Dashboard**: https://dashboard.lob.com
   - Go to Settings → API Keys
   - You can create/view API keys there directly

## 🔗 Direct Access

If you can't find the email, you can:

1. **Log into Lob Dashboard**: https://dashboard.lob.com
2. **Go to**: Settings → API Keys
3. **Create New Key** or **View Existing Keys**
4. **Copy the API key** and add to `.env`

---

**Note**: The email check script (`scripts/check_email_for_lob.py`) requires direct IMAP access which may not be available in all environments. Use the methods above to check your email instead.
