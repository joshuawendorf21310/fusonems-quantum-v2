# Production Setup Guide

Complete guide for setting up all services for production deployment.

## 🔐 Step 1: Security Keys

All security keys have been generated. Verify they are set in `.env`:
- `JWT_SECRET_KEY` ✅ Generated
- `STORAGE_ENCRYPTION_KEY` ✅ Generated
- `DOCS_ENCRYPTION_KEY` ✅ Generated
- `CAD_BACKEND_AUTH_TOKEN` ✅ Generated

**Status**: ✅ Complete

## 📧 Step 2: Email Configuration (SMTP/IMAP)

### Current Configuration
- Host: `mail.fusionemsquantum.com`
- Port: `587` (SMTP), `993` (IMAP)
- Username: `joshua.j.wendorf@fusionemsquantum.com`

### Action Required
1. **Get SMTP Password**:
   - Log into Mailu admin panel
   - Navigate to user settings
   - Copy SMTP password
   - Set in `.env`: `SMTP_PASSWORD=your-password`

2. **Get IMAP Password** (same as SMTP):
   - Set in `.env`: `IMAP_PASSWORD=your-password`

3. **Test Email**:
   ```bash
   python scripts/test_email.py
   ```

**Status**: ⚠️ Requires password

## 📞 Step 3: Telnyx Configuration

### Setup Steps
1. **Create Telnyx Account**: https://telnyx.com
2. **Get API Key**:
   - Dashboard → API Keys
   - Create new API key
   - Set in `.env`: `TELNYX_API_KEY=your-key`

3. **Purchase Phone Number**:
   - Numbers → Buy Number
   - Set in `.env`: `TELNYX_FROM_NUMBER=+1234567890`

4. **Configure Messaging Profile**:
   - Messaging → Profiles
   - Create profile
   - Set in `.env`: `TELNYX_MESSAGING_PROFILE_ID=your-profile-id`

5. **Configure Fax** (if needed):
   - Connections → Create Fax Connection
   - Set in `.env`: `TELNYX_FAX_CONNECTION_ID=your-connection-id`

**Status**: ⚠️ Requires Telnyx account setup

## 💳 Step 4: Stripe Configuration

### Setup Steps
1. **Create Stripe Account**: https://stripe.com
2. **Get API Keys**:
   - Dashboard → Developers → API Keys
   - Copy Secret Key: `sk_test_...` or `sk_live_...`
   - Copy Publishable Key: `pk_test_...` or `pk_live_...`
   - Set in `.env`:
     ```
     STRIPE_SECRET_KEY=sk_live_...
     STRIPE_PUBLISHABLE_KEY=pk_live_...
     STRIPE_ENV=live
     ```

3. **Configure Webhook**:
   - Webhooks → Add endpoint
   - URL: `https://api.fusionemsquantum.com/api/webhooks/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.*`
   - Copy webhook secret
   - Set in `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`

4. **Create Price IDs** (if using subscriptions):
   - Products → Create products
   - Copy Price IDs
   - Set in `.env`: `STRIPE_PRICE_ID_CAD=price_...`

**Status**: ⚠️ Requires Stripe account setup

## 🏥 Step 5: Office Ally Configuration

### Current Status
- ✅ Host: `ftp10.officeally.com`
- ✅ Port: `22`
- ✅ Username: `joshua.wendorf`
- ✅ Password: Configured
- ✅ Directories: `inbound` / `outbound`

### Enable for Production
Set in `.env`:
```
OFFICEALLY_ENABLED=true
```

### Verify Configuration
```bash
python scripts/test_office_ally.py
```

**Status**: ✅ Configured (enable when ready)

## ☁️ Step 6: DigitalOcean Spaces

### Current Status
- ✅ Endpoint: `https://sfo3.digitaloceanspaces.com`
- ✅ Region: `sfo3`
- ✅ Bucket: `fusionems-quantum`
- ✅ Access Keys: Configured

### Optional: CDN Setup
1. Create CDN endpoint in DigitalOcean
2. Set in `.env`: `SPACES_CDN_ENDPOINT=https://...`

**Status**: ✅ Complete

## 🚨 Step 7: CAD Backend Configuration

### Current Configuration
- URL: `http://localhost:3000` (development)
- Auth Token: ✅ Generated

### Production Update Required
1. Deploy CAD backend to production
2. Update `.env`:
   ```
   CAD_BACKEND_URL=https://cad.fusionemsquantum.com
   ```

**Status**: ⚠️ Update URL for production

## 🔑 Step 8: Keycloak Configuration

### Current Configuration
- Base URL: `http://keycloak:8080` (development)
- Realm: `fusionems`
- Client ID: `fusionems-api`
- Client Secret: `dev-secret` ⚠️

### Production Update Required
1. Deploy Keycloak to production
2. Create production client
3. Update `.env`:
   ```
   KEYCLOAK_BASE_URL=https://auth.fusionemsquantum.com
   KEYCLOAK_CLIENT_SECRET=production-secret
   ```

**Status**: ⚠️ Update for production

## 🧪 Step 9: Optional Services

### Metriport (Medical Records)
- Status: Optional
- Setup: https://metriport.com
- Set `METRIPORT_ENABLED=true` when configured

### Ollama (AI Assistant)
- Status: Optional
- Setup: Self-hosted or cloud
- Set `OLLAMA_ENABLED=true` when configured

### NEMSIS State Submission
- Status: Optional
- Contact state EMS office for endpoint
- Set `WISCONSIN_NEMSIS_ENDPOINT=https://...`

## ✅ Step 10: Final Validation

Run validation script:
```bash
python scripts/validate_config.py
```

This will check:
- ✅ All required settings are present
- ✅ Security keys are strong
- ✅ Database is configured
- ⚠️ Optional services are configured

## 🚀 Step 11: Production Deployment

1. **Set Production Environment**:
   ```bash
   ENV=production
   ```

2. **Update Database URL**:
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/fusonems
   ```

3. **Update Allowed Origins**:
   ```bash
   ALLOWED_ORIGINS=https://fusionemsquantum.com,https://app.fusionemsquantum.com
   ```

4. **Run Migrations**:
   ```bash
   python scripts/migrate.py
   ```

5. **Start Services**:
   ```bash
   docker-compose up -d
   ```

## 📋 Checklist

- [ ] Security keys generated ✅
- [ ] Email passwords configured
- [ ] Telnyx API key configured
- [ ] Stripe keys configured
- [ ] Office Ally enabled (when ready)
- [ ] DigitalOcean Spaces configured ✅
- [ ] CAD backend URL updated
- [ ] Keycloak configured for production
- [ ] Database URL updated
- [ ] Allowed origins updated
- [ ] Validation script passes
- [ ] Production deployment tested

## 🆘 Troubleshooting

### Email Not Sending
- Check SMTP password is correct
- Verify SMTP host is accessible
- Check firewall rules for port 587

### Telnyx Not Working
- Verify API key is correct
- Check phone number is active
- Verify messaging profile is configured

### Stripe Webhooks Not Receiving
- Verify webhook URL is accessible
- Check webhook secret matches
- Review Stripe dashboard for errors

### Office Ally Connection Failed
- Verify SFTP credentials
- Check firewall allows port 22
- Test connection manually: `sftp joshua.wendorf@ftp10.officeally.com`
