# 🌐 Your FusoNEMS CAD Apps are Live!

## ✅ Domain Configuration Complete

### Your Apps Are Now Accessible At:

**Main site (marketing landing):**
- http://fusionemsquantum.com
- http://www.fusionemsquantum.com
→ Proxies to **port 3000** (Next.js — this repo). `/api/` and `/auth/` are proxied to **port 8000** (FastAPI).

**Important:** The root path `/` must serve the marketing landing page (The Regulated EMS Operating System). Do **not** add nginx/hosting rewrites that send `/` to `/founder`; the founder/admin console is at `/founder`. Use `infrastructure/nginx/fusionemsquantum.conf` as the production nginx config for the main domain. A 502 at the root usually means the Next.js app on port 3000 is down or the proxy is pointing at the wrong upstream (e.g. 8000 instead of 3000).

**CAD Dashboard (Admin):**
- http://cad.fusionemsquantum.com
→ Proxies to port 3003 (CAD Next.js)

**CrewLink PWA:**
- http://crew.fusionemsquantum.com
→ Proxies to port 3001 (Vite)

**MDT PWA:**
- http://mdt.fusionemsquantum.com
→ Proxies to port 3002 (Vite)

**Backend API:**
- http://api.fusionemsquantum.com
→ Proxies to port 8000 (FastAPI)

---

## 🔧 DNS Setup Required

For subdomains to work, add these DNS records in your domain registrar:

**A Records:**
```
fusionemsquantum.com        → 157.245.6.217
www.fusionemsquantum.com    → 157.245.6.217
crew.fusionemsquantum.com   → 157.245.6.217
mdt.fusionemsquantum.com    → 157.245.6.217
api.fusionemsquantum.com    → 157.245.6.217
```

Or use a **wildcard:**
```
*.fusionemsquantum.com → 157.245.6.217
```

---

## 📱 Test Your Apps

1. **Main Dashboard:** http://fusionemsquantum.com
2. **CrewLink:** http://crew.fusionemsquantum.com
3. **MDT:** http://mdt.fusionemsquantum.com

---

## 🔒 Add HTTPS (Optional)

Install SSL with Let's Encrypt:

```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d fusionemsquantum.com -d www.fusionemsquantum.com -d crew.fusionemsquantum.com -d mdt.fusionemsquantum.com -d api.fusionemsquantum.com
```

---

## 📊 Running Services (port matrix)

| Port | Service | Used by |
|------|---------|---------|
| **3000** | Next.js (this repo) — marketing + app | fusionemsquantum.com (root, pages, static) |
| **8000** | FastAPI backend | /api/, /auth/, api.fusionemsquantum.com |
| 3001 | CrewLink PWA (Vite) | crew.fusionemsquantum.com |
| 3002 | MDT PWA (Vite) | mdt.fusionemsquantum.com |
| 3003 | CAD Dashboard | cad.fusionemsquantum.com |
| Nginx | Reverse proxy | Use `infrastructure/nginx/fusionemsquantum.conf` for main domain |
| PostgreSQL, Redis | Database / cache | Backend |

---

## 🎉 SUCCESS!

Your FusoNEMS CAD system is now live on your domain!

**Main URL:** http://fusionemsquantum.com
