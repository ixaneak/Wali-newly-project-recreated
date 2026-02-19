# CIMA Production Readiness Checklist

## Objective
Verify WALI micro-insurance platform handles 10,000 concurrent users and 100 transactions/minute before CIMA audit.

---

## Phase 1: Pre-Test Setup (Do Not Skip)

### [ ] Database Backup
```bash
fly pg backup create --app wali-db-prod
fly pg backup list --app wali-db-prod
```

### [ ] Scale Infrastructure
```bash
# Pre-scale before load test
fly scale count 4 --app wali-policy-service
fly scale count 4 --app wali-claims-service
fly scale count 2 --app wali-ai-concierge
fly scale count 2 --app wali-payment-gateway

# Verify
fly status --app wali-policy-service
```

### [ ] Enable Redis Caching
```bash
# Verify Redis is attached
echo $REDIS_URL

# Check connection
fly redis connect wali-redis
> PING
```

### [ ] Start Celery Workers
```bash
# Policy service
fly ssh console --app wali-policy-service
> celery -A infrastructure.celery.celery_app worker -Q sar,default -l info

# Run multiple workers for high load
fly scale count 3 --app wali-celery-worker
```

### [ ] Monitoring Dashboard
- [ ] Open Fly.io dashboard: https://fly.io/apps/wali-policy-service/metrics
- [ ] Open logs: `fly logs --app wali-policy-service`
- [ ] Set up alerts (error rate >1%, response time >1s)

---

## Phase 2: Load Test Execution

### [ ] Dry Run (Single User)
```bash
k6 run --vus 1 --iterations 1 load-tests/wali-load-test.js
```
**Expected:** All checks pass, no errors

### [ ] Baseline Test (100 VUs)
```bash
k6 run --vus 100 --duration 5m load-tests/wali-load-test.js
```
**Expected:**
- p95 latency <500ms
- Error rate <0.1%
- All services healthy

### [ ] Peak Load Test (400 VUs)
```bash
k6 run --vus 400 --duration 10m load-tests/wali-load-test.js
```
**Expected:**
- Auto-scaling triggers (machines increase)
- p95 latency <800ms
- Error rate <1%
- DB connections <80%

### [ ] Stress Test (1000 VUs)
```bash
k6 run --vus 1000 --duration 5m load-tests/wali-load-test.js
```
**Expected:**
- System remains stable
- No data loss
- Recovery within 2 minutes after load ends

### [ ] SAR Detection Validation
During load test, verify:
```bash
# Check SAR reports are created
fly ssh console --app wali-policy-service
> psql $DATABASE_URL -c "SELECT COUNT(*) FROM sar_reports WHERE created_at > NOW() - INTERVAL '1 hour';"

# Check risk events
> psql $DATABASE_URL -c "SELECT event_type, COUNT(*) FROM risk_events GROUP BY event_type;"
```

---

## Phase 3: Real-Time Monitoring

### [ ] Watch Database Connections
```bash
fly ssh console --app wali-db-prod
> psql -c "SELECT count(*) FROM pg_stat_activity;"
> psql -c "SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;"
```
**Alert if:** Active connections > 80

### [ ] Monitor Error Logs
```bash
# In separate terminal
fly logs --app wali-policy-service | grep ERROR
fly logs --app wali-claims-service | grep ERROR
```

### [ ] Check Resource Usage
- [ ] CPU usage < 90% per machine
- [ ] Memory usage < 80% per machine
- [ ] Disk I/O normal (no spikes)

---

## Phase 4: Post-Test Analysis

### [ ] k6 Results Review
Check output for:
- `checks`: Should be >99% passing
- `http_req_duration`: p95 should be <500ms
- `http_req_failed`: Should be <1%
- `iterations`: Completed successfully

### [ ] Database Integrity
```bash
# Verify no data corruption
psql $DATABASE_URL -c "SELECT COUNT(*) FROM coverage_subscriptions;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM incident_reports;"

# Verify SAR reports created during test
psql $DATABASE_URL -c "SELECT * FROM sar_reports ORDER BY created_at DESC LIMIT 5;"
```

### [ ] Performance Report
Generate summary:
```bash
k6 run --out json=results.json load-tests/wali-load-test.js
# Analyze results.json for bottlenecks
```

---

## Phase 5: Scaling Decision Matrix

| Metric | Target | Current | Action |
|--------|--------|---------|--------|
| QR Generation p95 | <200ms | ? | Add Redis if >300ms |
| Pharmacy Verify p95 | <500ms | ? | Optimize query if >600ms |
| AI Response p95 | <3s | ? | Scale AI service if >4s |
| Error Rate | <0.1% | ? | Fix bugs if >0.5% |
| DB Connections | <80% | ? | Increase pool or add replica |
| Memory Usage | <80% | ? | Scale VM size if >90% |

---

## Phase 6: Production Configuration

### [ ] Final fly.toml Updates
```toml
[[vm]]
  size = "performance-4x"  # 4 CPU, 8GB RAM
  memory = "8gb"

[http_service]
  min_machines_running = 4
  max_machines_running = 20
```

### [ ] Database Pool Configuration
Verify environment variables:
```bash
fly secrets list --app wali-policy-service
# Should include: SERVICE_NAME=policy-service
```

### [ ] Celery Production Workers
```bash
# Start with 3 workers per queue
fly deploy --dockerfile Dockerfile.celery
```

---

## Phase 7: CIMA Audit Preparation

### [ ] Compliance Documentation
- [ ] SAR detection logs (last 90 days)
- [ ] Risk event audit trail
- [ ] TRACFIN export capability demonstrated
- [ ] Data retention policy (5 years) configured

### [ ] Security Checklist
- [ ] All services use HTTPS
- [ ] Database connections use SSL
- [ ] API keys rotated
- [ ] No sensitive data in logs

### [ ] Business Continuity
- [ ] Database backups automated
- [ ] Failover tested (kill a machine, verify recovery)
- [ ] Recovery Time Objective (RTO) < 15 minutes
- [ ] Recovery Point Objective (RPO) < 5 minutes

---

## Final Verification

Run complete test:
```bash
# Full production simulation
k6 run --vus 1000 --duration 30m load-tests/wali-load-test.js

# Verify all systems operational afterward
fly status --app wali-policy-service
fly status --app wali-claims-service
```

**Sign-off:** _________________ Date: ___________
**CIMA Auditor:** _________________ Date: ___________
