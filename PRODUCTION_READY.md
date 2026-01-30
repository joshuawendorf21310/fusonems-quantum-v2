# Production-ready checklist (fusionemsquantum.com)

This doc ensures the **root URL** serves the marketing landing page and the stack is real-life ready.

## Port layout (must match)

| Port | Process | Purpose |
|------|---------|---------|
| **3000** | Next.js (this repo) | Marketing landing (`/`) + all app routes. **Root must hit this.** |
| **8000** | FastAPI (backend) | API and auth. Nginx proxies `/api/` and `/auth/` here. |

If nginx sends `fusionemsquantum.com/` to port **8000**, you will get 502 or wrong content (backend does not serve the marketing page). Fix: point `/` to **3000** only.

## Nginx for main domain

1. Use the canonical config: **`infrastructure/nginx/fusionemsquantum.conf`**
2. Install:
   ```bash
   sudo cp infrastructure/nginx/fusionemsquantum.conf /etc/nginx/sites-available/fusionemsquantum
   sudo ln -sf /etc/nginx/sites-available/fusionemsquantum /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
3. In that config:
   - `location /` → `proxy_pass http://127.0.0.1:3000` (Next.js)
   - `location /api/` and `location /auth/` → `proxy_pass http://127.0.0.1:8000` (FastAPI)
   - **No** rewrite of `/` to `/founder`

## Docker Compose (this repo)

- **frontend**: `3000:3000` (Next.js). This is what the main domain must proxy to.
- **backend**: `8000:8000` (FastAPI). Nginx proxies `/api/` and `/auth/` here.

Start:

```bash
docker compose up -d backend frontend
```

Then:

- `http://localhost:3000` → marketing landing
- `http://localhost:8000/docs` → API docs

## 502 at root — checklist

1. **Is Next.js running on 3000?**  
   `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/` should be 200.

2. **Is nginx sending `/` to 3000?**  
   In the server block for `fusionemsquantum.com`, `location /` must have `proxy_pass http://127.0.0.1:3000` (not 8000).

3. **No rewrite to /founder**  
   There must be no `rewrite ^/$ /founder` (or similar). Root stays `/`.

4. **Backend on 8000**  
   `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs` should be 200.

## Environment (production)

- **Backend**: `ALLOWED_ORIGINS` should include `https://fusionemsquantum.com` (and `http://` if you still use it).
- **Frontend**: Build with `NEXT_PUBLIC_API_URL` empty or `https://fusionemsquantum.com` so browser requests go to the same origin; nginx then proxies to the backend.

## Quick verification

After deploy:

1. Open `https://fusionemsquantum.com/` → marketing landing (“The Regulated EMS Operating System”), not founder/admin.
2. Open `https://fusionemsquantum.com/founder` → founder console (optional, for admins).
3. Open `https://fusionemsquantum.com/login` → login page.
4. No 502 on `/` when both frontend (3000) and backend (8000) are up.
