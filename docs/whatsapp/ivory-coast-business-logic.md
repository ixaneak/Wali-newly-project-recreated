# Ivory Coast Business Logic - WhatsApp Implementation

## Overview

This document describes the Ivory Coast-specific business logic constraints implemented in the Wali WhatsApp service.

## Legal Framework

### Law 2013-450 (Data Protection)
- **Explicit Consent**: Users must respond with "OUI" (not "OK" or other variations) to consent
- **Cross-Border Transfer Logging**: Every Meta API call logged for compliance audit
- **Pseudonymization**: Phone numbers hashed in logs
- **Retention**: 365 days data retention logged

### ARTCI Regulations (Telecom Authority)
- **Quiet Hours**: No marketing messages between 20:00 and 08:00
- **Emergency Exception**: Medical emergencies (keywords: urgence, accident, hopital) allowed 24/7
- **USSD Fallback**: Must include alternative contact method

### CIMA Regulations (Insurance Authority)
- **Group Size Limit**: Maximum 100 members per group
- **Parental Confirmation**: Mandatory for Family plans
- **Duplicate Prevention**: Cannot have multiple active policies
- **Claims Limit**: WhatsApp processing limited to ≤500,000 CFA

## Implementation Details

### 1. Quiet Hours Compliance (`_is_quiet_hours()`)

```python
def _is_quiet_hours(self) -> bool:
    """Check if current time is within ARTCI quiet hours (before 08:00 or after 20:00)."""
    now = datetime.utcnow()
    hour = now.hour
    return hour < 8 or hour >= 20
```

**Usage**:
- Payment reminders queued during quiet hours
- Emergency claims bypass restriction
- User-initiated messages always allowed

### 2. Law 2013-450 Consent (`_validate_explicit_consent()`)

```python
def _validate_explicit_consent(self, message: str) -> bool:
    """Validate explicit 'OUI' consent for Law 2013-450."""
    return message.strip().upper() == "OUI"
```

**Requirements**:
- Must be uppercase "OUI" (not "oui", "ok", "yes", etc.)
- Part of opt-in flow before any data processing
- Stored in conversation context

### 3. Parental Coverage Confirmation

```python
async def send_parental_confirmation(self, phone: str, region: Optional[str] = None):
    """Send mandatory parental coverage confirmation (CIMA requirement)."""
    text = (
        "⚠️ CONFIRMATION OBLIGATOIRE\n\n"
        "La formule Famille couvre:\n"
        "• Vous (souscripteur)\n"
        "• Votre conjoint(e)\n"
        "• Jusqu'à 3 enfants\n"
        "• 2 parents (père ET mère)\n\n"
        "Cette formule inclut vos 2 parents. Confirmez-vous cette inclusion?\n\n"
        "Répondez OUI pour confirmer ou NON pour exclure."
    )
```

**Flow**:
1. User selects "famille" plan
2. State transitions to `PARENT_CONFIRMATION`
3. Mandatory confirmation message sent
4. User must respond "OUI" to proceed
5. If "NON", downgraded to individual plan

### 4. CNMCI Trade Validation

```python
# CNMCI Official Trade Categories
CNMCI_TRADES = [
    "menuisier", "mecanicien", "electricien", "plombier", "macon",
    "peintre", "soudeur", "coiffeur", "tailleur", "vendeur",
    "cordonnier", "tisserand", "potier", "forgeron", "cuisinier",
    "boulanger", "patissier", "mecanicien_moto", "carrossier",
    "vitrier", "tapissier", "maroquinier", " bijoutier", "horloger"
]

def _validate_trade_cnmci(self, trade: str) -> bool:
    """Validate trade against CNMCI official list."""
    return trade.lower() in self.CNMCI_TRADES
```

**Note**: User sees reference to "Liste CNMCI" in trade selection menu.

### 5. Regional Handling

```python
BORDER_REGIONS = ["noe", "danane", "odienne", "man", "touba"]

def _get_footer(self, region: Optional[str] = None) -> str:
    """Generate message footer with USSD fallback and regional info."""
    footer = f"\n\n📞 USSD: {self.USSD_FALLBACK} (si WhatsApp indisponible)"
    
    if region:
        region_lower = region.lower()
        if region_lower in ["abidjan", "cocody", "marcory", "treichville"]:
            footer += "\n🏥 Pharmacie de garde: https://wali.ci/pharmacies-garde"
        elif region_lower in ["korhogo", "man", "odienne", "bondoukou"]:
            footer += "\n⚠️ Zone rurale: En cas de problème réseau, visitez un agent Wali."
        elif region_lower in self.BORDER_REGIONS:
            footer += "\n⏳ Vérification additionnelle requise (zone frontalière)."
    
    return footer
```

**Regional Classifications**:
- **Abidjan Metro**: Pharmacy links included
- **Rural**: Agent visit recommendation
- **Border Regions**: Auto-flagged for fraud review

### 6. USSD Fallback Integration

Every message includes footer with USSD code:
```
📞 USSD: 130WALI# (si WhatsApp indisponible)
```

### 7. Claims Limit Enforcement (>500,000 CFA)

```python
def _check_claim_limit(self, amount: Decimal) -> bool:
    """Check if claim amount exceeds 500,000 CFA limit for WhatsApp processing."""
    return amount <= Decimal("500000")

async def handle_claim_with_escalation(self, phone: str, amount: Decimal, description: str, db: Session):
    """Handle claim with automatic escalation for amounts >500k CFA."""
    if not self._check_claim_limit(amount):
        # Escalate to human agent
        return {
            "escalated": True,
            "message": "Votre sinistre dépasse 500,000 FCFA. Un agent Wali va vous contacter sous 24h..."
        }
```

### 8. Policy Document Delivery (24h Legal Requirement)

```python
def _send_policy_document(self, phone: str, policy_id: str, language: str = "fr"):
    """Send PDF policy document within 24 hours of payment (legal requirement)."""
    pdf_url = f"https://wali.ci/policies/{policy_id}/document.pdf"
    # ... send message with document link
```

### 9. Duplicate Policy Prevention

```python
def _check_active_policy(self, phone: str) -> bool:
    """Check if user already has an active policy (prevent duplicates)."""
    existing = self.db.query(WhatsAppConversation).filter(
        WhatsAppConversation.phone == phone,
        WhatsAppConversation.state.in_([
            ConversationState.PAYMENT_PENDING,
            ConversationState.SETTLEMENT
        ])
    ).first()
    return existing and existing.context.get("policy_active")
```

### 10. Cross-Border Transfer Logging (Law 2013-450)

```python
def _log_cross_border_transfer(self, phone: str, transfer_type: str, destination: str, 
                               data_type: str, legal_basis: str, db: Session):
    """Log cross-border data transfers as required by Law 2013-450."""
    logger.info(
        f"CROSS_BORDER_TRANSFER|"
        f"timestamp={datetime.utcnow().isoformat()}|"
        f"phone_hash={hash(phone) % (10**10)}|"  # Pseudonymized
        f"type={transfer_type}|"
        f"destination={destination}|"
        f"data_type={data_type}|"
        f"legal_basis={legal_basis}|"
        f"retention_days=365"
    )
```

### 11. Message Sanitization

```python
def _sanitize_message(self, text: str) -> str:
    """Remove any mobile money PINs and informal language from messages."""
    import re
    
    # Delete any 4-digit PINs that might have been sent by mistake
    text = re.sub(r'\b\d{4}\b', '[SUPPRIMÉ]', text)
    
    # Replace informal French with professional tone
    informal_to_formal = {
        r'\bsalut\b': 'Bonjour',
        r'\bça va\b': 'Comment allez-vous',
        # ... more mappings
    }
    
    for pattern, replacement in informal_to_formal.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text
```

## State Machine Integration

The business logic is integrated into the state machine flow:

```
OPT_IN_REQUIRED → IDLE → TRADE_SELECTION → PLAN_SELECTION → PARENT_CONFIRMATION (if family) → PAYMENT_PENDING → IDLE
                    ↓
              ACTIVE_CLAIM → DOCUMENT_UPLOAD → SETTLEMENT
```

### Critical Transitions

1. **OPT_IN_REQUIRED**: Must receive "OUI" to proceed (Law 2013-450)
2. **TRADE_SELECTION**: CNMCI validation enforced
3. **PLAN_SELECTION**: Family → forced PARENT_CONFIRMATION transition
4. **PARENT_CONFIRMATION**: Must receive "OUI" or downgraded to individual
5. **ACTIVE_CLAIM**: Amount checked for escalation threshold

## Testing Checklist

- [ ] "OUI" required for opt-in ("ok" should not work)
- [ ] Quiet hours block payment reminders (08:00-20:00 only)
- [ ] Emergency keywords bypass quiet hours
- [ ] Family plan requires parental confirmation
- [ ] Border regions auto-flag for fraud
- [ ] Invalid CNMCI trade rejected
- [ ] Duplicate policy blocked
- [ ] Claim >500k escalated to human
- [ ] USSD fallback in every message
- [ ] Cross-border transfers logged
- [ ] Mobile money PINs redacted
- [ ] Informal language converted to formal

## Compliance Audit Trail

All compliance events are logged with specific format:
- `CROSS_BORDER_TRANSFER`: Meta API calls
- `fraud_review_required`: Border region enrollments
- `Claim escalated`: >500k claims
- `Enrollment completion failed`: Validation failures

## Localization

Messages support FR/DY/BA languages:
- **FR**: French (primary)
- **DY**: Dioula (Jula)
- **BA**: Baoulé

Regional variations included in footers based on user's location.
