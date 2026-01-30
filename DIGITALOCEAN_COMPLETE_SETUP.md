# Complete DigitalOcean Setup Guide
**Date:** January 30, 2026  
**Strategy:** Single-Platform Approach - Everything on DigitalOcean ✅

---

## 🎯 Why Stay on DigitalOcean?

**Benefits of Single Platform:**
- ✅ **Unified Billing** - One invoice, easier budgeting
- ✅ **Simplified Management** - One dashboard for everything
- ✅ **Better Integration** - Services work seamlessly together
- ✅ **Easier Support** - One support team for all issues
- ✅ **Cost Optimization** - Can bundle services for discounts
- ✅ **Network Performance** - Services in same data center = faster

---

## 📦 Your DigitalOcean Stack

### Current Services:
1. ✅ **Droplets** - Your application servers
2. ✅ **Databases** - PostgreSQL (if using managed DB)
3. ✅ **Spaces** - File storage (to be configured)
4. ✅ **Load Balancers** - Traffic distribution (if using)
5. ✅ **VPC** - Private networking (if using)

### All in One Place! 🎉

---

## 🚀 DigitalOcean Spaces Setup

### Step 1: Create Spaces Bucket

1. **Log into DigitalOcean Console**
   - Go to https://cloud.digitalocean.com
   - Navigate to **Spaces** → **Create a Space**

2. **Configure Your Space:**
   ```
   Name: fusonems-quantum-storage
   Region: [Choose same region as your Droplets]
   File Listing: Restricted (Private) ✅
   CDN: Optional (enable for faster file delivery)
   ```

3. **Choose Region:**
   - **Match your Droplets region** for best performance
   - Common regions: `nyc3`, `sfo3`, `ams3`, `sgp1`
   - Example: If Droplets are in NYC3, use NYC3 Spaces

4. **Note Your Endpoint:**
   - Format: `https://{region}.digitaloceanspaces.com`
   - Example: `https://nyc3.digitaloceanspaces.com`

---

### Step 2: Generate Access Keys

1. **Navigate to API → Spaces Keys**
   - In DigitalOcean Console: **API** → **Spaces Keys**

2. **Generate New Key:**
   - Click **"Generate New Key"**
   - **Name:** "FusonEMS Quantum Storage"
   - **Save both:**
     - ✅ **Access Key ID** (starts with `DO...`)
     - ✅ **Secret Access Key** (shown only once!)

3. **⚠️ Important:** 
   - Store keys securely (password manager)
   - Secret shown only once!

---

### Step 3: Add to `.env` File

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
- `nyc3` with your actual region
- `fusonems-quantum-storage` with your bucket name
- `DOXXXXXXXXXXXXXXXXXXXXX` with your Access Key ID
- `your-secret-key-here` with your Secret Access Key

---

## 🔗 DigitalOcean Integration Benefits

### 1. **Same Data Center = Faster**
- Droplets and Spaces in same region
- Lower latency for file operations
- Better performance overall

### 2. **Unified Networking**
- Use DigitalOcean VPC for private networking
- Keep traffic internal (no egress fees)
- Better security

### 3. **Single Dashboard**
- Monitor everything in one place
- Easier troubleshooting
- Unified alerts

### 4. **Cost Optimization**
- Bundle services for discounts
- Predictable billing
- Easier to optimize costs

---

## 📊 What Gets Stored in Spaces

- ✅ **ePCR Documents** - Patient care reports, PDFs
- ✅ **Billing Documents** - Invoices, claims, remittances
- ✅ **Fax Documents** - Inbound/outbound faxes
- ✅ **Email Attachments** - Email attachments
- ✅ **Workspace Files** - Documents, spreadsheets
- ✅ **Accounting Files** - Receipts, exports
- ✅ **App Builder Artifacts** - Source files, builds

---

## 🧪 Test Your Setup

After adding credentials:

```bash
cd /root/fusonems-quantum-v2/backend
python3 -c "
from services.storage import get_storage_service
storage = get_storage_service()
print('✅ DigitalOcean Spaces connected!')
print(f'   Bucket: {storage.bucket_name}')
print(f'   Region: {storage.region}')
"
```

---

## 💰 Cost Estimation

**DigitalOcean Spaces Pricing:**
- **Storage:** $5/month per 250GB
- **Bandwidth:** First 1TB free, then $0.01/GB
- **Operations:** Free (GET/PUT/DELETE)

**Typical Usage:**
- Small deployment: ~$5-10/month
- Medium deployment: ~$10-20/month
- Large deployment: ~$20-50/month

**All on one bill with your Droplets!** 💳

---

## ✅ Best Practices

### 1. **Match Regions**
- Use same region for Droplets and Spaces
- Reduces latency
- Better performance

### 2. **Enable CDN** (Optional)
- Faster file delivery globally
- Good for public assets
- Costs extra but worth it for scale

### 3. **Use VPC** (If Available)
- Private networking between services
- No egress fees for internal traffic
- Better security

### 4. **Monitor Usage**
- Check Spaces usage in dashboard
- Set up alerts for quota limits
- Optimize storage regularly

---

## 🎯 Complete DigitalOcean Stack

Once configured, you'll have:

```
┌─────────────────────────────────────┐
│     DigitalOcean Platform            │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐    ┌──────────┐     │
│  │ Droplets │───▶│ Databases│     │
│  │ (App)    │    │ (Postgres)│    │
│  └──────────┘    └──────────┘     │
│       │                │            │
│       └───────┬────────┘            │
│               │                     │
│               ▼                     │
│         ┌──────────┐                │
│         │  Spaces  │                │
│         │ (Storage)│                │
│         └──────────┘                │
│                                     │
│  All in one platform! ✅            │
└─────────────────────────────────────┘
```

---

## 🚀 Next Steps

1. ✅ Create Spaces bucket in DigitalOcean
2. ✅ Generate access keys
3. ✅ Add credentials to `.env` file
4. ✅ Test connection
5. ✅ Start using storage!

---

## ✅ Status: Ready to Configure

**You're making the right choice staying on DigitalOcean!**

- ✅ Simpler management
- ✅ Unified billing
- ✅ Better integration
- ✅ Easier support
- ✅ Cost optimization

Once you add the Spaces credentials, everything will be on one platform! 🎉

---

**Last Updated:** January 30, 2026  
**Strategy:** Single-Platform (DigitalOcean) ✅
