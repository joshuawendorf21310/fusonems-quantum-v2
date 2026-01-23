# FusonEMS Quantum Platform

FusonEMS Quantum Platform is a unified EMS operations suite spanning CAD dispatch, ePCR clinical documentation, scheduling, billing, communications, AI analytics, and executive dashboards. This repo contains a FastAPI backend with PostgreSQL + SQLAlchemy, and a React + Vite frontend with a dark charcoal/orange theme.

## Highlights
- CAD dispatch with call intake, unit assignment, ETA calculation, and WebSocket tracking.
- ePCR module with vitals, interventions, medications, and audit-ready records.
- Scheduling and staffing alerts.
- Billing and business operations with Office Ally FTP integration.
- Telnyx mail/SMS/fax notifications.
- AI console with predictions and optimization insights.
- Founder and investor dashboards.

## Project Structure
```
backend/
  core/            # config, database, security
  models/          # SQLAlchemy models
  services/        # API routers by module
  tests/           # pytest tests
next-fusionems/
  src/
    components/
    context/
    pages/
    services/
    data/
  public/
  index.html
infrastructure/
  do-app.yaml
.vscode/
  tasks.json
.env.template
start_dev.sh
```

## Local Development
### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd next-fusionems
npm install
npm run dev
```

### Combined launcher
```bash
./start_dev.sh
```

## Environment
Copy `.env.template` and populate the values.

```bash
cp .env.template backend/.env
```

Set `VITE_API_URL` in `next-fusionems/.env` (or your hosting platform) for API integration.

## Tests
### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd next-fusionems
npm run test
```

## Deployment (DigitalOcean App Platform)
- Backend: Python build, FastAPI, port 8080, auto-deploy from `main`.
- Frontend: Node build, Vite, port 8080, auto-deploy from `main`.
- Database: Managed PostgreSQL with SSL.
- Environment variables: `DATABASE_URL`, `ENV=production`, `PYTHONUNBUFFERED=1`, `VITE_API_URL`.

See `infrastructure/do-app.yaml` for a sample spec.

## VS Code
Use `.vscode/tasks.json` to launch backend and frontend tasks. Recommended extension: `ES7+ React/Redux/React-Native snippets`.
