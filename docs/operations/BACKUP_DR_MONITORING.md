# Backup, Disaster Recovery & Production Monitoring

**FusionEMS Quantum — Operations**  
**Last updated:** January 30, 2026

---

## 1. Backup

### Database (PostgreSQL)

- **Scope:** Primary app DB; optionally separate DBs (Fire, HEMS, Telehealth) if used.
- **Frequency:** At least **daily**; consider continuous archiving (WAL) for point-in-time recovery.
- **Retention:** Minimum 30 days on-site; 90+ days for compliance (align with retention policy).
- **Storage:** Off-app-server (e.g. S3/Spaces, separate region).

**Example (daily cron):**

```bash
# Daily 02:00 — set DATABASE_URL in env
0 2 * * * pg_dump -Fc "$DATABASE_URL" > /backups/fusonems_$(date +\%Y\%m\%d).dump
# Optional: upload to S3/Spaces
# aws s3 cp /backups/fusonems_$(date +\%Y\%m\%d).dump s3://your-backup-bucket/
```

### Application / config

- **Code:** Git (e.g. `main` + tagged releases).
- **Secrets:** Never in repo; use env files or secrets manager (e.g. Doppler, DO App Platform env).
- **Config:** Document required env vars in `backend/.env.example` and deployment docs.

### Object storage (DigitalOcean Spaces)

- Spaces has no built-in backup; use sync to second bucket or backup provider (e.g. s3cmd sync, Veeam, CloudBerry).
- See `docs/storage/OPERATIONAL_RUNBOOK.md` for storage backup commands.

---

## 2. Disaster Recovery (DR)

### Goals (define with business)

- **RTO (Recovery Time Objective):** e.g. 4–24 hours (how soon the system must be back).
- **RPO (Recovery Point Objective):** e.g. 1–24 hours (max acceptable data loss).

### Steps (high level)

1. **Restore DB** from latest backup (or PITR if enabled).
2. **Redeploy app** from Git + correct env (same or new region).
3. **Restore Spaces** from backup if used.
4. **Re-point DNS** if failover to new region.
5. **Smoke-test** critical paths (login, demo request, billing lookup, healthz).
6. **Notify** stakeholders and document incident.

### Runbook

- Keep a one-page **DR runbook** (who does what, order of steps, contacts).
- **Test annually:** Restore from backup to a staging environment and verify.

---

## 3. Production Monitoring

### Health checks

- **Backend:** `GET /healthz` → 200, body `{"status":"online"}`.
- **Optional:** `GET /api/health/telnyx` (Telnyx config/balance).
- **Frontend:** Root or a dedicated `/api/health` that returns 200.

Use these for:

- Load balancer / platform health checks (e.g. DigitalOcean, Kubernetes).
- Uptime monitoring (e.g. UptimeRobot, Pingdom).

### Recommended additions

| Layer | Tool / approach | Purpose |
|-------|------------------|--------|
| **Errors** | Sentry (or similar) | Capture frontend + backend exceptions, alerts. |
| **APM** | DataDog, New Relic, or OpenTelemetry | Latency, throughput, DB and external calls. |
| **Uptime** | UptimeRobot, Pingdom | Alert when /healthz or frontend is down. |
| **On-call** | PagerDuty (or similar) | Route alerts to on-call; escalation. |
| **Logs** | Centralized logging (e.g. DO Spaces, Logtail, Datadog) | Query and retain app logs. |

### Alerts (examples)

- `/healthz` down for >2 minutes.
- Error rate > 5% over 5 minutes.
- DB connection pool exhausted or replication lag.
- Disk or memory above 80% on app/DB servers.

---

## 4. Checklist (real-life readiness)

- [ ] **Backup:** Daily DB backups to off-server storage; test restore once.
- [ ] **DR:** RTO/RPO defined; one-page DR runbook; annual DR test.
- [ ] **Monitoring:** Health checks wired to LB/platform; uptime monitor on /healthz (and frontend).
- [ ] **Errors:** Sentry (or equivalent) for backend + frontend.
- [ ] **On-call:** PagerDuty or equivalent; escalation path documented.

---

*See also: FORENSIC_SYSTEM_AUDIT.md, docs/storage/OPERATIONAL_RUNBOOK.md, DEPLOYMENT_GUIDE.md.*
