# WhatsApp OTP Implementation Guide

## 💰 Cost Comparison

| Provider | Method | Cost per OTP | Monthly (1000 OTPs) |
|----------|--------|--------------|---------------------|
| **Twilio SMS** | SMS | $0.05-0.10 | $50-100 |
| **Twilio WhatsApp** | WhatsApp | $0.005-0.01 | $5-10 |
| **Meta WhatsApp API** | WhatsApp | $0.00* | ~$0 |

*Meta WhatsApp API: Free for user-initiated conversations (24h window). Only pay for business-initiated conversations outside the window (~$0.05).

### Ivory Coast Specific Costs

| Provider | SMS (XOF) | WhatsApp (XOF) | Savings |
|----------|-----------|----------------|---------|
| Twilio | ~30-60 F | ~3-6 F | **90%** |
| Local Provider | ~15-25 F | ~0-5 F | **80%** |

**Conclusion**: WhatsApp is **5-10x cheaper** than SMS for OTP delivery.

---

## 🚀 Quick Setup

### Option 1: Meta WhatsApp Business API (Recommended - Free!)

#### Step 1: Create Meta Developer Account
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a developer account
3. Create a new app (type: Business)

#### Step 2: Set Up WhatsApp Business
1. Add "WhatsApp" product to your app
2. Create/select a Business Account
3. Verify your business (required for production)

#### Step 3: Get API Credentials
```bash
# In Meta Developer Dashboard:
# 1. Go to WhatsApp → API Setup
# 2. Get "Access Token" (temporary, 24h)
# 3. Get "Phone Number ID"
# 4. Get "WhatsApp Business Account ID"

# For permanent token:
# Go to System Users → Generate Token (never expires)
```

#### Step 4: Configure Environment Variables
```bash
# .env file

# WhatsApp Business API (Meta)
WHATSAPP_API_TOKEN=your_permanent_access_token_here
WHATSAPP_PHONE_NUMBER_ID=12345678901234
WHATSAPP_BUSINESS_ACCOUNT_ID=1234567890
WHATSAPP_OTP_TEMPLATE=wali_otp

# Optional: Fallback to Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=+14155238886
```

### Option 2: Twilio WhatsApp (Easier Setup)

If Meta setup is too complex, use Twilio WhatsApp as a simpler alternative:

```bash
# .env file
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=+14155238886  # Twilio sandbox number
```

Note: Users must message "join <sandbox-code>" to the Twilio number first.

---

## 📱 How It Works

### User Flow
```
1. User enters phone number on login page
   ↓
2. System checks WhatsApp availability
   ↓
3. WhatsApp message sent (if available)
   ↓
4. User receives message:
   "🔐 Code de vérification WALI: 123456
    Ce code est valable pendant 5 minutes."
   ↓
5. User enters code
   ↓
6. Login successful!
```

### Fallback Flow
```
1. WhatsApp fails or unavailable
   ↓
2. Automatic fallback to SMS
   ↓
3. SMS sent via Twilio
   ↓
4. User receives SMS with code
```

---

## 🔧 Code Usage

### Send OTP (Recommended Method)

```python
from app.core.mfa import MFAService

mfa = MFAService(db_session)

# Automatically chooses WhatsApp or SMS
result = mfa.send_user_otp(
    phone_number="+2250707070707",
    name="Kouassi Jean"
)

if result['success']:
    print(f"OTP sent via {result['provider']}")  # 'whatsapp' or 'sms'
    print(f"Code: {result['code']}")  # Store this securely!
else:
    print(f"Failed: {result['message']}")
```

### Direct WhatsApp Usage

```python
from app.core.whatsapp_otp import send_unified_otp

result = send_unified_otp(
    phone="+2250707070707",
    name="Kouassi Jean"
)

# Returns: {'success': True, 'code': '123456', 'provider': 'whatsapp'}
```

---

## 📋 WhatsApp Message Template

For Meta API, you need an approved template. Create this in Meta Business Manager:

**Template Name**: `wali_otp`
**Language**: French
**Category**: Authentication

**Template Body**:
```
🔐 *Code de vérification WALI*

Bonjour {{1}},

Votre code de vérification est : *{{2}}*

Ce code est valable pendant {{3}} minutes.

Ne partagez ce code avec personne.
```

**Variables**:
- `{{1}}` = User name
- `{{2}}` = OTP code
- `{{3}}` = Validity time (minutes)

---

## 🧪 Testing

### Meta WhatsApp Sandbox

1. Get sandbox credentials from Meta Developer Console
2. Add test phone numbers
3. Send test message:

```bash
curl -X POST \
  https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "messaging_product": "whatsapp",
    "to": "+2250707070707",
    "type": "text",
    "text": {"body": "Test message from WALI"}
  }'
```

### Twilio WhatsApp Sandbox

1. Join sandbox by messaging "join <your-code>" to +1 415 523 8886
2. Test via console or API

---

## 🔒 Security Considerations

### Code Storage
- Never store OTP codes in plain text
- Store hashed version (SHA-256) or use short TTL cache (Redis)
- Maximum 3 attempts per code
- Auto-expire after 5 minutes

### Rate Limiting
```python
# Limit OTP requests
MAX_OTP_REQUESTS = 3  # per phone per hour
MAX_OTP_ATTEMPTS = 3  # per code
```

### WhatsApp Verification
- Verify the phone number has WhatsApp before sending
- Fall back to SMS if user doesn't have WhatsApp
- Track delivery status and retry failures

---

## 📊 Monitoring

### Key Metrics

```python
# Track in your logs/SIEM
{
    "event": "otp_sent",
    "provider": "whatsapp",  # or "sms"
    "success": True,
    "phone_hash": "sha256_hash",
    "latency_ms": 250,
    "cost_usd": 0.00
}
```

### Cost Tracking

| Metric | Target |
|--------|--------|
| WhatsApp success rate | > 80% |
| SMS fallback rate | < 20% |
| Avg cost per OTP | < $0.01 |
| Delivery latency | < 5 seconds |

---

## 🛠️ Troubleshooting

### Issue: "WhatsApp not configured"
**Solution**: Check environment variables are set:
```bash
echo $WHATSAPP_API_TOKEN
echo $WHATSAPP_PHONE_NUMBER_ID
```

### Issue: "Message failed to send"
**Solution**: Check:
1. Phone number format (+225...)
2. User has WhatsApp installed
3. Your template is approved (Meta API)
4. User has messaged you first (Twilio sandbox)

### Issue: "High SMS fallback rate"
**Solution**:
1. Check WhatsApp penetration in your user base
2. Prompt users to install WhatsApp
3. Offer WhatsApp signup bonus

---

## 📈 Migration from SMS

### Phase 1: Dual Support (Current)
- Send WhatsApp first
- Fall back to SMS
- Track success rates

### Phase 2: WhatsApp Preferred
- Promote WhatsApp in UI
- Educate users
- Maintain SMS fallback

### Phase 3: SMS Only for Edge Cases
- 90%+ WhatsApp adoption
- SMS for non-smartphone users
- Significant cost savings

---

## 💡 Best Practices

1. **Always have SMS fallback** - Not all users have WhatsApp
2. **Cache delivery status** - Don't retry if recent failure
3. **Track costs per provider** - Monitor savings
4. **A/B test message copy** - Improve open rates
5. **Localize messages** - French for Ivory Coast
6. **Include branding** - "WALI" in message for trust

---

## 📞 Support

### Meta WhatsApp API
- [Meta for Developers](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Business API Docs](https://business.whatsapp.com/products/business-platform)

### Twilio WhatsApp
- [Twilio WhatsApp Docs](https://www.twilio.com/docs/whatsapp)
- Console: [console.twilio.com](https://console.twilio.com)

### WALI Support
- Email: support@wali.ci
- WhatsApp: +225 XX XX XX XX
