# Office Ally Configuration Guide
**Date:** January 30, 2026  
**Status:** ✅ **CONFIGURED AND READY**

---

## ✅ Your Office Ally Credentials

Based on the email you provided, your Office Ally SFTP credentials are:

```
Host: ftp10.officeally.com
Username: joshua.wendorf
Port: 22
Password: [Will be sent in separate email - check SPAM folder]
```

**Important:** Copy and paste the password from the email to avoid typing errors.

---

## 🔧 Environment Configuration

Add these to your `backend/.env` file:

```bash
# Enable Office Ally
OFFICEALLY_ENABLED=true

# Office Ally SFTP Credentials
OFFICEALLY_FTP_HOST=ftp10.officeally.com
OFFICEALLY_FTP_PORT=22
OFFICEALLY_FTP_USER=joshua.wendorf
OFFICEALLY_FTP_PASSWORD=<paste_password_from_email>

# Office Ally Directories
OFFICEALLY_SFTP_DIRECTORY=inbound        # For claim submissions
OFFICEALLY_SFTP_OUTBOUND_DIRECTORY=outbound  # For ERA/835 reports

# Office Ally Identifiers (get from Office Ally account)
OFFICEALLY_INTERCHANGE_ID=FUSIONEMS
OFFICEALLY_TRADING_PARTNER_ID=FUSIONEMS001
OFFICEALLY_SUBMITTER_NAME=FUSION EMS BILLING
OFFICEALLY_SUBMITTER_ID=FUSIONEMS001
OFFICEALLY_CONTACT_PHONE=555-555-5555
OFFICEALLY_DEFAULT_NPI=1234567890  # Your actual NPI
```

---

## 📁 Directory Structure

Office Ally uses two directories:

### 1. **inbound** folder (Submissions)
- **Purpose:** Upload claim files (EDI 837P)
- **Action:** Files placed here are automatically picked up for processing
- **Usage:** Our system uploads claim files here

### 2. **outbound** folder (Reports)
- **Purpose:** Download reports and ERA/835 files
- **Action:** Office Ally places reports here when available
- **Usage:** Our system downloads ERA/835 files from here

---

## 🚀 How It Works

### Submitting Claims

1. **Create Claim** → Status: `"ready"`
2. **Call Sync Endpoint:**
   ```bash
   POST /api/billing/office-ally/sync
   ```
3. **System:**
   - Gathers all claims with status `"ready"`
   - Generates EDI 837P files
   - Uploads to `inbound` folder via SFTP
   - Updates claim status to `"submitted"`
   - Creates export snapshot for audit

### Receiving ERA/835 Files

1. **Office Ally processes claims** → Generates ERA/835 files
2. **Files appear in `outbound` folder** (zip files with ANSI 835 + human-readable)
3. **Call Remittance Endpoint:**
   ```bash
   POST /api/billing/office-ally/post-payment
   ```
4. **System:**
   - Downloads ERA/835 files from `outbound` folder
   - Parses remittance data
   - Updates claim status to `"paid"`
   - Records payment information

---

## ✅ Features Implemented

### 1. Claim Submission
- ✅ EDI 837P generation (X12 005010X222A1)
- ✅ SFTP upload to `inbound` folder
- ✅ Batch processing (up to 10 claims per batch)
- ✅ Export snapshots for audit trail
- ✅ Automatic status updates

### 2. ERA/835 Processing
- ✅ SFTP download from `outbound` folder
- ✅ File listing and detection
- ✅ Remittance processing
- ✅ Claim status updates

### 3. Additional Features
- ✅ Eligibility checking
- ✅ Batch status tracking
- ✅ Error handling
- ✅ Training mode support

---

## 🔐 Security Notes

1. **SSH Key Caching:** Office Ally requires caching SSH keys - our code handles this automatically
2. **Password:** Copy/paste from email to avoid typos
3. **SFTP Only:** Office Ally requires SFTP (not FTP) - our implementation uses paramiko
4. **Confidential:** Office Ally emails contain PHI - handle securely

---

## 📋 Testing Checklist

### Before Production:

- [ ] Set `OFFICEALLY_FTP_PASSWORD` in `.env` (from separate email)
- [ ] Verify SFTP connection works:
  ```bash
  # Test connection manually with SFTP client
  sftp joshua.wendorf@ftp10.officeally.com
  ```
- [ ] Test claim submission with test claim
- [ ] Verify file appears in `inbound` folder
- [ ] Check Office Ally dashboard for claim status
- [ ] Test ERA/835 download from `outbound` folder
- [ ] Verify remittance processing works

---

## 🐛 Troubleshooting

### Connection Issues

**Problem:** Cannot connect to SFTP server
- **Check:** Password copied correctly (no extra spaces)
- **Check:** Port 22 is open
- **Check:** Hostname is correct: `ftp10.officeally.com`
- **Check:** Username is correct: `joshua.wendorf`

### File Upload Issues

**Problem:** Files not appearing in `inbound` folder
- **Check:** File is uploaded to `inbound` folder (not root)
- **Check:** File permissions allow write access
- **Check:** Office Ally is processing files (check dashboard)

### ERA/835 Issues

**Problem:** No ERA files found
- **Check:** ERA/835 enrollment is complete
- **Check:** Claims have been processed by payers
- **Check:** Files are in `outbound` folder (not `inbound`)

---

## 📞 Office Ally Support

If you need help:
- **Email:** Reply to the Office Ally setup email
- **Request:** 999 and/or 277CA reports (optional)
- **Note:** 999s acknowledge Office Ally's receipt, not payer's receipt
- **Note:** 277CAs contain Office Ally's initial responses only

---

## ✅ Status: READY FOR CONFIGURATION

**Next Steps:**
1. ✅ Host, username, port configured
2. ⏳ **Add password to `.env`** (from separate email)
3. ⏳ Test SFTP connection
4. ⏳ Submit test claim
5. ⏳ Verify claim processing

Once password is added and connection tested, Office Ally is ready to process claims!

---

**Last Updated:** January 30, 2026  
**Status:** ✅ **CONFIGURED - AWAITING PASSWORD**
