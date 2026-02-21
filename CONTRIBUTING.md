# Contributing to Wali

Thank you for contributing to the Wali Micro-Insurance Platform! This guide ensures all contributions (human or AI) maintain project quality.

---

## 🚀 Quick Start

1. **Read AGENTS.md first** - Critical for AI assistants
2. **Check PROJECT_STRUCTURE.md** - Understand the layout
3. **Follow this guide** - Contribution standards

---

## 📋 Before You Start

### For AI Agents

⚠️ **CRITICAL:** Read `AGENTS.md` before making ANY changes.

Key points:
- Never create files in root directory
- Always check for existing similar files
- Follow existing code patterns
- Use proper subdirectories

### For Human Contributors

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation: `python scripts/validate-project-structure.py`
5. Submit PR

---

## 📁 File Organization

### Where to Put Files

| What | Where | Example |
|------|-------|---------|
| New feature docs | `docs/guides/` | `docs/guides/payment-v2.md` |
| API docs | `docs/architecture/` | `docs/architecture/api-v2.md` |
| Security docs | `docs/security/` | `docs/security/audit-2026.md` |
| Scripts | `scripts/` | `scripts/backup-database.sh` |
| Unit tests | `python-services/<service>/tests/` | `tests/test_payment.py` |
| E2E tests | `tests/e2e/` | `tests/e2e/test_payment_flow.py` |
| Load tests | `tests/load/scenarios/` | `tests/load/scenarios/payment.js` |
| JSON data | `data/` | `data/payment-methods.json` |

### Forbidden in Root

Never create these in project root:
- ❌ `.md` files (except README.md, PROJECT_STRUCTURE.md, AGENTS.md)
- ❌ `.txt` files
- ❌ `.py` scripts
- ❌ `.ps1` scripts
- ❌ `.json` data files
- ❌ Debug or log files

---

## 📝 Documentation Standards

### Creating New Docs

1. **Choose category:**
   ```
   docs/
   ├── architecture/    # System design, APIs
   ├── development/     # Dev guides, coding standards
   ├── guides/          # User how-tos
   ├── operations/      # Deployment, monitoring
   ├── security/        # Security, compliance
   └── whatsapp/        # WhatsApp integration
   ```

2. **File naming:**
   - Use kebab-case: `payment-webhooks.md`
   - Be descriptive: `deployment-guide.md` not `guide.md`

3. **Required header:**
   ```markdown
   # Document Title
   
   **Date:** 2026-02-21  
   **Status:** Draft|Review|Complete
   
   ---
   ```

4. **Update index:** Add to `docs/README.md`

### Documentation Template

```markdown
# Feature Name

**Date:** 2026-02-21  
**Status:** Draft

---

## Overview

Brief description of the feature.

## Prerequisites

- List requirements
- Include versions

## Usage

```bash
# Code examples
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `KEY` | Description | `value` |

## Troubleshooting

Common issues and solutions.

---

**See also:**
- [Related Doc](../other/doc.md)
- [Architecture](../architecture/system.md)
```

---

## 💻 Code Standards

### Python

```python
"""
Module docstring describing purpose.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db

router = APIRouter(prefix="/api/v1/feature", tags=["feature"])
logger = logging.getLogger(__name__)


@router.get("/")
def get_items(db: Session = Depends(get_db)):
    """Get all items."""
    try:
        # Implementation
        logger.info("Fetching items")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

### Rules

- ✅ Use `logging` (never `print()`)
- ✅ Add docstrings to all functions
- ✅ Handle errors with try/except
- ✅ Use type hints where possible
- ❌ No hardcoded credentials
- ❌ No debug bypass code
- ❌ No `TODO` without `TODO-PROD:` for production

---

## 🧪 Testing

### Adding Tests

**Unit Tests:**
```python
# python-services/policy-service/tests/test_feature.py

import pytest
from fastapi.testclient import TestClient


def test_feature_success(client: TestClient):
    """Test successful feature operation."""
    response = client.get("/api/v1/feature/")
    assert response.status_code == 200
```

**E2E Tests:**
```python
# tests/e2e/verify_feature_flow.py

import requests

BASE_URL = "http://localhost:8000"


def test_feature_flow():
    """Test complete feature flow."""
    # Test implementation
    pass
```

### Running Tests

```bash
# All tests
./tests/run_tests.sh all

# Specific suites
./tests/run_tests.sh unit
./tests/run_tests.sh integration
./tests/run_tests.sh e2e

# Load tests
k6 run tests/load/scenarios/feature.js
```

---

## 🔒 Security

### Security Checklist

Before submitting:

- [ ] No debug bypass code
- [ ] No `print()` statements (use `logging`)
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] Proper error handling (no stack traces in production)
- [ ] Rate limiting on sensitive endpoints
- [ ] Authentication checks on protected routes

### Security Reviews

Changes to these files require extra review:
- `python-services/policy-service/app/core/secure_auth.py`
- `python-services/policy-service/app/routes/pharmacy.py`
- `python-services/policy-service/app/routes/admin_auth.py`
- Any authentication/authorization code

---

## ✅ Submission Checklist

Before submitting PR or completing AI task:

- [ ] Files in correct folders (no root-level files)
- [ ] No duplicate files created
- [ ] Code follows existing patterns
- [ ] Tests added for new features
- [ ] Documentation updated
- [ ] `docs/README.md` updated (if new docs)
- [ ] No `print()` statements
- [ ] Security standards followed
- [ ] Validation script passes:
  ```bash
  python scripts/validate-project-structure.py
  ```

---

## 🔍 Code Review Process

### For AI-Generated Code

1. **Run validation:**
   ```bash
   python scripts/validate-project-structure.py
   ```

2. **Check for common issues:**
   - Files in root directory
   - Duplicate functionality
   - Missing tests
   - Debug code left in

3. **Verify against AGENTS.md:**
   - All rules followed?
   - Proper file placement?
   - Documentation updated?

### For Human Contributors

1. Create feature branch
2. Make changes following standards
3. Run tests
4. Run validation script
5. Submit PR with description
6. Address review feedback

---

## 🆘 Need Help?

### Resources

- **Project Structure:** `PROJECT_STRUCTURE.md`
- **AI Guidelines:** `AGENTS.md`
- **Scripts:** `scripts/README.md`
- **Docs:** `docs/README.md`

### Common Issues

**"Where should I put this file?"**
- Check PROJECT_STRUCTURE.md
- Look at similar existing files
- Ask in PR description

**"Is this a duplicate?"**
- Search for similar file names
- Check docs/ for similar topics
- Review before creating

**"Tests are failing"**
- Check `python-services/policy-service/tests/conftest.py`
- Use existing fixtures
- Ensure database is set up

---

## 📞 Contact

- **Issues:** GitHub Issues
- **Email:** dev@wali.ci
- **Docs:** https://docs.wali.ci

---

Thank you for maintaining code quality! 🎉

**Remember:** When in doubt, check AGENTS.md first!
