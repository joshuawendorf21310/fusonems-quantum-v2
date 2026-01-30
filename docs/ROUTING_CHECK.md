# Routing Check — FusionEMS Quantum

## Summary

**Routing is correct.** `/portals` is handled by the Next.js App Router and nginx proxies it to the frontend. No rewrites or redirects interfere.

---

## 1. Next.js App Router

| Path | File | Notes |
|------|------|--------|
| `/` | `src/app/page.tsx` | Marketing landing |
| `/portals` | `src/app/portals/page.tsx` | Architecture page (layout: `portals/layout.tsx`) |
| `/portals/patient/login` | `src/app/portals/patient/login/page.tsx` | Patient portal login |
| `/portals/transportlink/login` | `src/app/portals/transportlink/login/page.tsx` | TransportLink login |
| `/portals/carefusion/login` | `src/app/portals/carefusion/login/page.tsx` | FusionCare login |
| `/login` | `src/app/login/page.tsx` | Platform login |
| `/founder` | `src/app/founder/page.tsx` | Founder console |
| `/api/*` | **Not in Next.js** | Proxied by nginx to FastAPI (port 8000) |

- **Portals layout:** `src/app/portals/layout.tsx` wraps all `/portals/*` routes (dark bg, `z-10`).
- **No catch‑all or conflicting routes** for `/portals`.

---

## 2. next.config.ts

- **No `rewrites`** — no internal path rewrites.
- **No `redirects`** — no permanent/temporary redirects.
- No `basePath` or `assetPrefix` that would change path resolution.

So `/portals` is served by `src/app/portals/page.tsx` as expected.

---

## 3. Middleware (`src/middleware.ts`)

- **Matcher:** `["/"]` — runs only for the exact path `/`.
- **Behavior:** `NextResponse.next()` (no rewrite).
- **Effect on /portals:** Middleware does **not** run for `/portals`, so it cannot change or block that route.

---

## 4. Nginx (production)

**Config:** `infrastructure/nginx/fusionemsquantum.conf`

| Location | Proxy to | Effect |
|----------|----------|--------|
| `location /` | `http://127.0.0.1:3000` | All paths not matched below → Next.js (including `/portals`) |
| `location /api/` | `http://127.0.0.1:8000` | API → FastAPI |
| `location /auth/` | `http://127.0.0.1:8000` | Auth → FastAPI |
| `location /socket.io` | `http://127.0.0.1:8000` | WebSocket → FastAPI |
| `location /_next/static/` | `http://127.0.0.1:3000` | Static assets → Next.js |

- **Request flow for `https://www.fusionemsquantum.com/portals`:**
  1. Nginx receives request; path `/portals` matches `location /`.
  2. Request is proxied to `http://127.0.0.1:3000/portals`.
  3. Next.js serves `src/app/portals/page.tsx` (with `portals/layout.tsx`).

So production routing for `/portals` is correct at the nginx level.

---

## 5. Things to verify on the server

If `/portals` still shows the wrong content:

1. **Next.js is on 3000**  
   `curl -sI http://127.0.0.1:3000/portals` → 200 and HTML from Next.

2. **No other server on 3000**  
   Ensure the Docker (or process) serving the app from this repo is bound to 3000 and nginx is not pointing elsewhere.

3. **Cache**  
   Browser hard refresh (Ctrl+Shift+R) and, if used, CDN/cache purge for `/portals`.

4. **Correct build**  
   After `git pull` and `docker compose up -d --build`, the running image should include the latest `portals/page.tsx` and `portals/layout.tsx`. Check that the container was rebuilt (e.g. `docker compose images` / build logs).

---

## 6. Quick test from server

```bash
# On the droplet
curl -s http://127.0.0.1:3000/portals | grep -o 'data-page="portals-architecture"'
# Should print: data-page="portals-architecture"
```

If that appears, the new portals page is being served by the app on 3000; if the browser still shows old content, the issue is caching or traffic not hitting this server.
