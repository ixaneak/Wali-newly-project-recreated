# Redis Setup for WALI

Redis is used for:
- Celery task queue broker
- QR code caching
- Session storage
- Rate limiting

## Fly.io Redis Creation

```bash
# Create Redis in Johannesburg (closest to Ivory Coast)
fly redis create --name wali-redis --region jnb

# Choose plan:
# - Development: Free tier, 1GB storage
# - Production: Paid tier, HA, persistence

# Get Redis URL
fly redis status wali-redis

# Attach to services
fly redis attach wali-redis --app wali-policy-service
fly redis attach wali-redis --app wali-claims-service
fly redis attach wali-redis --app wali-payment-gateway
fly redis attach wali-redis --app wali-ai-concierge
```

## Local Development

```bash
# Using Docker
docker run -d --name wali-redis -p 6379:6379 redis:7-alpine

# Set environment variable
export REDIS_URL=redis://localhost:6379/0
```

## Environment Variables

Add to each service's `.env`:

```bash
# Required for Celery
REDIS_URL=redis://default:password@wali-redis.upstash.io:6379

# Optional: Separate URLs for different purposes
REDIS_CACHE_URL=redis://default:password@wali-redis.upstash.io:6379/1
REDIS_CELERY_URL=redis://default:password@wali-redis.upstash.io:6379/2
```

## Monitoring

```bash
# Connect to Redis CLI
fly redis connect wali-redis

# Check queue lengths
LLEN celery
LLEN sar
LLEN notifications

# Monitor in real-time
MONITOR
```

## Backup & Persistence

Fly.io Redis (Upstash) provides:
- Automatic daily backups
- Point-in-time recovery
- Cross-region replication (for paid plans)

## Troubleshooting

### High Memory Usage
```bash
# Check memory usage
INFO memory

# Evict old keys if needed
redis-cli --eviction-policy allkeys-lru
```

### Connection Issues
```bash
# Test connection
redis-cli -u $REDIS_URL PING

# Check connection pool settings in your app
# Ensure max_connections < Redis plan limit
```
