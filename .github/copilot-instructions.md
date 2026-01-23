# Copilot / AI Agent Instructions for FusonEMS Quantum

This file contains concise, actionable guidance to help an AI coding agent be productive in this repository.

- **Big Picture:** Backend is a FastAPI monolith ([../backend/main.py](../backend/main.py)) exposing many routers under `services/`. Frontend is a React + Vite app in `frontend/` that expects `VITE_API_URL` to point to the backend.

- **Key entrypoints:**
-  - **Backend app:** [backend/main.py](../backend/main.py) (routers are registered here). Use `uvicorn main:app --reload` for local runs or `./start_dev.sh` at repo root to launch both services.
-  - **Configuration:** [backend/core/config.py](../backend/core/config.py) — pydantic settings drive feature toggles (OIDC, Stripe, Telnyx, Postmark, storage backend).
  - **DB models:** `backend/models/` contains SQLAlchemy models used across services.

- **Important architectural patterns to respect:**
  - Each logical feature lives in `backend/services/<feature>` and exposes a FastAPI `router` (imported in `backend/main.py`). Modify routers or add new ones there.
  - Multiple database targets are used: primary `DATABASE_URL`, plus `TELEHEALTH_DATABASE_URL`, `FIRE_DATABASE_URL`, and a `hems` schema. Startup code conditionally creates schemas/tables in `backend/main.py`.
  - Settings are read from a local `.env` when developing. See [.env.template](../.env.template) and copy it into `backend/.env`.

- **Developer workflows / commands:**
  - Local combined dev: `./start_dev.sh` from repo root (launches backend + frontend). See [README.md](../README.md).
  - Backend only: `cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload --host 127.0.0.1 --port 8000`
  - Frontend only: `cd frontend && npm install && npm run dev` (set `VITE_API_URL` in `frontend/.env` if needed).
  - Tests: backend tests run with `pytest` from `backend/`; frontend tests use `npm run test` in `frontend/`.

- **Conventions and project-specific patterns:**
  - Router naming: each router variable is `router` inside a service module (e.g., `services/auth/auth_router.py`) and is directly included in `main.py`.
  - Middleware: server/device time and CSRF enforcement are implemented as HTTP middlewares in `backend/main.py` — respect CSRF cookie/header pairing for browser flows.
  - Feature flags and integrations are toggled via environment variables in `backend/core/config.py` (e.g., `POSTMARK_REQUIRE_SIGNATURE`, `TELNYX_REQUIRE_SIGNATURE`, `OIDC_ENABLED`). Don't hard-code secrets.
  - Storage: `DOCS_STORAGE_BACKEND` supports `local` or `s3`; check `core/config.py` and services that call document storage.

- **Integration points / external deps to be careful with:**
  - Payment: Stripe keys and webhook secrets (see config fields `STRIPE_*`). Tests and local dev often run with `STRIPE_ENV=test`.
  - Messaging/email: Telnyx and Postmark integrations — signature verification is optional but enabled via env toggles.
  - Third-party DBs: Telehealth and Fire use separate DB URLs. Code may assume separate engines exist in `backend/core/database.py`.

- **Where to change behaviour safely:**
  - Add or change API endpoints under `backend/services/<feature>` and expose them by importing and including their `router` in `backend/main.py`.
  - Change deployment-sensitive configuration in `backend/core/config.py` via env variables; production runtime validates required secrets.

- **Files to inspect for examples or patterns:**
  - Router registration: [backend/main.py](../backend/main.py)
  - Settings & runtime validation: [backend/core/config.py](../backend/core/config.py)
  - README contains local run instructions: [README.md](../README.md)

- **Do not assume:**
  - That a single DB is used — there are multiple DB engines and schema creation logic at startup.
  - That OIDC, Stripe, Telnyx, Postmark, or S3 are enabled by default — check env toggles.

- If anything above is unclear or you want a different level of detail (examples for adding a new router, tests to run, or a sample `.env` with safe defaults), tell me which section to expand.
