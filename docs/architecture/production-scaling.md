# WALI Production Scaling & SRE Infrastructure

## Overview
Complete Site Reliability Engineering (SRE) setup for CIMA audit and 10,000 concurrent user capacity.

---

## 📁 Created Files

### Load Testing
| File | Purpose |
|------|---------|
| `load-tests/wali-load-test.js` | k6 load test script (100-1000 VUs) |
| `load-tests/CIMA_PRODUCTION_CHECKLIST.md` | Pre/during/post test checklist |

### Database Optimization
| File | Purpose |
|------|---------|
| `python-services/shared/wali_core/database.py` | Connection pooling with 100-connection budget |

### Async Processing
| File | Purpose |
|------|---------|
| `infrastructure/celery/celery_app.py` | Celery configuration with Redis broker |
| `infrastructure/celery/tasks/sar_tasks.py` | Background SAR detection tasks |
| `infrastructure/celery/tasks/notification_tasks.py` | Email/SMS async tasks |

### Infrastructure Config
| File | Purpose |
|------|---------|
| `infrastructure/fly-policy-service.toml` | Fly.io auto-scaling (2-20 machines) |
| `infrastructure/redis/redis-config.md` | Redis setup instructions |

---

## 🎯 Capacity Targets

| Metric | Target | Configuration |
|--------|--------|---------------|
| Concurrent Users | 10,000 | Auto-scale to 20 machines |
| Transactions/min | 100 | Connection pooling + Redis |
| Response Time (p95) | <500ms | Performance-2x VMs |
| Uptime | 99.9% | Multi-machine + health checks |

---

## 🚀 Quick Start

### 1. Install k6
```bash
brew install k6  # macOS
# or
sudo apt-get install k6  # Linux
```

### 2. Run Load Test
```bash
# Dry run
k6 run --vus 1 --iterations 1 load-tests/wali-load-test.js

# Full production test
k6 run load-tests/wali-load-test.js
```

### 3. Monitor in Real-Time
```bash
# Terminal 1: Watch logs
fly logs --app wali-policy-service

# Terminal 2: Check DB connections
fly ssh console --app wali-db-prod -C "psql -c 'SELECT count(*) FROM pg_stat_activity;'"
```

---

## 📊 Connection Pool Budget (100 Total)

| Service | Pool Size | Max Overflow | Total |
|---------|-----------|--------------|-------|
| policy-service | 10 | 20 | 30 |
| claims-service | 10 | 20 | 30 |
| payment-gateway | 8 | 12 | 20 |
| ai-concierge | 5 | 10 | 15 |
| compliance | 3 | 2 | 5 |
| **TOTAL** | | | **100** |

---

## 🔄 Auto-Scaling Configuration

```toml
[http_service]
  min_machines_running = 2      # Always on for redundancy
  max_machines_running = 20     # Scale up under load
  
  [http_service.concurrency]
    soft_limit = 100            # Scale up at 100 connections
    hard_limit = 250            # Max per machine
```

**Scaling Triggers:**
- 100 concurrent connections → Start new machine
- CPU > 80% → Add machines
- Memory > 80% → Add machines
- Error rate > 1% → Alert (don't auto-scale)

---

## 🧪 Test Scenarios

The k6 script tests:

1. **Health Check** - API availability
2. **QR Generation** - Insurance card generation (cached)
3. **Policy Enrollment** - New subscriptions (with SAR detection)
4. **Pharmacy Verification** - QR code scanning at pharmacies
5. **Incident Report** - Claim submission (with SAR detection)
6. **AI Concierge** - Chatbot responses
7. **Payment Webhook** - Orange Money callbacks
8. **Compliance Dashboard** - Admin monitoring

---

## 📈 Monitoring Checkpoints

### During Test
- [ ] p95 latency < 500ms
- [ ] Error rate < 1%
- [ ] DB connections < 80
- [ ] CPU < 90% per machine
- [ ] Memory < 80% per machine

### Post-Test
- [ ] All data persisted correctly
- [ ] SAR reports generated for suspicious activity
- [ ] No memory leaks (1-hour stability test)
- [ ] Auto-scaling recovered properly

---

## 🚨 Alert Thresholds

| Condition | Action |
|-----------|--------|
| Error rate > 1% for 2 min | Page on-call |
| Response time > 1s (p95) | Scale up immediately |
| DB connections > 80% | Alert + investigate |
| Machine CPU > 90% | Add machines |
| Redis memory > 90% | Evict old keys |

---

## 📋 CIMA Audit Readiness

### ✅ Implemented
- [x] Load testing infrastructure (k6)
- [x] Auto-scaling (2-20 machines)
- [x] Connection pooling (100 budget)
- [x] Redis caching layer
- [x] Async task processing (Celery)
- [x] Database health monitoring
- [x] 5-year data retention (SAR reports)
- [x] TRACFIN export capability

### 📝 To Complete Before Audit
- [ ] Run full 30-minute load test
- [ ] Document RTO/RPO tests
- [ ] Verify backup recovery
- [ ] Security penetration test
- [ ] CIMA compliance documentation

---

## 🛠 Troubleshooting

### "Too many clients already" (DB)
```bash
# Check pool usage per service
fly ssh console --app wali-policy-service
> python -c "from app.core.database import engine; print(engine.pool.status())"
```
**Fix:** Reduce pool_size in `database.py`

### High Response Times
```bash
# Check if Redis caching is working
fly redis connect wali-redis
> INFO stats
```
**Fix:** Verify REDIS_URL env var

### Memory Leaks
```bash
# Monitor over 1 hour
fly metrics --app wali-policy-service
```
**Fix:** Restart workers after 1000 tasks (`worker_max_tasks_per_child`)

---

## 🔗 Useful Commands

```bash
# Scale up manually for big event
fly scale count 10 --app wali-policy-service

# Check all services
fly status --app wali-policy-service
fly status --app wali-claims-service
fly status --app wali-payment-gateway

# Database backup
fly pg backup create --app wali-db-prod

# Redis monitoring
fly redis connect wali-redis
> MONITOR

# Celery queue status
celery -A infrastructure.celery.celery_app inspect active
celery -A infrastructure.celery.celery_app inspect scheduled
```

---

**Last Updated:** 2026-02-18  
**Version:** 1.0  
**Owner:** SRE Team
