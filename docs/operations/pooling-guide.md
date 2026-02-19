# Database Connection Pooling Guide

## Overview

WALI supports both **client-side pooling** (SQLAlchemy QueuePool) and **server-side pooling** (PgBouncer).

## Quick Decision Tree

```
Are you using PgBouncer or a connection pooler?
├── YES → Use NullPool (auto-detected)
│         No client-side pooling needed
└── NO  → Use QueuePool (default)
          Client-side pooling with configurable size
```

## Configuration

### 1. Client-Side Pooling (Default)

**Use this for:**
- Development environments
- Small to medium production loads (< 1000 concurrent connections)
- When you want full visibility into connection metrics

**Setup:**
```bash
# .env
DATABASE_URL=postgresql://user:pass@db.example.com:5432/wali
SERVICE_NAME=policy-service
```

**Behavior:**
- Automatically uses `QueuePool`
- Pool size: 10 connections
- Max overflow: 20 connections
- Pre-ping: Enabled (validates connections before use)

### 2. Server-Side Pooling (PgBouncer)

**Use this for:**
- High-scale production (> 1000 concurrent connections)
- Microservices with many instances
- Reducing database connection overhead

**Setup:**
```bash
# .env
DATABASE_URL=postgresql://user:pass@pgbouncer.internal:6432/wali
# Port 6432 indicates PgBouncer
SERVICE_NAME=policy-service
```

**Behavior:**
- Automatically detects PgBouncer (port 6432 or 'pgbouncer' in URL)
- Uses `NullPool` (no client-side pooling)
- Relies on PgBouncer for connection management

## PgBouncer Setup

### Installation (Fly.io)

```bash
# Create PgBouncer app
fly apps create wali-pgbouncer

# Deploy PgBouncer
fly deploy --dockerfile Dockerfile.pgbouncer
```

### Configuration (pgbouncer.ini)

```ini
[databases]
wali = host=db.internal port=5432 dbname=wali

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pooling mode
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

# Timeouts
server_idle_timeout = 600
server_lifetime = 3600
client_idle_timeout = 0
client_login_timeout = 60

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
```

### Pooling Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **session** | Connection kept for entire session | Long-running transactions, prepared statements |
| **transaction** | Connection kept per transaction | **Recommended for most apps** |
| **statement** | Connection per statement | Simple, stateless queries only |

## Service-Specific Pool Sizes

| Service | Pool Size | Max Overflow | Total |
|---------|-----------|--------------|-------|
| policy-service | 10 | 20 | 30 |
| claims-service | 10 | 20 | 30 |
| payment-gateway | 8 | 12 | 20 |
| ai-concierge | 5 | 10 | 15 |
| compliance | 3 | 2 | 5 |
| **TOTAL** | | | **100** |

## Monitoring

### Check Pool Status

```python
from wali_core.database import DatabaseManager

db = DatabaseManager(DATABASE_URL, 'policy-service')
status = db.get_pool_status()
print(status)
# {
#     'service': 'policy-service',
#     'pool_type': 'QueuePool (client-side)',
#     'pool_size': 10,
#     'checked_in': 5,
#     'checked_out': 3,
#     'overflow': 0,
#     'total_connections': 8
# }
```

### Health Check Endpoint

```python
@app.get("/health/db")
def db_health():
    from wali_core.database import check_database_health
    return check_database_health(engine)
```

## Troubleshooting

### "Too many connections"

**Cause:** Pool sizes sum to > database max_connections

**Fix:**
```python
# Reduce pool sizes in POOL_CONFIGS
POOL_CONFIGS = {
    'policy-service': {
        'pool_size': 5,        # Reduce from 10
        'max_overflow': 10,    # Reduce from 20
    }
}
```

### "Connection timeout"

**Cause:** All connections in use, waiting too long

**Fix:**
```python
# Increase timeout
POOL_CONFIGS = {
    'policy-service': {
        'pool_timeout': 60,  # Increase from 30
    }
}
```

Or use PgBouncer for better connection handling.

### "SSL connection has been closed unexpectedly"

**Cause:** Connection closed by server/firewall

**Fix:**
```python
# Enable pre-ping (already enabled by default)
POOL_CONFIGS = {
    'policy-service': {
        'pool_pre_ping': True,  # Validates connection before use
        'pool_recycle': 300,    # Recycle connections every 5 min
    }
}
```

## Migration: QueuePool → PgBouncer

1. **Set up PgBouncer** (see above)

2. **Update DATABASE_URL:**
   ```bash
   # Old
   DATABASE_URL=postgresql://user:pass@db.internal:5432/wali
   
   # New
   DATABASE_URL=postgresql://user:pass@pgbouncer.internal:6432/wali
   ```

3. **Deploy application** - Code auto-detects PgBouncer and uses NullPool

4. **Monitor** - Check connection counts:
   ```sql
   -- On PostgreSQL
   SELECT count(*) FROM pg_stat_activity;
   ```

## Performance Comparison

| Metric | QueuePool | PgBouncer |
|--------|-----------|-----------|
| Connection Latency | ~1-5ms | ~0.5-2ms |
| Memory per Connection | ~10MB | ~1-2MB |
| Max Connections | 100 (DB limit) | 10,000+ |
| Setup Complexity | Low | Medium |
| Visibility | High | Medium |

## Recommendations

### Development
```bash
DATABASE_URL=postgresql://localhost:5432/wali
# Uses QueuePool, pool_size=5
```

### Staging
```bash
DATABASE_URL=postgresql://db.staging.internal:5432/wali
# Uses QueuePool, pool_size=10
```

### Production (< 1000 users)
```bash
DATABASE_URL=postgresql://db.production.internal:5432/wali
# Uses QueuePool, pool_size=10
```

### Production (> 1000 users)
```bash
DATABASE_URL=postgresql://pgbouncer.internal:6432/wali
# Uses NullPool, PgBouncer handles pooling
```

## References

- [SQLAlchemy Pooling Documentation](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/)
- [Fly.io Postgres Pooling](https://fly.io/docs/reference/postgres/#connection-pooling)
