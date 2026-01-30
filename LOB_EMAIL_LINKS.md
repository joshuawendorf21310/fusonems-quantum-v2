# Lob Email Links - Quick Reference

## 🔗 Common Links in Lob Emails

### Most Important Links

1. **Lob Dashboard** (Main Access)
   ```
   https://dashboard.lob.com
   ```
   - Log in to your account
   - View API keys
   - Manage settings

2. **API Keys Page** (Get Your API Key)
   ```
   https://dashboard.lob.com/settings/api-keys
   ```
   - View existing API keys
   - Create new API keys
   - Copy test/live keys

3. **Address Verification** (If Required)
   ```
   https://dashboard.lob.com/addresses
   ```
   - Verify your billing address
   - Required before sending mail

4. **Account Verification** (If Email Contains)
   ```
   https://dashboard.lob.com/verify
   ```
   - Verify your email address
   - Complete account setup

## 📧 What Links to Look For

### In Welcome/Verification Emails:
- **Verification Link**: Usually looks like `https://dashboard.lob.com/verify?token=...`
- **Get Started Link**: `https://dashboard.lob.com/get-started`
- **Dashboard Link**: `https://dashboard.lob.com`

### In API Key Emails:
- **View API Keys**: `https://dashboard.lob.com/settings/api-keys`
- **Create API Key**: `https://dashboard.lob.com/settings/api-keys/new`

### In Setup Emails:
- **Complete Setup**: `https://dashboard.lob.com/setup`
- **Verify Address**: `https://dashboard.lob.com/addresses/verify`

## 🔍 How to Extract Links from Email

### Option 1: Use the Script
```bash
# Paste email content when prompted
python3 scripts/extract_email_links.py

# Or provide email content as argument
python3 scripts/extract_email_links.py "paste email content here"
```

### Option 2: Manual Extraction
1. Open the Lob email
2. Look for blue/underlined links
3. Right-click → Copy Link Address
4. Or look for URLs starting with `https://`

### Option 3: View Email Source
1. In your email client, find "View Source" or "Show Original"
2. Search for `https://` or `http://`
3. Look for links containing `lob.com`

## 🎯 Quick Access (No Email Needed)

If you can't find the email, you can access these directly:

### 1. Log into Lob Dashboard
```
https://dashboard.lob.com
```
- Use your email: `joshua.j.wendorf@fusionemsquantum.com`
- Click "Forgot Password" if needed

### 2. Get API Key Directly
```
https://dashboard.lob.com/settings/api-keys
```
- Navigate to Settings → API Keys
- Create new key or view existing

### 3. Verify Address
```
https://dashboard.lob.com/addresses
```
- Add your billing address
- Verify it (Lob will send verification postcard)

## 📝 After Getting the Link

### If it's a Verification Link:
1. Click the link
2. Complete verification
3. Then get your API key

### If it's an API Key Link:
1. Click the link
2. Copy the API key (starts with `test_` or `live_`)
3. Add to `.env`:
   ```bash
   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LOB_ENABLED=true
   ```

### If it's a Dashboard Link:
1. Click the link
2. Log in
3. Go to Settings → API Keys
4. Copy your API key

## 🆘 Can't Find the Email?

1. **Check Spam/Junk Folder**
2. **Search All Mail** for "Lob"
3. **Check Trash/Deleted Items**
4. **Use Direct Links Above** - You don't need the email!

## ✅ Quick Setup (Without Email)

1. Go to: https://dashboard.lob.com
2. Sign up/Log in with: `joshua.j.wendorf@fusionemsquantum.com`
3. Go to: Settings → API Keys
4. Create API Key (Test environment)
5. Copy key and add to `.env`

---

**Tip**: You don't actually need the email - you can access everything directly through the Lob dashboard!
