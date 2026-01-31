# 🚀 Deployment Checklist - FusionEMS Quantum Platform

**Date:** January 30, 2026  
**Status:** All 77+ bugs fixed, ready for deployment

---

## ✅ Pre-Deployment Verification

### Code Quality
- [x] All Python files compile without syntax errors
- [x] All TypeScript files type-check correctly
- [x] No `os.getenv()` calls in backend services
- [x] XSS vulnerabilities patched with sanitization
- [x] Array index keys replaced with stable IDs
- [x] Error boundaries implemented
- [x] Memory leaks fixed

### Security
- [x] JWT secrets enforced (32+ chars required)
- [x] Security headers middleware active
- [x] CORS properly restricted
- [x] Rate limiting distributed (Redis)
- [x] WebSocket authentication raises exceptions
- [x] Health endpoints require authentication
- [x] Request size limits (100MB)

### Database
- [x] N+1 queries optimized
- [x] Migration created for cascade deletes
- [x] Session management fixed
- [x] Transaction rollback handling

### PWAs
- [x] Service workers registered
- [x] Offline queue implemented
- [x] LocalStorage error handling
- [x] Socket token refresh fixed

---

## 📋 Deployment Steps

### 1. Environment Variables

**CRITICAL: Generate strong secrets before deployment!**

```bash
# Generate secrets (run 3 times)
openssl rand -hex 32

# Update production .env file:
```

**Required variables in `backend/.env`:**
```bash
# CRITICAL - Use strong random 64+ character strings
JWT_SECRET_KEY=<paste-64-char-random-string>
STORAGE_ENCRYPTION_KEY=<paste-64-char-random-string>
DOCS_ENCRYPTION_KEY=<paste-64-char-random-string>

# Redis (required for distributed rate limiting)
REDIS_URL=redis://your-redis-host:6379/0

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# CORS origins (production URLs)
ALLOWED_ORIGINS=https://app.fusionemsquantum.com,https://api.fusionemsquantum.com

# Email (Mailu)
SMTP_HOST=mail.fusionemsquantum.com
SMTP_PORT=587
SMTP_USERNAME=your-email@fusionemsquantum.com
SMTP_PASSWORD=<secure-password>
IMAP_HOST=mail.fusionemsquantum.com
IMAP_USERNAME=your-email@fusionemsquantum.com
IMAP_PASSWORD=<secure-password>

# Stripe
STRIPE_SECRET_KEY=<stripe-secret>
STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret>
STRIPE_PUBLISHABLE_KEY=<stripe-public-key>

# Optional services
JITSI_APP_SECRET=<jitsi-secret>
MAPBOX_ACCESS_TOKEN=<mapbox-token>
CAD_BACKEND_AUTH_TOKEN=<secure-random-token>
```

### 2. Database Migration

```bash
cd backend

# Backup database first!
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
alembic upgrade head

# Verify migration
alembic current
```

### 3. Install Dependencies

```bash
# Backend (if needed)
cd backend
pip install -r requirements.txt

# Frontend
cd ..
npm install

# PWAs
cd mdt-pwa && npm install && cd ..
cd epcr-pwa && npm install && cd ..
cd fleet-pwa && npm install && cd ..
cd workforce-pwa && npm install && cd ..
cd crewlink-pwa && npm install && cd ..
cd fire-mdt-pwa && npm install && cd ..
```

### 4. Build All Applications

```bash
# Frontend
npm run build

# Each PWA
cd mdt-pwa && npm run build && cd ..
cd epcr-pwa && npm run build && cd ..
cd fleet-pwa && npm run build && cd ..
cd workforce-pwa && npm run build && cd ..
cd crewlink-pwa && npm run build && cd ..
cd fire-mdt-pwa && npm run build && cd ..
```

### 5. Test Redis Connection

```bash
# Verify Redis is accessible
redis-cli -u $REDIS_URL ping
# Should return: PONG

# Test from Python
python3 -c "import redis; r = redis.Redis.from_url('$REDIS_URL'); print('Redis OK' if r.ping() else 'Redis FAIL')"
```

### 6. Restart Services

```bash
# Backend API
sudo systemctl restart fusionems-api
# or
pm2 restart fusionems-api

# Nginx (if config changed)
sudo nginx -t
sudo systemctl reload nginx

# Check logs
tail -f /var/log/fusionems/api.log
```

### 7. Smoke Tests

```bash
# Health check
curl https://api.fusionemsquantum.com/api/system/health

# Test authentication
curl -X POST https://api.fusionemsquantum.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Check security headers
curl -I https://api.fusionemsquantum.com/ | grep -E "X-Frame|X-Content|Strict-Transport"
```

---

## 🔍 Post-Deployment Verification

### Backend Health
- [ ] API responds to health checks
- [ ] Authentication endpoints work
- [ ] Rate limiting active (check Redis)
- [ ] Security headers present
- [ ] Database queries performant
- [ ] No error logs

### Frontend
- [ ] Application loads
- [ ] Login works
- [ ] Error boundaries catch errors
- [ ] No console errors
- [ ] API calls succeed

### PWAs
- [ ] Service workers register
- [ ] Offline mode works
- [ ] Data syncs when back online
- [ ] LocalStorage functions
- [ ] No TypeScript errors

### Security
- [ ] Strong secrets in .env
- [ ] HTTPS enforced
- [ ] CORS restricted
- [ ] Rate limiting works
- [ ] XSS protections active
- [ ] CSRF tokens validated

---

## 🚨 Rollback Plan

If issues occur:

1. **Database Rollback:**
   ```bash
   alembic downgrade -1
   # or restore from backup
   psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
   ```

2. **Code Rollback:**
   ```bash
   git revert HEAD
   git push
   # Redeploy previous version
   ```

3. **Emergency Disable Rate Limiter:**
   - Set `REDIS_URL=` (empty) in .env
   - Rate limiter will disable gracefully

---

## 📊 Monitoring

### Key Metrics to Watch

1. **API Response Times**
   - Should be < 200ms for most endpoints
   - Check for N+1 query regressions

2. **Error Rates**
   - Should be < 0.1%
   - Check logs for new error patterns

3. **Redis Memory**
   - Rate limiter uses minimal memory
   - Monitor for memory leaks

4. **Security Events**
   - Watch for rate limit triggers
   - Monitor authentication failures
   - Check for XSS attempt logs

### Log Locations

```bash
# API logs
/var/log/fusionems/api.log
/var/log/fusionems/api-error.log

# Nginx logs
/var/log/nginx/access.log
/var/log/nginx/error.log

# Redis logs
/var/log/redis/redis-server.log
```

---

## ✅ Sign-Off

- [ ] All environment variables updated
- [ ] Database migration successful
- [ ] All builds completed
- [ ] Redis connection verified
- [ ] Services restarted
- [ ] Smoke tests passed
- [ ] Monitoring configured
- [ ] Team notified

**Deployment Manager:** ________________  
**Date/Time:** ________________  
**Version:** v2.0 (77+ fixes applied)

---

## 📚 Additional Resources

- **PLATFORM_FIXES_SUMMARY.md** - Complete list of all fixes
- **PLATFORM_STATUS_FINAL.md** - Verification results
- **backend/.env.example** - Updated with all new variables

---

**Status: READY FOR PRODUCTION** 🎉
