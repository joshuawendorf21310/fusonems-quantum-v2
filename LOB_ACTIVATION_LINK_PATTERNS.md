# Lob Activation Link Patterns

## 🔗 Common Lob Activation Link Formats

Since Lob sent an email to `joshua.j.wendorf@fusionemsquantum.com`, here are the typical activation link patterns:

### Most Common Formats:

1. **Email Verification Link**:
   ```
   https://dashboard.lob.com/verify?token=xxxxxxxxxxxxxxxxxxxxx
   https://lob.com/verify?email=joshua.j.wendorf@fusionemsquantum.com&token=xxxxx
   ```

2. **Account Activation Link**:
   ```
   https://dashboard.lob.com/activate?token=xxxxxxxxxxxxxxxxxxxxx
   https://lob.com/activate?key=xxxxxxxxxxxxxxxxxxxxx
   ```

3. **Welcome/Setup Link**:
   ```
   https://dashboard.lob.com/welcome?token=xxxxxxxxxxxxxxxxxxxxx
   https://lob.com/get-started?token=xxxxxxxxxxxxxxxxxxxxx
   ```

## 🚀 Direct Activation (No Email Needed)

**You can activate directly without the email:**

1. **Go to**: https://dashboard.lob.com
2. **Click**: "Sign Up" or "Log In"
3. **Enter**: `joshua.j.wendorf@fusionemsquantum.com`
4. **If account exists**: Click "Forgot Password" to reset
5. **If new**: Complete signup, then verify email
6. **After login**: Go to Settings → API Keys

## 📧 When You Can Access Platform Email

### Option 1: Extract Link from Email

1. **Access platform email dashboard**
2. **Find Lob email** (search for "Lob")
3. **Copy email body**
4. **Run**:
   ```bash
   python3 scripts/extract_lob_activation_link.py
   ```
5. **Paste email content** → Get activation link

### Option 2: View Email Source

1. **Open Lob email** in platform
2. **View email source/HTML** (if available)
3. **Search for**: `https://dashboard.lob.com` or `https://lob.com`
4. **Copy the link** that contains `verify`, `activate`, or `token`

## 🔍 Finding the Email in Platform

### Via API (if platform is running):

```bash
# Get recent emails
curl -X GET "http://localhost:8000/api/founder/email/recent?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search for Lob emails
curl -X GET "http://localhost:8000/api/email/messages?search=Lob" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Via Platform UI:

1. Log into platform
2. Go to Email Dashboard
3. Search for: `Lob` or `lob.com`
4. Filter by sender: `lob.com`
5. Open the email

## ✅ Quick Activation Steps

**Fastest Method** (No email needed):

1. **Visit**: https://dashboard.lob.com
2. **Sign up/Log in** with your email
3. **Complete activation**
4. **Get API key**: https://dashboard.lob.com/settings/api-keys
5. **Add to .env**:
   ```bash
   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LOB_ENABLED=true
   ```

## 🆘 If Link Doesn't Work

1. **Link may have expired** (usually 24-48 hours)
2. **Request new verification**: Go to dashboard → Resend verification email
3. **Or activate directly**: Use dashboard signup/login

---

**Recommendation**: Just go to https://dashboard.lob.com and sign up/log in directly - you don't need the email link!
