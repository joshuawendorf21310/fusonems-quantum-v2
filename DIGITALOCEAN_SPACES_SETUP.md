# DigitalOcean Spaces Setup Guide
**Date:** January 30, 2026

---

## 🚀 Quick Setup Steps

### 1. Create DigitalOcean Spaces Bucket

1. **Log into DigitalOcean Console**
   - Go to https://cloud.digitalocean.com
   - Navigate to **Spaces** → **Create a Space**

2. **Configure Your Space:**
   - **Name:** `fusonems-quantum-storage` (or your preferred name)
   - **Region:** Choose closest to your users (e.g., `nyc3`, `sfo3`, `ams3`)
   - **File Listing:** **Restricted** (Private) ✅
   - **CDN:** Optional (can enable later)

3. **Note Your Endpoint:**
   - Format: `https://{region}.digitaloceanspaces.com`
   - Example: `https://nyc3.digitaloceanspaces.com`

---

### 2. Generate Access Keys

1. **Navigate to API → Spaces Keys**
   - In DigitalOcean Console, go to **API** → **Spaces Keys**

2. **Generate New Key:**
   - Click **"Generate New Key"**
   - **Name:** "FusonEMS Quantum Storage"
   - **Save both:**
     - ✅ **Access Key ID** (starts with `DO...`)
     - ✅ **Secret Access Key** (shown only once - save securely!)

3. **⚠️ Important:** Store keys in password manager - secret is shown only once!

---

### 3. Configure CORS (Optional but Recommended)

If you need direct browser access to files:

1. **In Spaces bucket settings → CORS**
2. **Add CORS rule:**
   ```json
   {
     "CORSRules": [
       {
         "AllowedOrigins": [
           "https://your-production-domain.com",
           "http://localhost:5173",
           "http://localhost:3000"
         ],
         "AllowedMethods": ["GET", "HEAD"],
         "AllowedHeaders": ["*"],
         "MaxAgeSeconds": 3000
       }
     ]
   }
   ```

---

### 4. Add to Your `.env` File

Add these lines to `/root/fusonems-quantum-v2/.env`:

```bash
# DigitalOcean Spaces Configuration
SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
SPACES_REGION=nyc3
SPACES_BUCKET=fusonems-quantum-storage
SPACES_ACCESS_KEY=DOXXXXXXXXXXXXXXXXXXXXX
SPACES_SECRET_KEY=your-secret-key-here
SPACES_CDN_ENDPOINT=
```

**Replace:**
- `nyc3` with your region (nyc3, sfo3, ams3, etc.)
- `fusonems-quantum-storage` with your bucket name
- `DOXXXXXXXXXXXXXXXXXXXXX` with your Access Key ID
- `your-secret-key-here` with your Secret Access Key

---

## ✅ What Gets Stored in Spaces

The platform uses DigitalOcean Spaces for:

- ✅ **ePCR Documents** - Patient care reports, PDFs
- ✅ **Billing Documents** - Invoices, claims, remittances
- ✅ **Fax Documents** - Inbound/outbound faxes
- ✅ **Email Attachments** - Email attachments
- ✅ **Workspace Files** - Documents, spreadsheets, presentations
- ✅ **Accounting Files** - Receipts, exports
- ✅ **App Builder Artifacts** - Source files, builds

---

## 📁 File Organization

Files are organized by path structure:

```
/{orgId}/{system}/{objectType}/{objectId}/{filename}
```

**Example:**
```
org-123/epcr/document/epcr-456/20260130_report.pdf
org-123/billing/invoice/inv-789/invoice.pdf
org-123/communications/email-attachment/msg-101/attachment.jpg
```

---

## 🔒 Security Features

- ✅ **Private by Default** - All files are private
- ✅ **Signed URLs** - Short-lived access URLs (5-15 minutes)
- ✅ **Role-Based Access** - Only authorized users can access files
- ✅ **Audit Logging** - All file operations are logged
- ✅ **Soft Deletes** - Files can be recovered if needed

---

## 🧪 Test Your Configuration

After adding credentials, test the connection:

```bash
# In your backend container or local environment
cd /root/fusonems-quantum-v2/backend
python -c "
from services.storage import get_storage_service
storage = get_storage_service()
print('✅ DigitalOcean Spaces connected successfully!')
"
```

---

## 📊 Monitoring

Check storage usage in DigitalOcean Console:
- **Spaces** → Your bucket → **Metrics**
- Monitor storage size and bandwidth

---

## 🆘 Troubleshooting

### Connection Issues

**Problem:** "Storage service not properly configured"
- **Check:** All `SPACES_*` variables are set in `.env`
- **Check:** No trailing slashes in `SPACES_ENDPOINT`
- **Check:** Access keys are correct (copy/paste, no extra spaces)

### Upload Failures

**Problem:** Files not uploading
- **Check:** Bucket name matches `SPACES_BUCKET`
- **Check:** Access key has write permissions
- **Check:** Region matches endpoint region

### Access Denied

**Problem:** Cannot access files
- **Check:** Files are accessed via signed URLs (not direct links)
- **Check:** Signed URL hasn't expired (default 10 minutes)
- **Check:** User has proper role permissions

---

## 💰 Cost Estimation

DigitalOcean Spaces pricing (as of 2026):
- **Storage:** $5/month per 250 GB
- **Bandwidth:** $0.01/GB (first 1 TB free)
- **Operations:** Free (GET/PUT/DELETE)

**Typical usage:** ~$5-20/month for small to medium deployments

---

## ✅ Status: Ready to Configure

**Next Steps:**
1. ✅ Create Spaces bucket in DigitalOcean
2. ✅ Generate access keys
3. ✅ Add credentials to `.env` file
4. ✅ Test connection
5. ✅ Start using storage!

---

**Last Updated:** January 30, 2026
