# OWASP Top 10 Remediation Guide for WALI

**Target:** CIMA Fintech Compliance  
**Standard:** OWASP ASVS Level 2 (Financial Services)  
**Last Updated:** 2026-02-18

---

## A01:2021 – Broken Access Control

### Vulnerabilities Found
- [ ] Missing authorization checks on admin endpoints
- [ ] IDOR (Insecure Direct Object Reference) on claim viewing
- [ ] CORS misconfiguration allowing wildcard origins

### Remediation

```python
# BEFORE (Vulnerable)
@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str):
    return db.get_claim(claim_id)  # No auth check!

# AFTER (Secure)
@app.get("/api/claims/{claim_id}")
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user)
):
    claim = db.get_claim(claim_id)
    
    # Verify ownership
    if claim.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log access
    log_security_event(
        event_type="claim_access",
        user_id=current_user.id,
        ip_address=request.client.host,
        details={"claim_id": claim_id}
    )
    
    return claim
```

### Implementation Checklist
- [ ] Add `@require_auth` decorator to all protected endpoints
- [ ] Implement role-based access control (RBAC)
- [ ] Add ownership checks for user-specific resources
- [ ] Enable CORS with explicit allowlist
- [ ] Add security headers middleware

---

## A02:2021 – Cryptographic Failures

### Vulnerabilities Found
- [ ] Weak JWT signing algorithm (HS256 should be RS256 in prod)
- [ ] Missing encryption for sensitive data at rest
- [ ] No key rotation mechanism

### Remediation

```python
# Add to security-audit/configs/encryption.py
from cryptography.fernet import Fernet
import os

class DataEncryption:
    """AES-256 encryption for sensitive data."""
    
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage for PII
encryption = DataEncryption()
encrypted_phone = encryption.encrypt(user.phone_number)
```

### Database Encryption
```sql
-- Enable PostgreSQL encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt columns containing PII
ALTER TABLE users ALTER COLUMN phone_number TYPE bytea 
USING pgp_sym_encrypt(phone_number, 'key')::bytea;
```

---

## A03:2021 – Injection

### Vulnerabilities Found
- [ ] SQL injection risk in raw queries
- [ ] NoSQL injection in MongoDB queries
- [ ] Command injection in file processing

### Remediation

```python
# BEFORE (SQL Injection Risk)
query = f"SELECT * FROM claims WHERE user_id = '{user_id}'"
result = db.execute(query)

# AFTER (Parameterized)
from sqlalchemy import text
query = text("SELECT * FROM claims WHERE user_id = :user_id")
result = db.execute(query, {"user_id": user_id})

# Input validation
from pydantic import BaseModel, validator

class ClaimCreate(BaseModel):
    description: str
    amount: int
    
    @validator('description')
    def validate_description(cls, v):
        # Prevent injection
        if any(char in v for char in [';', '--', '/*', '*/']):
            raise ValueError('Invalid characters in description')
        return sanitize_input(v, max_length=1000)
```

---

## A04:2021 – Insecure Design

### Vulnerabilities Found
- [ ] No business logic limits (unlimited claims)
- [ ] Missing fraud detection
- [ ] No rate limiting on sensitive operations

### Remediation

```python
# Add business logic limits
MAX_CLAIMS_PER_DAY = 3
MAX_CLAIM_AMOUNT = 500000  # XOF

@rate_limit(max_requests=3, window_seconds=86400)  # 3 per day
@app.post("/api/claims")
async def submit_claim(
    claim: ClaimCreate,
    current_user: User = Depends(get_current_user)
):
    # Check daily limit
    today_claims = db.count_claims_today(current_user.id)
    if today_claims >= MAX_CLAIMS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_CLAIMS_PER_DAY} claims per day"
        )
    
    # Check amount
    if claim.amount > MAX_CLAIM_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum claim amount is {MAX_CLAIM_AMOUNT} XOF"
        )
    
    # SAR detection
    sar_engine = SARDetectionEngine(db)
    risk = await sar_engine.analyze_claim(claim.dict())
    
    if risk and risk.risk_score > 70:
        # Auto-flag for review
        claim.status = "flagged_for_review"
        await notify_compliance_team.delay(claim.id, risk.risk_score)
```

---

## A05:2021 – Security Misconfiguration

### Vulnerabilities Found
- [ ] Default credentials in config
- [ ] Debug mode enabled in production
- [ ] Missing security headers
- [ ] Verbose error messages

### Remediation

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Security
    DEBUG: bool = False  # NEVER True in production
    SECRET_KEY: str  # Must be set in env
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Encryption
    ENCRYPTION_KEY: str  # 32-byte Fernet key
    
    class Config:
        env_file = ".env"
        
    @validator('DEBUG')
    def no_debug_in_prod(cls, v):
        if os.getenv('ENV') == 'production' and v:
            raise ValueError('DEBUG cannot be True in production')
        return v

settings = Settings()

# main.py
from security-audit.configs.security_headers import add_security_middleware

app = FastAPI(
    debug=settings.DEBUG,
    docs_url=None if not settings.DEBUG else "/docs",  # Hide docs in prod
    redoc_url=None if not settings.DEBUG else "/redoc",
)

add_security_middleware(app)

# Custom error handler (no stack traces in prod)
@app.exception_handler(Exception)
async def custom_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request.state.request_id
        } if not settings.DEBUG else {
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )
```

---

## A06:2021 – Vulnerable Components

### Remediation
```bash
# Run dependency audit
./security-audit/scripts/dependency_audit.sh

# Update all dependencies
pip install --upgrade -r requirements.txt

# Pin specific versions in requirements.txt
# requirements.txt
fastapi==0.109.0        # Pinned version
uvicorn[standard]==0.27.0
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
sqlalchemy==2.0.25
```

### SCA Tools Configuration
```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run pip-audit
        uses: pypa/gh-action-pip-audit@v1.0.8
        with:
          inputs: requirements.txt
          require-hashes: true
          
      - name: Run Safety check
        run: safety check --full-report
```

---

## A07:2021 – Authentication Failures

### Vulnerabilities Found
- [ ] Weak password policy
- [ ] No MFA implementation
- [ ] Session tokens not rotated
- [ ] No brute force protection

### Remediation
```python
# See security-audit/configs/secure_auth.py for full implementation

# MFA Implementation (Twilio Authy or similar)
from twilio.rest import Client

class MFA:
    def __init__(self):
        self.client = Client(account_sid, auth_token)
    
    def send_otp(self, phone: str) -> str:
        """Send OTP via SMS."""
        otp = secrets.randbelow(1000000)
        otp = f"{otp:06d}"
        
        self.client.messages.create(
            body=f"Your WALI verification code: {otp}",
            from_='+1234567890',
            to=phone
        )
        
        # Store hashed OTP with expiry
        store_otp(phone, otp, expiry=300)  # 5 minutes
        return otp

# Enforce MFA for admin users
@app.post("/api/admin/login")
@rate_limit(max_requests=5, window_seconds=300)
async def admin_login(credentials: LoginRequest):
    user = authenticate(credentials)
    
    if not user:
        log_security_event("login_failure", None, request.client.host, {})
        raise HTTPException(status_code=401)
    
    if user.role == "admin":
        # Require MFA for admin
        mfa.send_otp(user.phone)
        return {"mfa_required": True, "temp_token": create_temp_token(user)}
    
    return {"access_token": create_access_token({"sub": user.id})}
```

---

## A08:2021 – Software and Data Integrity Failures

### Remediation
```python
# Verify file uploads haven't been tampered
import hashlib

def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
    """Verify file SHA-256 hash."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash

# Sign webhooks
import hmac

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature from payment provider."""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

# Usage in webhook handler
@app.post("/webhooks/orange-money")
async def orange_money_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Orange-Signature')
    
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

---

## A09:2021 – Security Logging and Monitoring Failures

### Remediation
```python
# Configure structured logging
import json
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s'
)
logHandler.setFormatter(formatter)

security_logger = logging.getLogger('security')
security_logger.addHandler(logHandler)
security_logger.setLevel(logging.WARNING)

# Log all security events
def log_security_event(event_type, user_id, ip, details, severity='info'):
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip,
        'severity': severity,
        'details': details,
    }
    security_logger.warning(json.dumps(event))

# Send to SIEM (Splunk, ELK, Datadog)
def send_to_siem(event):
    requests.post(SIEM_ENDPOINT, json=event, headers={'Authorization': SIEM_TOKEN})
```

---

## A10:2021 – Server-Side Request Forgery (SSRF)

### Vulnerabilities Found
- [ ] No validation on outbound requests
- [ ] Internal services accessible via user input

### Remediation
```python
import ipaddress
import re
from urllib.parse import urlparse

class SSRFProtection:
    """Prevent Server-Side Request Forgery attacks."""
    
    # Block internal IP ranges
    BLOCKED_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),  # Link-local
        ipaddress.ip_network('0.0.0.0/8'),
    ]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Check if URL is safe to request."""
        try:
            parsed = urlparse(url)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Resolve hostname
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # Check IP if hostname is IP address
            try:
                ip = ipaddress.ip_address(hostname)
                for network in cls.BLOCKED_NETWORKS:
                    if ip in network:
                        return False
            except ValueError:
                # Not an IP, check for localhost bypasses
                if hostname in ['localhost', '127.0.0.1', '[::1]']:
                    return False
            
            return True
            
        except Exception:
            return False

# Usage
@app.post("/api/fetch-document")
async def fetch_document(url: str):
    if not SSRFProtection.validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    # Use timeout and size limits
    response = requests.get(url, timeout=10, max_redirects=3)
    return response.content
```

---

## Implementation Priority

### Critical (Fix Before Launch)
1. A01 - Access Control
2. A02 - Cryptographic Failures
3. A07 - Authentication Failures
4. A05 - Security Misconfiguration

### High (Fix Within 30 Days)
5. A03 - Injection
6. A09 - Logging/Monitoring
7. A04 - Insecure Design

### Medium (Fix Within 90 Days)
8. A08 - Integrity Failures
9. A10 - SSRF
10. A06 - Vulnerable Components

---

## Security Testing Checklist

### Pre-Production
- [ ] Run `dependency_audit.sh`
- [ ] Run OWASP ZAP scan
- [ ] Penetration test by third party
- [ ] Code review of auth modules
- [ ] Encryption key management review

### Post-Deployment
- [ ] Enable WAF (Cloudflare/AWS WAF)
- [ ] Set up SIEM alerts
- [ ] Weekly vulnerability scans
- [ ] Quarterly penetration tests
- [ ] Annual security audit
