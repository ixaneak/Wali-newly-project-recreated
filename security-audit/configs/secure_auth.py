"""
Secure Authentication & Authorization

OWASP ASVS Level 2 compliance for fintech applications.
"""

import re
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import logging

from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════
# PASSWORD SECURITY (OWASP ASVS 4.0 V2.1)
# ═════════════════════════════════════════════════════════════════

pwd_context = CryptContext(
    schemes=["argon2"],  # Argon2id recommended by OWASP
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,  # 64MB
    argon2__parallelism=4,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password using Argon2."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets OWASP requirements.
    
    Requirements:
    - Min 12 characters
    - At least 1 uppercase, 1 lowercase, 1 digit, 1 special char
    - No common patterns
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = ['password', '123456', 'qwerty', 'admin', 'wali']
    if any(pattern in password.lower() for pattern in common_patterns):
        return False, "Password contains common patterns"
    
    return True, "Password meets requirements"


# ═════════════════════════════════════════════════════════════════
# JWT SECURITY (OWASP ASVS 4.0 V3)
# ═════════════════════════════════════════════════════════════════

# Security settings
SECRET_KEY = secrets.token_urlsafe(32)  # Generate secure secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create secure JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ═════════════════════════════════════════════════════════════════
# RATE LIMITING (OWASP ASVS 4.0 V11.1)
# ═════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Redis-based rate limiter.
    
    Protects against brute force and DoS attacks.
    """
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum allowed requests
            window_seconds: Time window in seconds
        """
        current = self.redis.get(key)
        
        if current is None:
            # First request
            self.redis.setex(key, window_seconds, 1)
            return True
        
        current = int(current)
        if current >= max_requests:
            return False
        
        self.redis.incr(key)
        return True
    
    def get_remaining(self, key: str, max_requests: int) -> int:
        """Get remaining requests for key."""
        current = self.redis.get(key)
        if current is None:
            return max_requests
        return max(0, max_requests - int(current))


# Global rate limiter instance
rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(redis_url: str):
    """Initialize rate limiter with Redis."""
    global rate_limiter
    rate_limiter = RateLimiter(redis_url)


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator to apply rate limiting to endpoints.
    
    Usage:
        @app.get("/api/login")
        @rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
        async def login(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if rate_limiter is None:
                logger.warning("Rate limiter not initialized")
                return await func(request, *args, **kwargs)
            
            # Use IP + endpoint as key
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}:{request.url.path}"
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining(key, max_requests)
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again later.",
                    headers={"Retry-After": str(window_seconds)}
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# ═════════════════════════════════════════════════════════════════
# INPUT VALIDATION (OWASP ASVS 4.0 V5)
# ═════════════════════════════════════════════════════════════════

def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    - Removes null bytes
    - Truncates to max length
    - Strips dangerous characters
    """
    if not value:
        return ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newlines/tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')
    
    # Truncate
    value = value[:max_length]
    
    return value.strip()


def validate_phone_number(phone: str) -> tuple[bool, str]:
    """Validate Ivory Coast phone number format."""
    # Ivory Coast format: +225 XX XX XX XX XX or 07 XX XX XX XX
    pattern = r'^(\+225|00225)?[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    
    if not re.match(pattern, phone):
        return False, "Invalid phone number format. Expected: +225 XX XX XX XX XX"
    
    return True, "Valid phone number"


def validate_id_number(id_number: str) -> tuple[bool, str]:
    """Validate national ID number format."""
    # Côte d'Ivoire CNI format: 9 digits
    if not re.match(r'^\d{9}$', id_number):
        return False, "Invalid ID number. Expected 9 digits."
    
    return True, "Valid ID number"


# ═════════════════════════════════════════════════════════════════
# AUDIT LOGGING (OWASP ASVS 4.0 V7)
# ═════════════════════════════════════════════════════════════════

def log_security_event(
    event_type: str,
    user_id: Optional[str],
    ip_address: Optional[str],
    details: Dict[str, Any],
    severity: str = "info"
):
    """
    Log security events for audit trail.
    
    Events to log:
    - Login attempts (success/failure)
    - Password changes
    - Permission changes
    - Sensitive data access
    - Admin actions
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "severity": severity,
        "details": details,
    }
    
    # Log to structured logger
    logger.warning(f"SECURITY_EVENT: {event}")
    
    # In production: Send to SIEM (Splunk, ELK, etc.)


# ═════════════════════════════════════════════════════════════════
# SECURE COOKIES (OWASP ASVS 4.0 V3.4)
# ═════════════════════════════════════════════════════════════════

def get_secure_cookie_settings():
    """Get secure cookie settings for production."""
    return {
        "httponly": True,
        "secure": True,  # Only send over HTTPS
        "samesite": "strict",
        "max_age": 3600,  # 1 hour
    }


# ═════════════════════════════════════════════════════════════════
# API KEY SECURITY
# ═════════════════════════════════════════════════════════════════

def generate_api_key() -> str:
    """Generate secure API key."""
    return f"wali_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key against stored hash."""
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)
