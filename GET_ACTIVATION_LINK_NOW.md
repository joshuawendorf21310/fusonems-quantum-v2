# Get Lob Activation Link - Quick Guide

## 🚀 Fastest Way to Get Your Activation Link

### Option 1: Extract from Email (If You Have It)

1. **Open the Lob email** in your platform
2. **Copy the entire email body** (Ctrl+A, Ctrl+C)
3. **Run this command**:
   ```bash
   python3 scripts/extract_lob_activation_link.py
   ```
4. **Paste the email content** and press Ctrl+D
5. **The script will show you the activation link**

### Option 2: Direct Activation (No Email Needed)

**Just go directly to Lob and activate:**

1. **Open this link**: https://dashboard.lob.com
2. **Sign up/Log in** with: `joshua.j.wendorf@fusionemsquantum.com`
3. **If you need to reset password**: Click "Forgot Password"
4. **Complete account setup**
5. **Verify your email** (if prompted)
6. **Get API key**: https://dashboard.lob.com/settings/api-keys

### Option 3: Common Activation Links

Try these direct links (may work if you're logged in):

- **Verify Email**: https://dashboard.lob.com/verify
- **Activate Account**: https://dashboard.lob.com/activate
- **Get Started**: https://dashboard.lob.com/get-started

## 📧 If You Need to Find the Email

### In Platform:
1. Go to **Email Dashboard**
2. Search for: `Lob`
3. Look for email with subject: "Verify", "Activate", or "Welcome"
4. Open it and copy the link

### Direct Email Access:
1. Log into: `joshua.j.wendorf@fusionemsquantum.com`
2. Search for: `Lob`
3. Check spam folder too
4. Open email and click the activation link

## ✅ After Activation

1. **Get API Key**: https://dashboard.lob.com/settings/api-keys
2. **Add to .env**:
   ```bash
   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LOB_ENABLED=true
   ```
3. **Test**: `python3 scripts/test_lob.py`

---

**Quickest**: Just go to https://dashboard.lob.com and sign up/log in - you don't need the email!
