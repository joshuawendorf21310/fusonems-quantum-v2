# Deploy Live (fusionemsquantum.com)

Get the app live at **https://fusionemsquantum.com** (and **https://api.fusionemsquantum.com** if you use that subdomain).

---

## Option A: Deploy on your Droplet (recommended)

Your nginx already proxies **fusionemsquantum.com** → Next.js (port 3000) and **/api/** → FastAPI (port 8000). Deploy by running the deploy script **on the server**.

### 1. Push your code

```bash
git add -A && git commit -m "Deploy" && git push origin main
```

### 2. SSH into the droplet

```bash
ssh root@157.245.6.217
# or: ssh root@fusionemsquantum.com
```

### 3. Run the live deploy script

From the repo directory on the server:

```bash
cd /root/fusonems-quantum-v2   # or wherever the repo is cloned
chmod +x scripts/deploy_live.sh
./scripts/deploy_live.sh
```

This will:

- `git pull` latest
- `docker compose up -d --build` (backend, frontend, db, redis, etc.)
- Wait for backend health
- `sudo nginx -s reload`

**Env (optional):**

- `SKIP_PULL=1` – don’t run `git pull`
- `NO_NGINX=1` – don’t reload nginx
- `REPO_DIR=/path/to/repo` – use a different repo path

### 4. Check live site

- **Site:** https://fusionemsquantum.com  
- **API health:** https://fusionemsquantum.com/api/health (or https://api.fusionemsquantum.com/health if you proxy that)

---

## Option B: DigitalOcean App Platform

If you use App Platform instead of a droplet:

1. In DO: create/update the app from **infrastructure/do-app.yaml** (repo root = frontend, `backend/` = backend). Set **github.repo** to your real repo (e.g. `your-org/fusonems-quantum-v2`).
2. Add secrets in the DO dashboard (DATABASE_URL, JWT_SECRET_KEY, etc.).
3. To trigger a deploy from your machine:

   ```bash
   export DO_API_TOKEN=your_personal_access_token
   export DO_APP_ID=your_app_platform_app_id
   ./scripts/deploy.sh digitalocean
   ```

   Or push to `main` if the app has **deploy_on_push: true**.

---

## One-liner from your laptop (deploy to droplet)

If you have SSH access and the repo is at `/root/fusonems-quantum-v2` on the server:

```bash
ssh root@157.245.6.217 'cd /root/fusonems-quantum-v2 && git pull && docker compose up -d --build && sudo nginx -s reload'
```

Replace the host and path if yours differ.

---

## Troubleshooting

- **502 Bad Gateway:** Backend or frontend not up. On server: `docker compose ps` and `docker compose logs backend --tail=50`.
- **API 404:** Nginx might be proxying `/api/` to the wrong port; ensure `location /api/` points to `http://127.0.0.1:8000`.
- **CORS errors:** Set `ALLOWED_ORIGINS` in backend to include `https://fusionemsquantum.com` (and `https://www.fusionemsquantum.com` if you use it).
