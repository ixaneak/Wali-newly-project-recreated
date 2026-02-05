# Ivory Coast Legal Compliance Checklist

## Wali Application - Law 2013-450 & ARTCI Compliance

### ✅ Terms of Use (Conditions Générales d'Utilisation)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Governing Law: Ivorian law (Law 2013-450, OHADA) | ✅ Done | Article 2 |
| Jurisdiction: Courts of Abidjan | ✅ Done | Article 2 |
| Age requirement: 18+ or 13+ with consent | ✅ Done | Article 3 |
| ARTCI compliance reference | ✅ Done | Article 1, 2 |
| Acceptable use prohibitions | ✅ Done | Article 5 |
| Account security obligations | ✅ Done | Article 4 |
| Termination clauses | ✅ Done | Article 10 |
| IP protections (Ivorian IP Code) | ✅ Done | Article 6 |
| Liability limitations (OHADA standards) | ✅ Done | Article 8 |
| Amicable dispute resolution period | ✅ Done | Article 11 (30 days) |
| Service availability/maintenance | ✅ Done | Article 9 |
| User content licensing | ✅ Done | Article 7 |

### ✅ Privacy Policy (Politique de Confidentialité)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Data Controller identification | ✅ Done | Article 1 |
| Legal basis: Express consent (Art. 23) | ✅ Done | Article 2 |
| Categories of personal data | ✅ Done | Article 3 |
| Processing purposes | ✅ Done | Article 4 |
| Data subject rights (Art. 28-34) | ✅ Done | Article 5 |
| Right of access (Art. 28) | ✅ Done | Article 5.1 |
| Right of rectification (Art. 29) | ✅ Done | Article 5.2 |
| Right of erasure (Art. 30) | ✅ Done | Article 5.3 |
| Right of objection (Art. 31) | ✅ Done | Article 5.4 |
| Right to portability (Art. 32) | ✅ Done | Article 5.5 |
| Post-mortem rights (Art. 34) | ✅ Done | Article 5.6 |
| Data retention periods (ARTCI aligned) | ✅ Done | Article 6 |
| Recipients list | ✅ Done | Article 7 |
| Cross-border transfers | ✅ Done | Article 8 |
| Security measures (Art. 19) | ✅ Done | Article 9 |
| Sensitive data handling (Art. 7) | ✅ Done | Article 10 |
| Cookies and tracking consent | ✅ Done | Article 11 |
| ARTCI contact details | ✅ Done | Contact box |
| Right to lodge complaints | ✅ Done | Article 12 |

### 📝 Before Deployment

Replace these placeholders in both documents:

- `[NOM DE LA SOCIÉTÉ]` / `[COMPANY NAME]` - Your legal company name
- `[ADRESSE COMPLÈTE]` / `[ADDRESS]` - Full business address in Abidjan
- `[NUMÉRO RCCM]` / `[RCCM NUMBER]` - Trade register number
- `[EMAIL DE CONTACT]` - General contact email
- `[EMAIL DE SUPPORT]` / `[SUPPORT EMAIL]` - Support email address
- `[EMAIL DPO]` / `[DPO EMAIL]` - Data Protection Officer email
- `[NUMÉRO DE TÉLÉPHONE]` - Phone number

### 📁 Files Created

| File | Purpose |
|------|---------|
| `app/legal/legal.css` | Styling for legal pages |
| `app/legal/terms/page.tsx` | Terms of Use (FR/EN) |
| `app/legal/privacy/page.tsx` | Privacy Policy (FR/EN) |
| `components/LegalLinks.tsx` | Login screen component |

### 🔗 Integration

Add to login screen:

```tsx
import { LegalLinks } from '@/components/LegalLinks';

// In your login form:
<LegalLinks />
```

### ⚖️ Legal Notes

1. **French version prevails** - Both documents state this explicitly
2. **30-day amicable period** - Required before litigation
3. **ARTCI notification** - Users can file complaints at www.artci.ci
4. **Consent required** - Login implies acceptance (per ARTCI guidelines)
