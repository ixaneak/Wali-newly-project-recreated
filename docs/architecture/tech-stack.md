# Wali Tech Stack

## Language Distribution

| Layer | Language | Framework | Port | Directory |
|-------|----------|-----------|------|-----------|
| Mobile PWA | TypeScript | Next.js 16 + React 19 | 3000 | `typescript-apps/pwa/` |
| Notification Service | TypeScript | Node.js | 8003 | `typescript-apps/notification-service/` |
| Policy Service | Python 3.11+ | FastAPI | 8000 | `python-services/policy-service/` |
| Claims Service | Python 3.11+ | FastAPI | 8001 | `python-services/claims-service/` |
| Compliance Service | Python 3.11+ | FastAPI | 8002 | `python-services/compliance-service/` |
| Identity Service | Python 3.11+ | FastAPI | 8004 | `python-services/identity-service/` |
| Payment Service | Go 1.21+ | Gin | 8080 | `go-services/payment-service/` |
| Database | SQL | PostgreSQL 15 | 5432 | `database/` |

## Directory Structure

```
wali-backend/
├── typescript-apps/     # All TypeScript code
├── python-services/     # All Python code
├── go-services/         # All Go code
├── database/            # Migrations, schemas, seeds
├── shared/              # Cross-language contracts
├── infrastructure/      # Docker, Fly.io configs
├── tests/e2e/           # End-to-end test scripts
└── _archive/            # Legacy code (not in production)
```

## Adding New Code

| What | Where | Notes |
|------|-------|-------|
| New API endpoint | `python-services/[service]/app/routes/` | Use FastAPI router |
| New UI component | `typescript-apps/pwa/components/` | React component |
| New DB column | `python-services/[service]/alembic/versions/` | Alembic migration |
| New enum/constant | `shared/constants.json` | Generate language-specific files |

## Standards

### TypeScript
- Strict mode enabled
- Use absolute imports (`@/components`, `@/lib`)
- No `any` types
- ESLint + Prettier

### Python
- Python 3.11+
- Formatter: `black`
- Linter: `ruff`
- Type hints required
- No raw SQL (use SQLAlchemy ORM)

### Go
- Go 1.21+
- Standard project layout
- `gofmt` enforced
- Return errors, don't panic

## Forbidden Patterns

```
❌ Python files in typescript-apps/
❌ TypeScript files in python-services/
❌ Go files outside go-services/
❌ Hardcoded environment variables
❌ Duplicate validation logic
❌ Raw SQL in route handlers
```
