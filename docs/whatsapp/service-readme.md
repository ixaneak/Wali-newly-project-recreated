# WhatsApp Business API Integration for Wali Assurance

Production-grade WhatsApp Business API implementation for Ivorian micro-insurance.

## 🏗️ Architecture

### Core Components

```
app/whatsapp/
├── __init__.py              # Module exports
├── models.py                # SQLAlchemy models (CIMA compliant)
├── state_machine.py         # Finite state machine for conversations
├── client.py               # Meta WhatsApp API client
├── webhook_handler.py      # FastAPI webhook endpoints
├── image_processor.py      # Fraud detection & image processing
├── service.py              # High-level business logic
└── requirements.txt        # Dependencies
```

## 🔐 Security Features

### 1. Webhook Security
- **HMAC-SHA256 signature verification**
- **Rate limiting**: 30 messages/minute per user
- **Circuit breaker**: Switches to SMS after 5 API failures
- **Idempotency**: Duplicate message detection via Redis

### 2. Fraud Detection (Image Processing)
- **Perceptual hash comparison**: Detect duplicate claim photos
- **EXIF analysis**: GPS validation, date verification
- **Metadata stripping**: Remove GPS before storage (privacy)
- **AES-256 encryption**: All images encrypted at rest

### 3. Compliance (CIMA + Law 2013-450)
- **Cross-border logging**: Every Meta API call logged
- **Data retention**: 3-year auto-purge
- **Opt-in required**: GDPR-compliant consent flow
- **Audit trail**: SHA-256 hashes of all messages

## 🔄 Conversation States

```python
OPT_IN_REQUIRED → IDLE → [B2B_ENROLLMENT, TRADE_SELECTION, PLAN_SELECTION]

PLAN_SELECTION → PARENT_CONFIRMATION (mandatory for family plans) → LOCATION_CAPTURE → PAYMENT_PENDING

ACTIVE_CLAIM → DOCUMENT_UPLOAD → FRAUD_REVIEW → SETTLEMENT
```

### Critical Rules
1. **Never skip PARENT_CONFIRMATION** for family plans (CIMA requirement)
2. **Auto-timeout**: 24 hours of inactivity resets to IDLE
3. **Idempotency**: Same `message_id` cannot trigger state change twice

## 🚀 Usage

### 1. Environment Variables
```bash
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAB...
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
```

### 2. Webhook Configuration
Configure in Meta Business Manager:
- **URL**: `https://api.wali.ci/webhooks/whatsapp`
- **Verify Token**: Same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- **Subscriptions**: `messages`, `message_template_status_update`

### 3. Send Message
```python
from app.whatsapp import WhatsAppClient, OutboundMessage, MessageType

client = WhatsAppClient(
    phone_number_id="123456789",
    access_token="EAAB..."
)

# Send text
client.send_message(OutboundMessage(
    phone="+2250701010101",
    type=MessageType.TEXT,
    text="Bonjour! Votre cotisation est due."
))

# Send template
client.send_template_message(
    phone="+2250701010101",
    template_name="payment_reminder",
    language="fr",
    params=["5000", "31/12/2024", "07 XX XX XX XX"]
)
```

### 4. B2B Group Enrollment
```python
from app.whatsapp import WhatsAppService, GroupEnrollmentRequest

service = WhatsAppService(client, state_machine, db)

# Create group
group = service.create_group_enrollment(GroupEnrollmentRequest(
    name="Syndicat Gbaka Abidjan",
    leader_phone="+2250701010101",
    leader_name="Kouassi Jean",
    region="Abidjan",
    expected_members=50
))

# Add member
service.add_member_to_group(group.code, "+2250702020202")
```

## 📋 Message Templates (Meta Pre-approval Required)

### 1. `welcome_message` (UTILITY)
```
Bienvenue chez {{1}}. Votre assurance santé sans avance. 
Support: {{2}}. Répondez OK pour commencer.
```

### 2. `claim_received` (UTILITY)
```
Sinistre {{1}} reçu. Traitement en 48h max. Suivi: {{2}}
```

### 3. `payment_reminder` (PAYMENT)
```
Votre cotisation {{1}} CFA est due le {{2}}. 
Payez par OM/Wave au {{3}}. Ref: WALI[votre numéro]
```

### 4. `pharmacy_approval` (UTILITY)
```
Autorisation pharmacie {{1}}. QR valable {{3}} min: {{2}}. 
Ne partagez pas ce code.
```

## 🧪 Testing

### Webhook Verification
```bash
curl "https://api.wali.ci/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=123456"
```

### Send Test Message
```bash
curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "+2250701010101",
    "type": "text",
    "text": {"body": "Test message"}
  }'
```

## 📊 Monitoring

### Logs
```python
# Security audit logs
logger.info(f"SECURITY_AUDIT: {log_data}")

# Payment audit logs
logger.info(f"PAYMENT_AUDIT: {log_data}")
```

### Circuit Breaker Status
```python
if client._circuit_open:
    # Switch to SMS fallback
    send_sms_fallback(phone, message)
```

## 🌍 Language Support

| Code | Language | Regions |
|------|----------|---------|
| `fr` | French | National (default) |
| `dy` | Dioula | Korhogo, Odienné (North) |
| `ba` | Baoulé | Yamoussoukro (Central) |

## ⚠️ CIMA Compliance Checklist

- [x] **Parent confirmation** mandatory for family plans
- [x] **48-hour cooling-off** period communicated
- [x] **Policy documents** delivered via WhatsApp Document
- [x] **Audit trail** with SHA-256 hashes
- [x] **3-year retention** with auto-purge
- [x] **Cross-border transfer** logging

## 🔧 Troubleshooting

### Webhook Not Receiving
1. Verify HTTPS endpoint
2. Check `hub.verify_token` matches
3. Ensure `/webhooks/whatsapp` accessible

### Message Not Sending
1. Check `access_token` not expired
2. Verify `phone_number_id` correct
3. Check Meta Business Manager status

### Image Processing Failures
1. Verify `/tmp` has write permissions
2. Check S3 credentials configured
3. Review `image_processor.py` logs

## 📚 References

- [Meta WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [CIMA Insurance Regulations](https://www.cima.int/)
- [Law 2013-450 (Ivory Coast Data Protection)](http://www.dgi.gouv.ci/)
