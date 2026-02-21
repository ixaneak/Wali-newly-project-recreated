# AI Agent Guidelines for Wali Project

**This document ensures AI agents (Claude, GPT, etc.) maintain project organization when adding features.**

---

## 🎯 Golden Rules

### 1. NEVER Create Files in Root Directory
❌ **Forbidden:** Creating `.md`, `.py`, `.ps1`, `.txt` files in project root  
✅ **Required:** Use proper subdirectories:
- Scripts → `scripts/`
- Docs → `docs/<category>/`
- Data → `data/`
- Logs → `logs/`
- Tests → `tests/<type>/`

### 2. ALWAYS Check Before Creating
Before creating ANY file, check if:
- A similar file already exists (avoid duplicates)
- There's an existing folder for this file type
- The file belongs in a service directory

### 3. Follow Existing Patterns
- Copy the style of existing files in the same directory
- Use same naming conventions (kebab-case for files)
- Match the existing code structure

---

## 📁 File Placement Reference

### Where to Put New Files

| File Type | Location | Example |
|-----------|----------|---------|
| Python scripts/tools | `scripts/` | `scripts/generate-report.py` |
| PowerShell scripts | `scripts/` | `scripts/deploy-staging.ps1` |
| Documentation | `docs/<category>/` | `docs/guides/new-feature.md` |
| JSON data/mocks | `data/` | `data/mock-users.json` |
| Log files | `logs/` | `logs/debug-output.txt` |
| Unit tests | `python-services/<service>/tests/` | `tests/test_new_feature.py` |
| E2E tests | `tests/e2e/` | `tests/e2e/test_flow.py` |
| Load tests | `tests/load/scenarios/` | `tests/load/scenarios/new-flow.js` |
| Service code | `python-services/<service>/app/` | `app/routes/new.py` |
| Docker configs | `infrastructure/` | `infrastructure/docker-compose.new.yml` |
| CI/CD workflows | `.github/workflows/` | `.github/workflows/new-job.yml` |

### Never Put These in Root
- ❌ Any `.md` files (except `README.md`)
- ❌ Any `.txt` files
- ❌ Any `.py` scripts
- ❌ Any `.ps1` scripts
- ❌ Any `.json` data files
- ❌ Any debug/log files

---

## 🏗️ Project Structure Reference

```
wali-backend/
├── .github/workflows/          # CI/CD only
├── data/                       # JSON, mock data ONLY
├── database/                   # SQL schemas ONLY
├── docs/                       # Documentation ONLY
│   ├── architecture/           # System design docs
│   ├── development/            # Dev guides
│   ├── guides/                 # User guides
│   ├── operations/             # DevOps docs
│   ├── security/               # Security docs
│   └── whatsapp/               # WhatsApp docs
├── go-services/                # Go microservices
├── infrastructure/             # Docker, monitoring
├── logs/                       # Log files ONLY
├── python-services/            # Python services
│   ├── claims-service/         # Claims service
│   └── policy-service/         # Policy service
│       └── tests/              # Unit tests here
├── scripts/                    # Automation scripts
├── security-audit/             # Security tools
├── shared/                     # Shared schemas
├── tests/                      # Test suites
│   ├── e2e/                    # E2E tests
│   └── load/                   # Load tests
└── typescript-apps/            # Frontend apps
```

---

## 📝 Documentation Standards

### Creating New Documentation

1. **Choose the right category:**
   - Technical architecture → `docs/architecture/`
   - Developer guides → `docs/development/`
   - User how-tos → `docs/guides/`
   - Deployment/infra → `docs/operations/`
   - Security/compliance → `docs/security/`

2. **Naming convention:**
   - Use kebab-case: `new-feature-guide.md`
   - Be descriptive: `payment-webhook-guide.md` not `guide.md`

3. **Required header:**
   ```markdown
   # Title
   
   **Date:** YYYY-MM-DD  
   **Status:** [Draft/Review/Complete]
   
   ---
   ```

4. **Update docs/README.md:**
   Add new doc to the index in `docs/README.md`

---

## 🧪 Testing Standards

### Adding New Tests

**Unit Tests:**
- Location: `python-services/<service>/tests/`
- Naming: `test_<feature>.py`
- Must use existing fixtures from `conftest.py`

**E2E Tests:**
- Location: `tests/e2e/`
- Naming: `verify_<feature>_flow.py`
- Must be runnable via `tests/run_tests.sh`

**Load Tests:**
- Location: `tests/load/scenarios/`
- Naming: `<feature>_load.js`
- Follow k6 patterns from existing scenarios

---

## 🔒 Security Standards

### Security-Sensitive Changes

ALWAYS check these files before security changes:
- `docs/security/PRODUCTION_SECURITY_FIXES.md`
- `python-services/policy-service/app/core/secure_auth.py`
- `python-services/policy-service/app/routes/pharmacy.py`

NEVER:
- Add debug bypass code
- Add `print()` statements (use `logging`)
- Hardcode credentials
- Add `TODO` without `TODO-PROD:` prefix for production items

---

## ✅ Pre-Completion Checklist

Before finishing ANY task, verify:

- [ ] No files created in root directory (except if explicitly requested)
- [ ] All scripts in `scripts/` folder
- [ ] All docs in appropriate `docs/<category>/` folder
- [ ] No duplicate files created (check if similar exists)
- [ ] Code follows existing patterns in same directory
- [ ] Tests added for new features
- [ ] Documentation updated (if needed)
- [ ] `docs/README.md` updated (if new docs added)

---

## 🚨 Common Mistakes to Avoid

### Mistake 1: Creating files in root
```bash
# WRONG:
/create new-script.py in root
/create notes.txt in root

# CORRECT:
/create scripts/new-script.py
/create docs/guides/notes.md
```

### Mistake 2: Duplicating existing functionality
```bash
# WRONG:
/create docs/security/new-security-doc.md
# (when similar doc already exists)

# CORRECT:
/update docs/security/existing-doc.md
```

### Mistake 3: Wrong file extensions
```bash
# WRONG:
/create docs/feature.txt

# CORRECT:
/create docs/guides/feature.md
```

### Mistake 4: Forgetting to update indexes
```bash
# After creating docs/guides/new-guide.md:
# ALSO update docs/README.md to include it
```

---

## 🎨 Code Style Reference

### Python (Policy/Claims Services)
```python
# File: python-services/policy-service/app/routes/example.py

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db

router = APIRouter(prefix="/api/v1/example", tags=["example"])
logger = logging.getLogger(__name__)


@router.get("/")
def get_examples(db: Session = Depends(get_db)):
    \"\"\"Get all examples.\"\"\"
    try:
        # Implementation
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

### Documentation
```markdown
# Feature Name

**Date:** 2026-02-21  
**Status:** Complete

---

## Overview

Brief description.

## Usage

```bash
# Example
```

---

**See also:**
- [Related Doc](../other/doc.md)
```

---

## 🤖 AI Agent Prompt Template

When asking an AI agent to add features, use this template:

```
Please add [feature description] to the Wali project.

**Requirements:**
- Follow AGENTS.md guidelines
- Place files in correct directories (NOT root)
- Follow existing code patterns in similar files
- Update docs/README.md if adding documentation
- Run tests to verify

**Checklist before completion:**
- [ ] No root-level files created
- [ ] All files in proper folders
- [ ] No duplicates
- [ ] Tests added
- [ ] Documentation updated
```

---

## 📞 Need Help?

If unsure about file placement:
1. Check `PROJECT_STRUCTURE.md`
2. Look at similar existing files
3. Ask: "Where should I put this file?"

**Never guess - always verify structure first!**

---

**Last Updated:** 2026-02-21  
**Maintainer:** Wali Development Team
