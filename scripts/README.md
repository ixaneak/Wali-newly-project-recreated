# Wali Scripts

Automation and utility scripts for development, testing, and deployment.

---

## 📁 Script Categories

### 🚀 Deployment

| Script | Description | Usage |
|--------|-------------|-------|
| `deploy-production.sh` | Production deployment with rollback | `./deploy-production.sh v1.0.0` |
| `migrate-to-cdg.sh` | Database migration script | `./migrate-to-cdg.sh` |

### 🧪 Testing & QA

| Script | Description | Usage |
|--------|-------------|-------|
| `run_tests.sh` | Run all test suites | `./run_tests.sh [unit\|integration\|e2e\|all]` |
| `test_rate_limit.ps1` | Test rate limiting | `powershell ./test_rate_limit.ps1` |
| `verify-payment-flow.ps1` | Verify payment integration | `powershell ./verify-payment-flow.ps1` |
| `verify_compliance.py` | Compliance verification | `python verify_compliance.py` |

### 🔧 Development

| Script | Description | Usage |
|--------|-------------|-------|
| `start-backend-mock.ps1` | Start backend in mock mode | `powershell ./start-backend-mock.ps1` |
| `start-pwa.ps1` | Start PWA development server | `powershell ./start-pwa.ps1` |
| `start-mobile-test.ps1` | Start mobile test environment | `powershell ./start-mobile-test.ps1` |
| `check_compliance.ps1` | Check CIMA compliance | `powershell ./check_compliance.ps1` |

---

## 🔒 Security Scripts

Located in `../security-audit/scripts/`:

| Script | Description |
|--------|-------------|
| `dependency_audit.sh` | Scan dependencies for vulnerabilities |
| `secrets_audit.sh` | Scan for hardcoded secrets |
| `container_scan.sh` | Scan Docker images |
| `penetration_test.py` | Automated penetration testing |

---

## 📝 Notes

- PowerShell scripts (`.ps1`) are for Windows environments
- Bash scripts (`.sh`) are for Linux/macOS environments
- Python scripts work cross-platform

---

**See also:**
- [Development Guide](../docs/development/)
- [Operations Guide](../docs/operations/)
