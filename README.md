# Wali Backend - Micro-Insurance Fintech Platform

Complete backend infrastructure for Wali micro-insurance platform targeting artisans and pharmacies in Côte d'Ivoire.

## 🏗️ Architecture

Microservices-based architecture with tri-provider mobile money integration (Orange/MTN/Wave), dual-role authentication, and COSUMAF compliance.

### Services

- **identity-service** (Node.js/TypeScript) - Authentication & User Management
- **payment-service** (Go) - Mobile Money Orchestration (Orange/MTN/Wave)
- **policy-service** (Python/FastAPI) - Insurance Policy Management
- **claims-service** (Python/FastAPI) - Claims Processing & Fraud Detection
- **compliance-service** (Python/FastAPI) - Audit Trails & COSUMAF Reporting
- **notification-service** (Node.js/TypeScript) - SMS/Push Notifications

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for identity/notification services)
- Python 3.11+ (for policy/claims/compliance services)
- Go 1.21+ (for payment service)
- PostgreSQL 15+ with PostGIS
- Redis 7+

### Development Setup

```bash
# Clone and navigate
cd wali-backend

# Start infrastructure
docker-compose -f infrastructure/docker-compose.dev.yml up -d

# Run database migrations
cd services/policy-service
alembic upgrade head

# Start services (in separate terminals)
cd services/identity-service && npm install && npm run dev
cd services/payment-service && go run main.go
cd services/policy-service && uvicorn app.main:app --reload
cd services/claims-service && uvicorn app.main:app --reload --port 8001
cd services/compliance-service && uvicorn app.main:app --reload --port 8002
cd services/notification-service && npm install && npm run dev
```

### Mock Mode Development (Offline)

For development without a live database or external payment APIs, you can run services in Mock Mode.

**Features:**
- In-Memory Database (persisted to JSON files)
- Mock Payment Providers (Orange/MTN/Wave)
- Offline Claims Fraud Detection

**Run End-to-End Verification:**
```bash
# Runs the full user journey: Create Policy -> Pay -> Activate -> Claim
python verify_e2e_flow.py
```

**Run Services Individually:**
```bash
# Policy Service (Mock DB)
export USE_MOCK_DB=True
cd services/policy-service && uvicorn app.main:app --reload

# Claims Service (Mock DB)
export USE_MOCK_DB=True
cd services/claims-service && uvicorn app.main:app --reload --port 8001

# Payment Service (Mock Providers)
export MOCK_PAYMENT_PROVIDERS=true
cd services/payment-service && go run main.go
```

## 📦 Project Structure

```
wali-backend/
├── services/
│   ├── identity-service/      # Auth, OTP, JWT
│   ├── payment-service/        # Orange/MTN/Wave integration
│   ├── policy-service/         # Policy CRUD, premium calculation
│   ├── claims-service/         # Claims submission, EXIF validation
│   ├── compliance-service/     # Immutable audit logs, reporting
│   └── notification-service/   # SMS/Push notifications
├── shared/
│   ├── proto/                  # gRPC protocol definitions
│   └── schemas/                # Database schemas
├── infrastructure/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
└── docs/
    ├── api-documentation.md
    └── data-flow-diagrams.md
```

## 🔒 Security & Compliance

- **Data Localization**: All data stored in Côte d'Ivoire (Loi n°2013-450)
- **COSUMAF Compliance**: Immutable audit trails with SHA-256 chain hashing
- **Tax Exemption**: Segregated escrow accounting (3-year fintech exemption)
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Fraud Detection**: EXIF validation, perceptual hashing, velocity checks

## 💳 Payment Providers

Tri-provider fallback system with intelligent routing:

1. **Orange Money CI** (Primary) - OAuth2, request-to-pay
2. **MTN MoMo** (Secondary) - Collection API v1.0
3. **Wave CI** (Tertiary) - Checkout sessions

## 📊 Database Schema

PostgreSQL 15 with PostGIS extension:

- `users` - Dual-role accounts (artisan/pharmacy/admin)
- `policies` - Insurance policies with JSONB coverage details
- `transactions` - Payment tracking with provider metadata
- `financial_events` - Immutable audit log with compliance hashing
- `pharmacies` - Geospatial data for nearest-pharmacy lookup

## 🧪 Testing

```bash
# Unit tests
cd services/identity-service && npm test
cd services/payment-service && go test ./...
cd services/policy-service && pytest

# Integration tests
cd services/payment-service && go test -tags=integration ./...

# Load testing
artillery run tests/load/payment-flow.yml
```

## 📝 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/wali
REDIS_URL=redis://localhost:6379
JWT_SECRET=<64-byte-random-string>

# Payment providers
ORANGE_CLIENT_ID=
ORANGE_CLIENT_SECRET=
MTN_API_USER=
MTN_API_KEY=
WAVE_API_KEY=
```

## 🚢 Deployment

```bash
# Build images
docker-compose -f infrastructure/docker-compose.prod.yml build

# Deploy with blue-green strategy
docker-compose -f infrastructure/docker-compose.prod.yml up -d

# Run migrations
docker-compose exec policy-service alembic upgrade head
```

## 📄 License

Proprietary - Wali Fintech Platform © 2026
