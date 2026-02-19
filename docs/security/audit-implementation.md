# WALI Security Audit Implementation

**Phase:** 4C - Comprehensive Security Assessment  
**Date:** 2026-02-18  
**Status:** Implementation Guide

---

## 📋 Executive Summary

This document implements the complete security audit phase for WALI, covering:
- Container security scanning
- OWASP Top 10 assessment
- Penetration testing
- Secrets audit
- SSL/TLS verification
- Incident response preparation

---

## PHASE 1: Container Security Scanning

### 1.1 Dockerfile Security Hardening

```dockerfile
# python-services/policy-service/Dockerfile.secure
FROM python:3.11-slim as builder

# Security: Run as non-root
RUN groupadd -r wali && useradd -r -g wali wali

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production image
FROM python:3.11-slim

# Security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r wali && useradd -r -g wali wali

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --chown=wali:wali app/ ./app/

# Switch to non-root user
USER wali

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Container Scanning Script

```bash
#!/bin/bash
# security-audit/scripts/container_scan.sh

set -e

echo "🔍 WALI Container Security Scan"
echo "================================"

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "Installing Trivy..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
fi

SERVICES=("policy-service" "claims-service" "payment-gateway")
SCAN_RESULTS_DIR="security-audit/reports/container-scans"
mkdir -p "$SCAN_RESULTS_DIR"

for service in "${SERVICES[@]}"; do
    echo ""
    echo "Scanning $service..."
    
    # Build image
    cd "python-services/$service"
    docker build -f Dockerfile.secure -t "wali-$service:scan" . 2>/dev/null || \
    docker build -t "wali-$service:scan" .
    cd - > /dev/null
    
    # Run Trivy scan
    trivy image \
        --severity HIGH,CRITICAL \
        --format json \
        --output "$SCAN_RESULTS_DIR/$service-scan.json" \
        "wali-$service:scan" 2>/dev/null || true
    
    # Check for critical vulnerabilities
    CRITICAL_COUNT=$(trivy image --severity CRITICAL "wali-$service:scan" 2>/dev/null | grep -c "CRITICAL" || echo "0")
    HIGH_COUNT=$(trivy image --severity HIGH "wali-$service:scan" 2>/dev/null | grep -c "HIGH" || echo "0")
    
    echo "  CRITICAL: $CRITICAL_COUNT"
    echo "  HIGH: $HIGH_COUNT"
    
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        echo "  ❌ FAILED: Critical vulnerabilities found!"
        exit 1
    fi
done

echo ""
echo "✅ Container scans complete"
echo "Reports saved to: $SCAN_RESULTS_DIR"
```

---

## PHASE 2: OWASP Top 10 Implementation

### 2.1 A01: Broken Access Control - Verification

```python
# app/core/access_control.py
from fastapi import Depends, HTTPException, Request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class AccessControl:
    """Centralized access control for all endpoints."""
    
    @staticmethod
    def verify_ownership(user_id: str, resource_user_id: str, admin_check: bool = False):
        """Verify user owns resource or is admin."""
        if user_id != resource_user_id and not admin_check:
            logger.warning(f"Access denied: {user_id} tried to access resource owned by {resource_user_id}")
            raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    @staticmethod
    def require_auth(endpoint_func):
        """Decorator to require authentication."""
        @wraps(endpoint_func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request or not hasattr(request.state, 'user'):
                raise HTTPException(status_code=401, detail="Authentication required")
            return await endpoint_func(*args, **kwargs)
        return wrapper

# Usage in routes
from app.core.access_control import AccessControl

@app.get("/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    policy = await get_policy_from_db(policy_id)
    
    # Verify ownership
    AccessControl.verify_ownership(
        user_id=current_user['id'],
        resource_user_id=policy.user_id,
        admin_check=current_user.get('is_admin', False)
    )
    
    return policy
```

### 2.2 A02: Cryptographic Failures - Verification

```python
# app/core/crypto_verification.py
import os
import jwt
from cryptography.fernet import Fernet

class CryptoVerification:
    """Verify cryptographic configurations."""
    
    @staticmethod
    def verify_jwt_secret():
        """Verify JWT secret meets security requirements."""
        secret = os.getenv('JWT_SECRET', '')
        
        if len(secret) < 32:
            raise ValueError(
                f"JWT_SECRET too short ({len(secret)} chars). "
                f"Must be at least 32 characters (256 bits). "
                f"Generate with: openssl rand -hex 32"
            )
        
        # Check for common weak secrets
        weak_patterns = ['secret', 'password', '123456', 'admin', 'wali']
        if any(pattern in secret.lower() for pattern in weak_patterns):
            raise ValueError("JWT_SECRET contains common weak pattern")
        
        return True
    
    @staticmethod
    def verify_encryption_key():
        """Verify data encryption key."""
        key = os.getenv('ENCRYPTION_KEY', '')
        
        try:
            # Validate Fernet key format
            Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")
        
        return True
    
    @staticmethod
    def get_secure_jwt_config():
        """Return secure JWT configuration."""
        return {
            'algorithms': ['HS256'],  # Only allow secure algorithms
            'options': {
                'require': ['exp', 'iat', 'sub'],
                'verify_exp': True,
                'verify_iat': True,
                'verify_signature': True,
            }
        }

# Run verification on startup
def verify_crypto_on_startup():
    """Verify all cryptographic configurations."""
    CryptoVerification.verify_jwt_secret()
    CryptoVerification.verify_encryption_key()
    print("✅ Cryptographic configuration verified")
```

### 2.3 A03: Injection Prevention - Verification

```python
# app/core/injection_prevention.py
import re
from typing import Any

class InjectionPrevention:
    """Prevent SQL, NoSQL, and command injection."""
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(;\s*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
    ]
    
    # Command injection patterns
    COMMAND_PATTERNS = [
        r"[;&|`]\s*\b(cat|ls|pwd|whoami|id|wget|curl|nc|netcat|python|bash|sh|cmd)\b",
        r"\$\([^)]+\)",
        r"`[^`]+`",
    ]
    
    @classmethod
    def sanitize_input(cls, value: str, max_length: int = 255) -> str:
        """Sanitize user input."""
        if not value:
            return value
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')
        
        # Truncate
        value = value[:max_length]
        
        return value.strip()
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection."""
        value_lower = value.lower()
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_lower):
                return True
        return False
    
    @classmethod
    def detect_command_injection(cls, value: str) -> bool:
        """Detect potential command injection."""
        for pattern in cls.COMMAND_PATTERNS:
            if re.search(pattern, value):
                return True
        return False
    
    @classmethod
    def validate_safe_string(cls, value: Any, field_name: str = "field") -> str:
        """Validate string is safe (no injection)."""
        if not isinstance(value, str):
            return str(value)
        
        if cls.detect_sql_injection(value):
            raise ValueError(f"Potential SQL injection detected in {field_name}")
        
        if cls.detect_command_injection(value):
            raise ValueError(f"Potential command injection detected in {field_name}")
        
        return cls.sanitize_input(value)

# SQLAlchemy safe query wrapper
def safe_query(db_session, query: str, params: tuple = ()):
    """Execute parameterized query safely."""
    # Verify no raw SQL injection
    for param in params:
        if InjectionPrevention.detect_sql_injection(str(param)):
            raise ValueError("Unsafe parameter detected")
    
    return db_session.execute(query, params)
```

### 2.4 A05: Security Misconfiguration - Middleware

```python
# app/core/security_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HTTPS only)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Prevent caching of sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Handle errors without leaking sensitive information."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            
            # Return generic error in production
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )
```

---

## PHASE 3: Penetration Testing Automation

```python
# security-audit/scripts/automated_pentest.py
#!/usr/bin/env python3
"""
Automated Penetration Testing for WALI
Tests OWASP Top 10 vulnerabilities
"""

import requests
import sys
import json
from typing import Dict, List

class WALIPenetrationTester:
    """Automated penetration testing suite."""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        self.results = []
    
    def test_sql_injection(self) -> Dict:
        """Test for SQL injection vulnerabilities."""
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND 1=1 --",
        ]
        
        vulnerable = False
        for payload in payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/policies?id={payload}",
                    timeout=5
                )
                
                # Check for SQL error indicators
                error_indicators = ['sql', 'mysql', 'postgresql', 'syntax error']
                if any(ind in response.text.lower() for ind in error_indicators):
                    vulnerable = True
                    break
                    
            except Exception:
                pass
        
        result = {
            'test': 'SQL Injection',
            'vulnerable': vulnerable,
            'severity': 'CRITICAL' if vulnerable else 'PASS',
        }
        self.results.append(result)
        return result
    
    def test_broken_auth(self) -> Dict:
        """Test for broken authentication."""
        # Test 1: Access without token
        try:
            response = self.session.get(f"{self.base_url}/api/policies/test123")
            no_auth_access = response.status_code == 200
        except:
            no_auth_access = False
        
        # Test 2: Weak JWT (if we have a test token)
        weak_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.test"
        try:
            response = self.session.get(
                f"{self.base_url}/api/policies/test",
                headers={'Authorization': f'Bearer {weak_token}'}
            )
            weak_token_accepted = response.status_code == 200
        except:
            weak_token_accepted = False
        
        vulnerable = no_auth_access or weak_token_accepted
        
        result = {
            'test': 'Broken Authentication',
            'vulnerable': vulnerable,
            'severity': 'CRITICAL' if vulnerable else 'PASS',
            'details': {
                'no_auth_access': no_auth_access,
                'weak_token_accepted': weak_token_accepted,
            }
        }
        self.results.append(result)
        return result
    
    def test_security_headers(self) -> Dict:
        """Test for security headers."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            required_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security',
            ]
            
            missing = [h for h in required_headers if h not in headers]
            
            result = {
                'test': 'Security Headers',
                'vulnerable': len(missing) > 0,
                'severity': 'HIGH' if missing else 'PASS',
                'details': {'missing_headers': missing}
            }
        except Exception as e:
            result = {
                'test': 'Security Headers',
                'vulnerable': True,
                'severity': 'ERROR',
                'details': str(e)
            }
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> Dict:
        """Generate penetration test report."""
        critical = sum(1 for r in self.results if r['severity'] == 'CRITICAL')
        high = sum(1 for r in self.results if r['severity'] == 'HIGH')
        passed = sum(1 for r in self.results if r['severity'] == 'PASS')
        
        return {
            'summary': {
                'total_tests': len(self.results),
                'critical': critical,
                'high': high,
                'passed': passed,
                'status': 'FAIL' if critical > 0 else ('WARNING' if high > 0 else 'PASS')
            },
            'details': self.results
        }

if __name__ == '__main__':
    tester = WALIPenetrationTester('https://api.wali.ci')
    
    print("Running penetration tests...")
    tester.test_sql_injection()
    tester.test_broken_auth()
    tester.test_security_headers()
    
    report = tester.generate_report()
    print(json.dumps(report, indent=2))
    
    sys.exit(0 if report['summary']['status'] == 'PASS' else 1)
```

---

## PHASE 4: Secrets Audit

```bash
#!/bin/bash
# security-audit/scripts/secrets_audit.sh

echo "🔐 WALI Secrets Audit"
echo "====================="

# Check for secrets in code
echo ""
echo "Checking for hardcoded secrets..."

PATTERNS=(
    "password\s*=\s*['\"][^'\"]+['\"]"
    "secret\s*=\s*['\"][^'\"]+['\"]"
    "api_key\s*=\s*['\"][^'\"]+['\"]"
    "AKIA[0-9A-Z]{16}"
    "sk_live_[a-zA-Z0-9]{24,}"
    "ghp_[a-zA-Z0-9]{36}"
)

FOUND=0
for pattern in "${PATTERNS[@]}"; do
    matches=$(grep -r "$pattern" python-services/ --include="*.py" 2>/dev/null | grep -v "getenv\|environ\|os.env\|example\|test" || true)
    if [ -n "$matches" ]; then
        echo "⚠️  Potential secret found:"
        echo "$matches"
        FOUND=$((FOUND + 1))
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "✅ No hardcoded secrets found in code"
else
    echo "❌ $FOUND potential secrets found - review immediately!"
fi

# Check Fly secrets
echo ""
echo "Checking Fly secrets configuration..."
fly secrets list --app wali-policy-service > /dev/null 2>&1 && echo "✅ Fly secrets configured" || echo "⚠️  Fly secrets not accessible"

# Check .env files
echo ""
echo "Checking .env files..."
if [ -f "python-services/policy-service/.env" ]; then
    if grep -q "SECRET\|PASSWORD\|KEY" python-services/policy-service/.env 2>/dev/null; then
        echo "⚠️  .env file contains sensitive values - ensure it's in .gitignore"
    fi
    echo "✅ .env file exists"
else
    echo "⚠️  No .env file found (may use Fly secrets directly)"
fi

echo ""
echo "Secrets audit complete"
```

---

## PHASE 5: Incident Response Runbook

```markdown
# SECURITY.md - Incident Response Runbook

## Emergency Contacts

| Role | Contact | Phone |
|------|---------|-------|
| Security Lead | security@wali.ci | +225 XX XX XX XX |
| CTO | cto@wali.ci | +225 XX XX XX XX |
| TRACFIN (Ivory Coast) | - | +225 XX XX XX XX |
| Fly.io Emergency | support@fly.io | - |

## Incident Severity Levels

### P1 - Critical (Immediate Response)
- Data breach (customer data exposed)
- Financial theft or fraud
- System completely down
- Ransomware attack

**Response Time:** 15 minutes  
**Actions:**
1. Isolate affected service immediately
2. Preserve all logs
3. Notify CTO and Security Lead
4. Begin forensic preservation

### P2 - High (1 Hour Response)
- Unauthorized access detected
- Vulnerability exploited
- Suspicious activity patterns

**Response Time:** 1 hour  
**Actions:**
1. Investigate scope
2. Implement containment
3. Document findings

### P3 - Medium (4 Hour Response)
- Failed attack attempts
- Minor policy violations
- Non-critical vulnerabilities

**Response Time:** 4 hours  

## Response Procedures

### 1. Immediate Containment

```bash
# Isolate affected service
fly scale count 0 --app wali-policy-service

# Or block at WAF level (if available)
# Block IP addresses if needed

# Preserve logs
fly logs --app wali-policy-service --recent > incident-$(date +%Y%m%d-%H%M).log
```

### 2. Forensic Preservation

```bash
# Database snapshot
fly pg backup create --app wali-db-prod

# Container images
docker save wali-policy-service:latest > incident-image-$(date +%Y%m%d).tar

# Save all environment variables (masked)
fly secrets list --app wali-policy-service > incident-secrets-$(date +%Y%m%d).txt
```

### 3. Notification Requirements

#### Internal (Immediate)
- [ ] Security Lead notified
- [ ] CTO notified
- [ ] Legal counsel consulted (if data breach)

#### Regulatory (Within 24 Hours)
- [ ] TRACFIN notified (financial crime suspicion)
- [ ] CIMA notified (insurance regulator)

#### Customers (Within 72 Hours)
- [ ] Affected customers notified
- [ ] Public disclosure (if required by law)

### 4. Recovery

```bash
# Rotate all secrets
fly secrets set JWT_SECRET=$(openssl rand -hex 32) --app wali-policy-service
fly secrets set DATABASE_URL="new-connection-string" --app wali-policy-service

# Redeploy with patched code
fly deploy --app wali-policy-service

# Verify health
fly status --app wali-policy-service
```

## Post-Incident Review

Within 48 hours of resolution:
1. Document timeline of events
2. Identify root cause
3. Implement preventive measures
4. Update security controls
5. Train team on lessons learned
```

---

## Sign-Off Checklist

Before Production Deployment:

- [ ] Container scans pass (no CRITICAL/HIGH vulnerabilities)
- [ ] All OWASP Top 10 mitigations tested
- [ ] JWT secrets 256+ bits, not in code
- [ ] SQL injection tested (parameterized queries only)
- [ ] Authorization bypass tested
- [ ] Rate limiting active on all endpoints
- [ ] Security headers present
- [ ] No secrets in git history
- [ ] SSL Grade A+
- [ ] Audit logging active
- [ ] Incident response runbook created
- [ ] Penetration test completed

**Security Engineer:** _________________ Date: _______  
**CTO:** _________________ Date: _______
