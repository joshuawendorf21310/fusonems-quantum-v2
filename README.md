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
frontend/
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
cd frontend
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

Set `VITE_API_URL` in `frontend/.env` (or your hosting platform) for API integration.

### Database Connection Pool Tuning

The platform uses PostgreSQL connection pooling for efficient resource management. Key environment variables for pool tuning:

- `DB_POOL_SIZE` - Number of persistent connections (default: 5)
- `DB_MAX_OVERFLOW` - Additional burst connections (default: 10)
- `DB_POOL_TIMEOUT` - Timeout in seconds for getting a connection (default: 30)
- `DB_POOL_RECYCLE` - Recycle connections after N seconds (default: 1800)

For deployment-tier recommendations and detailed tuning guidance, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#database-connection-pooling).

## Tests
### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
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
