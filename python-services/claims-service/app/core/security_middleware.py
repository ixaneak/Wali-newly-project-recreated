"""
Security Middleware for Claims Service
- JWT verification
- Rate limiting (5 requests/minute per IP)
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from collections import defaultdict
import time
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

# Rate limiting storage (in-memory, use Redis in production)
rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW = 60  # seconds


class RateLimitExceeded(HTTPException):
    def __init__(self):
        super().__init__(status_code=429, detail="Rate limit exceeded. Try again later.")


def check_rate_limit(client_ip: str) -> None:
    """Check if client has exceeded rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        ts for ts in rate_limit_store[client_ip] if ts > window_start
    ]
    
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise RateLimitExceeded()
    
    rate_limit_store[client_ip].append(now)


def decode_jwt(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    FastAPI dependency for JWT verification with rate limiting.
    
    Usage:
        @app.post("/protected", dependencies=[Depends(verify_jwt)])
        async def protected_endpoint(): pass
        
    Or to access user data:
        @app.post("/protected")
        async def protected_endpoint(user: dict = Depends(verify_jwt)): pass
    """
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = decode_jwt(token)
    
    # Validate required claims
    if "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")
    
    return payload


async def verify_admin(user: dict = Depends(verify_jwt)) -> dict:
    """
    Verify that the authenticated user has admin privileges.
    
    Usage:
        @app.post("/admin-only", dependencies=[Depends(verify_admin)])
        async def admin_endpoint(): pass
    """
    role = user.get("role", "")
    if role.upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def create_test_token(user_id: str, role: str = "ARTISAN", expires_minutes: int = 30) -> str:
    """Create a test JWT token (for development/testing only)."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
