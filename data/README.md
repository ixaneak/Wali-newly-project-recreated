# Wali Data Files

JSON data files, mock data, and API specifications.

---

## 📁 Files

### Mock Data

| File | Description |
|------|-------------|
| `mock_policies.json` | Mock policy data for testing |
| `mock_claims.json` | Mock claims data for testing |
| `e2e_state.json` | E2E test state persistence |

### API Specifications

| File | Description |
|------|-------------|
| `claims_openapi.json` | Claims service OpenAPI specification |

---

## 🔄 Data Flow

```
Mock Data → Services → Tests
     ↓
Production APIs (Orange/MTN/Wave)
```

---

## ⚠️ Note

These files are for **development and testing only**. Production data is stored in PostgreSQL.

---

**See also:**
- [Tests](../tests/)
- [Development Guide](../docs/development/)
