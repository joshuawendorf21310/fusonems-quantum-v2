# Getting Access to the FusionEMS Quantum Platform

If you don’t have access to the platform, use one of these options.

## 1. Dev access (development only)

**Requirements:** Backend running with `ENV=development` and `LOCAL_AUTH_ENABLED=true` in `backend/.env`.

1. Set the frontend API URL in `.env`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```
   (Use your actual backend URL; the path must end with `/api` so `/auth/login` and `/auth/dev_seed` hit the API.)

2. Open the app and go to **[/login](/login)**.

3. Click **“Dev access (founder) — no password”**.
   - This creates a founder user `dev@local` (or upgrades an existing dev user to founder) and logs you in.
   - You are redirected to the Founder dashboard.

4. All later API requests send the token from `localStorage` as `Authorization: Bearer <token>`.

## 2. Manual dev seed (curl)

If the “Dev access” button is not available or fails:

```bash
curl -X POST http://localhost:8000/api/auth/dev_seed
```

Then on the login page sign in with:

- **Email:** `dev@local`
- **Password:** `Pass1234`

You will be required to **change your password** on first login. The dev user has **founder** role and can use the Founder dashboard and AI assistant after changing the password.

## 3. Register and get founder/admin role

1. Go to **[/register](/register)** and create an account.
2. An existing admin/founder must set your user role to **founder** or **admin** in the database (e.g. `UPDATE users SET role = 'founder' WHERE email = 'your@email.com';`) so you can access the Founder dashboard.

## Troubleshooting

- **401 Unauthorized:** Ensure `NEXT_PUBLIC_API_URL` points to the backend (e.g. `http://localhost:8000/api`). The frontend sends the token in the `Authorization` header; the backend also accepts the session cookie.
- **403 on dev_seed:** Dev seed is disabled when `ENV=production` or `LOCAL_AUTH_ENABLED=false`. Use development env and enable local auth.
- **404 on /auth/login:** Your `NEXT_PUBLIC_API_URL` must end with `/api` (e.g. `http://localhost:8000/api`) so that requests to `/auth/login` go to `http://localhost:8000/api/auth/login`.
