# Get Lob Activation Link from Platform Email

## 🎯 Quick Method

### Step 1: Access the Email in Platform

1. **Log into your platform dashboard**
2. **Go to Email Dashboard** or **Communications**
3. **Search for**: `Lob` or `lob.com`
4. **Open the Lob email** (usually subject contains "verify", "activate", or "welcome")

### Step 2: Extract the Activation Link

**Option A: Use the Extraction Script** (Recommended)

1. **Copy the email body/content** from the platform
2. **Run the script**:
   ```bash
   python3 scripts/extract_lob_activation_link.py
   ```
3. **Paste the email content** when prompted
4. **Press Ctrl+D** or type `done` when finished
5. **The script will show you the activation link(s)**

**Option B: Manual Extraction**

1. **Open the email** in platform
2. **Look for blue/underlined links** in the email body
3. **Common link text**:
   - "Click here to activate"
   - "Verify your account"
   - "Activate your account"
   - "Complete setup"
4. **Right-click the link** → Copy Link Address
5. **Or look for URLs** starting with `https://dashboard.lob.com/` or `https://lob.com/`

### Step 3: Activate Your Account

1. **Copy the activation link** (from script or email)
2. **Open it in your web browser**
3. **Complete the activation process**:
   - Verify your email address
   - Set up your account
   - Complete any required steps

### Step 4: Get Your API Key

After activation:

1. **Go to**: https://dashboard.lob.com/settings/api-keys
2. **Create API Key** (if needed):
   - Click "Create API Key"
   - Name: "FusionEMS Quantum"
   - Environment: Test (for development)
3. **Copy the API key** (starts with `test_` or `live_`)

### Step 5: Configure Platform

Add to `.env`:
```bash
LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LOB_ENABLED=true
LOB_FROM_ADDRESS_NAME=Fusion EMS Billing
LOB_FROM_ADDRESS_LINE1=Your Street Address
LOB_FROM_ADDRESS_CITY=Your City
LOB_FROM_ADDRESS_STATE=Your State
LOB_FROM_ADDRESS_ZIP=Your ZIP
```

## 🔍 Finding the Email

### In Platform UI

1. **Email Dashboard**:
   - Shows recent emails
   - Search bar at top
   - Filter by sender or subject

2. **Search Tips**:
   - Search: `Lob`
   - Filter sender: `lob.com`, `noreply@lob.com`
   - Look for: "verify", "activate", "welcome" in subject

3. **Email Details**:
   - Click email to open full view
   - Look for links in body
   - Check HTML view if available

### Via API

**Get Recent Emails:**
```bash
GET /api/founder/email/recent?limit=50
```

**Search Messages:**
```bash
GET /api/email/messages?search=Lob
```

**Get Specific Email:**
```bash
GET /api/email/messages/{message_id}
```

## 🔗 Common Activation Link Formats

The activation link usually looks like:

```
https://dashboard.lob.com/verify?token=xxxxxxxxxxxxx
https://lob.com/verify?email=your@email.com&token=xxxxx
https://dashboard.lob.com/activate?key=xxxxxxxxxxxxx
https://lob.com/activate?token=xxxxxxxxxxxxx
```

## 📧 Email Content Example

The email typically contains:
- **Subject**: "Verify your Lob account" or "Activate your account"
- **Body**: Contains a button or link saying "Activate Account" or "Verify Email"
- **Link**: Usually in a blue button or underlined text

## 🚀 Quick Alternative (No Email Needed)

If you can't find the email, activate directly:

1. **Go to**: https://dashboard.lob.com
2. **Sign up/Log in** with: `joshua.j.wendorf@fusionemsquantum.com`
3. **Click "Forgot Password"** if needed to reset
4. **Complete account setup**
5. **Verify email** (if prompted)
6. **Get API key** from Settings → API Keys

## 🆘 Troubleshooting

### Can't Find Email in Platform
1. **Poll inbox first**: Use "Poll Inbox" button or `/api/email/poll-inbound`
2. **Check spam**: Lob emails sometimes marked as spam
3. **Search all folders**: Not just inbox
4. **Check email directly**: Log into `joshua.j.wendorf@fusionemsquantum.com`

### Activation Link Not Working
1. **Check expiration**: Links may expire after 24-48 hours
2. **Request new link**: Go to Lob dashboard → Resend verification
3. **Use direct access**: Activate through dashboard instead

### Script Not Finding Link
1. **Copy full email**: Include HTML if available
2. **Check email source**: View raw email to see all links
3. **Manual search**: Look for `https://` in email content

## ✅ Checklist

- [ ] Email found in platform
- [ ] Email content copied
- [ ] Activation link extracted
- [ ] Link clicked and account activated
- [ ] API key obtained
- [ ] API key added to `.env`
- [ ] `LOB_ENABLED=true` set
- [ ] Connection tested

---

**Tip**: The extraction script (`extract_lob_activation_link.py`) will automatically find and highlight the activation link for you!
