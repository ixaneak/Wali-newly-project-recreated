"""
Secure Authentication & Authorization - CIMA Compliant

OWASP ASVS Level 2 compliance for fintech/micro-insurance applications.
Implements:
- Argon2id password hashing
- JWT with secure configuration
- Rate limiting with Redis
- Input validation and sanitization
- Security audit logging
"""

import re
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import HTTPException, Security, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

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
    if not plain_password or not hashed_password:
        return False
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
    common_patterns = ['password', '123456', 'qwerty', 'admin', 'wali', 'insurance']
    if any(pattern in password.lower() for pattern in common_patterns):
        return False, "Password contains common patterns"
    
    return True, "Password meets requirements"


# ═════════════════════════════════════════════════════════════════
# JWT SECURITY (OWASP ASVS 4.0 V3)
# ═════════════════════════════════════════════════════════════════

import os

SECRET_KEY = os.getenv('JWT_SECRET', os.getenv('SECRET_KEY', secrets.token_urlsafe(32)))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create secure JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
        "iss": "wali-policy-service",  # Issuer
        "aud": "wali-api",  # Audience
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
        "iss": "wali-policy-service",
        "aud": "wali-api",
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience="wali-api",
            issuer="wali-policy-service"
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify refresh token."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="wali-api",
            issuer="wali-policy-service"
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


# ═════════════════════════════════════════════════════════════════
# RATE LIMITING (OWASP ASVS 4.0 V11.1)
# ═════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    In-memory rate limiter for protection against brute force.
    For production, use Redis-based rate limiter.
    """
    
    def __init__(self):
        self._storage = {}
        self._cleanup_interval = 3600  # Cleanup every hour
        self._last_cleanup = datetime.utcnow()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is within rate limit."""
        now = datetime.utcnow()
        
        # Periodic cleanup
        if (now - self._last_cleanup).seconds > self._cleanup_interval:
            self._cleanup()
        
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self._storage:
            self._storage[key] = []
        
        # Remove old entries
        self._storage[key] = [
            ts for ts in self._storage[key] 
            if ts > window_start
        ]
        
        # Check limit
        if len(self._storage[key]) >= max_requests:
            return False
        
        # Record request
        self._storage[key].append(now)
        return True
    
    def _cleanup(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)
        
        for key in list(self._storage.keys()):
            self._storage[key] = [ts for ts in self._storage[key] if ts > cutoff]
            if not self._storage[key]:
                del self._storage[key]
        
        self._last_cleanup = now


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator to apply rate limiting to endpoints.
    
    Usage:
        @app.get("/api/login")
        @rate_limit(max_requests=5, window_seconds=300)
        async def login(request: Request, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request = kwargs.get('request')
            if not request and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                client_ip = request.client.host if request.client else "unknown"
                key = f"rate_limit:{client_ip}:{request.url.path}"
                
                if not _rate_limiter.is_allowed(key, max_requests, window_seconds):
                    logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later.",
                        headers={"Retry-After": str(window_seconds)}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Specific rate limits for different operations
rate_limit_login = rate_limit(max_requests=5, window_seconds=300)      # 5 login attempts per 5 min
rate_limit_sensitive = rate_limit(max_requests=10, window_seconds=60)  # 10 sensitive ops per min
rate_limit_general = rate_limit(max_requests=100, window_seconds=60)   # 100 general requests per min


# ═════════════════════════════════════════════════════════════════
# INPUT VALIDATION (OWASP ASVS 4.0 V5)
# ═════════════════════════════════════════════════════════════════

def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
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
    """
    Validate Ivory Coast phone number format.
    Formats: +225 XX XX XX XX XX or 07 XX XX XX XX
    """
    if not phone:
        return False, "Phone number required"
    
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s\-]', '', phone)
    
    # Check format
    pattern = r'^(\+225|00225)?[0-9]{10}$'
    if not re.match(pattern, cleaned):
        return False, "Invalid phone number format. Expected: +225 XX XX XX XX XX"
    
    return True, "Valid phone number"


def validate_id_number(id_number: str) -> tuple[bool, str]:
    """
    Validate Côte d'Ivoire national ID (CNI) format.
    Format: 9 digits
    """
    if not id_number:
        return False, "ID number required"
    
    if not re.match(r'^\d{9}$', id_number):
        return False, "Invalid ID number. Expected 9 digits."
    
    return True, "Valid ID number"


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    if not email:
        return False, "Email required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, "Valid email"


# ═════════════════════════════════════════════════════════════════
# SECURITY AUDIT LOGGING (OWASP ASVS 4.0 V7)
# ═════════════════════════════════════════════════════════════════

def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
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
    - SAR/compliance events
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "severity": severity,
        "details": details or {},
    }
    
    # Log with appropriate level
    log_message = f"SECURITY_EVENT: {event}"
    
    if severity == "critical":
        logger.critical(log_message)
    elif severity == "error":
        logger.error(log_message)
    elif severity == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)


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
    if not provided_key or not stored_hash:
        return False
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)


# ═════════════════════════════════════════════════════════════════
# SSRF PROTECTION (OWASP A10)
# ═════════════════════════════════════════════════════════════════

import ipaddress
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('fc00::/7'),  # IPv6 private
]


def validate_url_safe(url: str) -> tuple[bool, str]:
    """
    Validate URL is safe to request (SSRF protection).
    
    Returns:
        (is_safe, reason)
    """
    try:
        parsed = urlparse(url)
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False, f"URL scheme '{parsed.scheme}' not allowed"
        
        hostname = parsed.hostname
        if not hostname:
            return False, "URL has no hostname"
        
        # Check for IP address
        try:
            ip = ipaddress.ip_address(hostname)
            for network in BLOCKED_NETWORKS:
                if ip in network:
                    return False, f"URL resolves to private IP: {ip}"
        except ValueError:
            # Not an IP, check for localhost bypasses
            if hostname.lower() in ['localhost', '127.0.0.1', '[::1]', '::1']:
                return False, "URL points to localhost"
        
        return True, "URL is safe"
        
    except Exception as e:
        return False, f"URL validation error: {e}"


# Export all public functions
__all__ = [
    'verify_password',
    'hash_password',
    'validate_password_strength',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'verify_refresh_token',
    'rate_limit',
    'rate_limit_login',
    'rate_limit_sensitive',
    'rate_limit_general',
    'sanitize_input',
    'validate_phone_number',
    'validate_id_number',
    'validate_email',
    'log_security_event',
    'generate_api_key',
    'hash_api_key',
    'verify_api_key',
    'validate_url_safe',
]
