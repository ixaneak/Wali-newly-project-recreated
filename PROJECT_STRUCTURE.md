# Wali Project Structure

Clean, organized project structure for the Wali Micro-Insurance Platform.

---

## 📁 Directory Overview

```
wali-backend/
├── .github/                    # GitHub Actions & workflows
├── .venv/                      # Python virtual environment
├── data/                       # JSON data files & mocks
├── database/                   # Database schemas & migrations
├── docs/                       # Documentation
│   ├── architecture/           # System design docs
│   ├── development/            # Developer guides
│   ├── guides/                 # User guides
│   ├── operations/             # DevOps & deployment
│   ├── security/               # Security & compliance
│   └── whatsapp/               # WhatsApp integration
├── go-services/                # Go microservices
│   └── payment-service/        # Payment orchestration
├── infrastructure/             # Docker Compose & monitoring
│   └── monitoring/             # Prometheus & Grafana configs
├── logs/                       # Application logs
├── python-services/            # Python microservices
│   ├── claims-service/         # Claims processing
│   └── policy-service/         # Policy management
├── scripts/                    # Automation scripts
├── security-audit/             # Security audit tools
├── shared/                     # Shared schemas & protos
├── tests/                      # Test suites
│   ├── e2e/                    # End-to-end tests
│   └── load/                   # Load testing (k6)
├── typescript-apps/            # Frontend applications
│   └── pwa/                    # Progressive Web App
└── wali-pwa/                   # PWA distribution
```

---

## 📄 Key Files

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Project overview & quick start |
| `.env.example` | Environment variable template |
| `.gitignore` | Git ignore patterns |
| `k6.exe` | Load testing binary |
| `query` | Query utility |

### Configuration

| Location | Purpose |
|----------|---------|
| `.github/workflows/` | CI/CD pipelines |
| `infrastructure/docker-compose.*.yml` | Docker orchestration |
| `infrastructure/monitoring/` | Prometheus & Grafana |

---

## 📚 Documentation Structure

```
docs/
├── README.md                           # Documentation index
├── architecture/                       # System design
│   ├── database-pooling-guide.md
│   ├── production-scaling.md
│   ├── tech-stack.md
│   └── unified-financial-analytics.md
├── development/                        # Developer guides
│   └── CODE_QUALITY_IMPROVEMENTS.md
├── guides/                            # User guides
│   ├── login-enhancements.md
│   ├── quickstart.md
│   ├── testing.md
│   └── verification-checklist.md
├── operations/                        # DevOps
│   ├── cima-compliance-checklist.md
│   ├── cima-production-checklist.md
│   └── INFRASTRUCTURE_TESTING_IMPROVEMENTS.md
├── security/                          # Security
│   ├── audit-complete.md
│   ├── cima-security-checklist.md
│   ├── final-compliance-report.md
│   ├── owasp-remediation-guide.md
│   └── PRODUCTION_SECURITY_FIXES.md
└── whatsapp/                          # WhatsApp
    ├── ivory-coast-business-logic.md
    ├── otp-setup.md
    ├── otp-summary.md
    ├── redis-config.md
    └── service-readme.md
```

---

## 🧪 Test Structure

```
tests/
├── e2e/                              # End-to-end tests
│   ├── verify_e2e_flow.py
│   ├── verify_claims_flow.py
│   └── ... (18 test files)
├── load/                             # Load testing
│   ├── configs/
│   ├── grafana/
│   ├── scenarios/
│   └── shared/
└── run_tests.sh                      # Test runner
```

---

## 🔧 Scripts

```
scripts/
├── README.md                         # Scripts documentation
├── deploy-production.sh              # Production deployment
├── migrate-to-cdg.sh                 # Database migration
├── run_tests.sh                      # Test runner
├── start-backend-mock.ps1            # Start mock backend
├── start-mobile-test.ps1             # Start mobile testing
├── start-pwa.ps1                     # Start PWA dev server
├── check_compliance.ps1              # Compliance check
├── test_rate_limit.ps1               # Rate limit testing
├── verify-payment-flow.ps1           # Payment verification
└── verify_compliance.py              # Compliance verification
```

---

## 📊 Data & Logs

### Data (`data/`)
- Mock JSON data for testing
- API specifications
- E2E test state

### Logs (`logs/`)
- Application logs
- Debug dumps
- Compliance reports
- **Note:** Secrets files are encrypted

---

## 🔒 Security

```
security-audit/
├── configs/                          # Security configurations
│   ├── secure_auth.py
│   ├── security_headers.py
│   └── waf_rules.py
├── scripts/                          # Audit scripts
│   ├── apply_critical_security.sh
│   ├── dependency_audit.sh
│   ├── secrets_audit.sh
│   └── penetration_test.py
├── siem_integration.py
└── vendor_assessments.py
```

---

## 🚀 Quick Navigation

| What | Where |
|------|-------|
| Getting Started | `docs/guides/quickstart.md` |
| API Documentation | `data/claims_openapi.json` |
| Security Fixes | `docs/security/PRODUCTION_SECURITY_FIXES.md` |
| Deployment | `scripts/deploy-production.sh` |
| Testing | `tests/run_tests.sh` |
| Monitoring | `infrastructure/monitoring/` |

---

**Last Updated:** 2026-02-21
