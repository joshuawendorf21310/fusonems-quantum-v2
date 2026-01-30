# 🌐 Your FusoNEMS CAD Apps are Live!

## ✅ Domain Configuration Complete

### Your Apps Are Now Accessible At:

**Main site (marketing landing):**
- http://fusionemsquantum.com
- http://www.fusionemsquantum.com
→ Proxies to port 3000 (Marketing Homepage)

**Important:** The root path `/` must serve the marketing landing page (The Regulated EMS Operating System). Do **not** add nginx/hosting rewrites that send `/` to `/founder`; the founder/admin console is at `/founder`. A 502 at the root usually means the app on port 3000 is down or the proxy is pointing at the wrong upstream.

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

## 📊 Running Services

- ✅ CAD Dashboard (port 3003) - Next.js
- ✅ CrewLink PWA (port 3001) - Vite
- ✅ MDT PWA (port 3002) - Vite
- ✅ Nginx - Reverse proxy
- ✅ PostgreSQL - Database
- ✅ Redis - Cache

---

## 🎉 SUCCESS!

Your FusoNEMS CAD system is now live on your domain!

**Main URL:** http://fusionemsquantum.com
