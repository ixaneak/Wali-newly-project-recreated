# Wali Backend

Micro-insurance fintech platform for artisans and pharmacies in Côte d'Ivoire.

[![CI/CD](https://github.com/wali/wali-backend/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/wali/wali-backend/actions)
[![Code Coverage](https://codecov.io/gh/wali/wali-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/wali/wali-backend)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE)

---

## 🏗️ Architecture

Microservices-based architecture with tri-provider mobile money integration.

### Services

| Service | Language | Port | Description |
|---------|----------|------|-------------|
| Policy Service | Python/FastAPI | 8000 | Insurance policies & enrollments |
| Claims Service | Python/FastAPI | 8001 | Claims processing & fraud detection |
| Payment Service | Go | 8080 | Mobile money orchestration |
| Notification Service | Node.js | 3001 | SMS/Push notifications |
| Compliance Service | Python | 8002 | Audit trails & CIMA reporting |

### Infrastructure

- **PostgreSQL 15** with PostGIS for geospatial data
- **Redis 7** for caching & sessions
- **RabbitMQ** for async task processing
- **MinIO** for object storage
- **Traefik** reverse proxy with auto SSL

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for PWA development)
- Go 1.21+ (for payment service)

### Development Setup

```bash
# Clone repository
git clone https://github.com/wali/wali-backend.git
cd wali-backend

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start infrastructure
docker-compose -f infrastructure/docker-compose.dev.yml up -d

# Run database migrations
cd python-services/policy-service
alembic upgrade head

# Start services (in separate terminals)
cd python-services/policy-service && uvicorn app.main:app --reload
cd python-services/claims-service && uvicorn app.main:app --reload --port 8001
```

### Production Deployment

```bash
# Deploy with script
./scripts/deploy-production.sh v1.0.0

# Or use Docker Compose
cd infrastructure
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 Documentation

Complete documentation is available in the [`docs/`](docs/) directory:

| Section | Description |
|---------|-------------|
| [Architecture](docs/architecture/) | System design & scaling |
| [Development](docs/development/) | Development guides |
| [Operations](docs/operations/) | DevOps & deployment |
| [Security](docs/security/) | Security & compliance |
| [WhatsApp](docs/whatsapp/) | WhatsApp integration |

---

## 🧪 Testing

```bash
# Run all tests
./tests/run_tests.sh all

# Run specific test suites
./tests/run_tests.sh unit
./tests/run_tests.sh integration
./tests/run_tests.sh security

# Run load tests
k6 run load-tests/wali-load-test-improved.js
```

---

## 🔒 Security

- **100% CIMA Compliant** - Full regulatory compliance
- **OWASP Top 10** - All mitigations implemented
- **MFA for Admins** - TOTP + SMS support
- **AES-256 Encryption** - PII data protection
- **Audit Logging** - Immutable audit trails

See [Security Documentation](docs/security/) for details.

---

## 📊 Monitoring

- **Prometheus** - Metrics collection
- **Grafana** - Dashboards & visualization
- **Health Checks** - `/health` endpoint on all services

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

Proprietary - Wali Fintech Platform © 2026

---

## 📞 Support

- **Email:** support@wali.ci
- **Documentation:** [docs.wali.ci](https://docs.wali.ci)
- **Issues:** [GitHub Issues](https://github.com/wali/wali-backend/issues)

---

**Made with ❤️ in Abidjan, Côte d'Ivoire**
