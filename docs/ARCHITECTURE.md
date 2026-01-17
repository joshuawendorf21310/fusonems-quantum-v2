# FusonEMS Quantum Platform - Architecture Documentation

## Database Connection Pooling

The FusonEMS Quantum Platform uses SQLAlchemy connection pooling to efficiently manage database connections across multiple concurrent requests. Proper pool configuration is critical for stability, performance, and resource utilization.

### Overview

All database engines in the application (`engine`, `telehealth_engine`, `fire_engine`, `hems_engine`) use a canonical hardened configuration defined in `backend/core/database.py`. This ensures consistent behavior across all database connections.

### Pool Configuration Parameters

The following environment variables control connection pooling behavior:

#### `DB_POOL_SIZE` (default: 5)
- **What it does**: Number of persistent database connections maintained in the pool at all times.
- **Impact**: Higher values allow more concurrent database operations but consume more database resources.
- **Tuning**: Set based on expected concurrent request volume and available database connections.

#### `DB_MAX_OVERFLOW` (default: 10)
- **What it does**: Additional temporary connections that can be created beyond `DB_POOL_SIZE` when the pool is exhausted.
- **Impact**: Provides burst capacity for traffic spikes. These connections are closed when no longer needed.
- **Total max connections**: `DB_POOL_SIZE + DB_MAX_OVERFLOW` per application instance.

#### `DB_POOL_TIMEOUT` (default: 30)
- **What it does**: Maximum seconds to wait for an available connection from the pool before raising a timeout error.
- **Impact**: Prevents requests from hanging indefinitely when the pool is exhausted. Lower values fail faster; higher values are more tolerant of temporary load spikes.
- **Tuning**: 30 seconds is reasonable for most workloads. Reduce to 10-15 for aggressive fail-fast behavior.

#### `DB_POOL_RECYCLE` (default: 1800)
- **What it does**: Recycle (close and replace) connections after this many seconds to avoid stale connections.
- **Impact**: Prevents "server closed the connection unexpectedly" errors caused by database-side timeouts or network issues.
- **Tuning**: Should be less than your database's connection timeout. PostgreSQL default is often 10 minutes (600s); 30 minutes (1800s) provides a safe margin.

### Additional Pool Features

#### `pool_pre_ping` (always enabled)
- Before using a connection from the pool, SQLAlchemy issues a lightweight `SELECT 1` query to verify the connection is still alive.
- Automatically recovers from stale connections without user-facing errors.
- Adds minimal overhead (~1ms) and is considered best practice for production deployments.

#### `echo` (conditional)
- Disabled in production (`ENV=production`) for performance.
- Enabled in development to log all SQL statements for debugging.

### Startup Connectivity Test

At application startup, `backend/core/database.py` performs a lightweight `SELECT 1` query to verify database connectivity:

- **Production (`ENV=production`)**: Fails fast with `RuntimeError` if the database is unreachable. This prevents the application from starting in a degraded state.
- **Development**: Logs a warning but allows the application to start with SQLite fallback. This enables local development without requiring a PostgreSQL instance.

### Deployment-Tier Recommendations

The optimal pool configuration depends on your deployment size, traffic volume, and database capacity. Below are recommended starting points:

#### Local Development
```bash
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=3
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```
- Minimal resource usage
- SQLite fallback allowed

#### Small Agency / Pilot (1-2 application instances)
```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```
- Up to 30 connections per instance
- Total max: 60 connections (2 instances × 30)
- Suitable for managed PostgreSQL with 100+ max_connections

#### Regional / Multi-Unit (3-5 application instances)
```bash
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```
- Up to 40 connections per instance
- Total max: 200 connections (5 instances × 40)
- Requires PostgreSQL with 250+ max_connections

#### Large Deployment / High Availability (10+ instances)
```bash
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=20
DB_POOL_RECYCLE=1800
```
- Up to 50 connections per instance
- Total max: 500+ connections (10 instances × 50)
- Requires PostgreSQL with 600+ max_connections or connection pooler (PgBouncer)
- Consider using a dedicated connection pooler to reduce database connection overhead

### Coordinating with PostgreSQL `max_connections`

**CRITICAL**: The total number of connections across all application instances must not exceed your PostgreSQL `max_connections` setting minus reserved connections for maintenance/monitoring.

**Formula**:
```
(DB_POOL_SIZE + DB_MAX_OVERFLOW) × Number_of_Instances < PostgreSQL_max_connections - 10
```

**Example**:
- Managed PostgreSQL with `max_connections=100`
- Reserve 10 for admin/monitoring
- Available for application: 90 connections
- If `DB_POOL_SIZE=10` and `DB_MAX_OVERFLOW=20` (30 total per instance)
- **Max safe instances**: 90 / 30 = 3 instances

**Exceeding `max_connections` will cause connection failures** like:
```
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

### Troubleshooting Connection Pool Issues

#### "QueuePool limit of X overflow Y reached, connection timed out"
- **Cause**: All pool connections are in use and `DB_POOL_TIMEOUT` was exceeded.
- **Solutions**:
  1. Increase `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
  2. Reduce `DB_POOL_TIMEOUT` for faster failure and retry
  3. Optimize slow queries or long-running transactions
  4. Add horizontal scaling (more instances) with connection pooler

```
QueuePool limit of 5 overflow 10 reached, connection timed out, timeout 30
```

#### "server closed the connection unexpectedly"
- **Cause**: Database-side connection timeout exceeded.
- **Solution**: Reduce `DB_POOL_RECYCLE` to be less than database timeout.

```
server closed the connection unexpectedly
This probably means the server terminated abnormally before or while processing the request.
```

#### "FATAL: too many connections"
- **Cause**: Exceeded PostgreSQL `max_connections`.
- **Solutions**:
  1. Reduce `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
  2. Scale down number of application instances
  3. Increase PostgreSQL `max_connections` (requires database restart)
  4. Deploy PgBouncer or another connection pooler

```
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

### Connection Pooler (PgBouncer) Considerations

For large-scale deployments with many application instances, consider using PgBouncer in transaction or statement pooling mode:

- **Benefits**: Drastically reduces PostgreSQL connection overhead, allows hundreds of application instances to share a small pool of database connections.
- **Trade-offs**: Session-level features (prepared statements, temp tables) may not work. Transaction pooling is recommended for most workloads.
- **Configuration**: Point `DATABASE_URL` to PgBouncer instead of PostgreSQL directly.

### References

- [SQLAlchemy Connection Pooling Documentation](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/)

### See Also

- `backend/core/config.py` - Pool parameter definitions
- `backend/core/database.py` - Canonical engine creation with hardened pooling
- `.env.example` - Sample configuration with pool variables
- `infrastructure/do-app.yaml` - Deployment configuration for DigitalOcean
