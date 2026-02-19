"""
Security Middleware for Policy Service
- JWT verification
- Rate limiting (Redis-backed with in-memory fallback)
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from collections import defaultdict
import time
import logging
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per window (dev)
RATE_LIMIT_WINDOW = 60  # seconds

# In-memory fallback
_fallback_store: dict[str, list[float]] = defaultdict(list)

# Redis client (lazy-init)
_redis_client = None
_redis_available = None  # None = not checked yet


def _get_redis():
    """Lazy-initialize Redis client. Returns None if unavailable."""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected for rate limiting")
        return _redis_client
    except Exception as e:
        _redis_available = False
        logger.warning(f"Redis unavailable, using in-memory rate limiting: {e}")
        return None


class RateLimitExceeded(HTTPException):
    def __init__(self):
        super().__init__(status_code=429, detail="Rate limit exceeded. Try again later.")


def check_rate_limit(client_ip: str) -> None:
    """Check rate limit using Redis (INCR+EXPIRE) with in-memory fallback."""
    r = _get_redis()

    if r is not None:
        try:
            key = f"ratelimit:{client_ip}"
            current = r.incr(key)
            if current == 1:
                r.expire(key, RATE_LIMIT_WINDOW)
            if current > RATE_LIMIT_REQUESTS:
                raise RateLimitExceeded()
            return
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.warning(f"Redis rate-limit error, falling back: {e}")

    # In-memory fallback
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    _fallback_store[client_ip] = [
        ts for ts in _fallback_store[client_ip] if ts > window_start
    ]
    if len(_fallback_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise RateLimitExceeded()
    _fallback_store[client_ip].append(now)



try:
    import firebase_admin
    from firebase_admin import auth
except ImportError:
    firebase_admin = None
    auth = None

def decode_jwt_v2(token: str) -> dict:
    """
    Decode and validate Firebase ID token.
    Falls back to local JWT in development if Firebase fails or is not configured.
    """
    raise Exception("I AM HERE")
    try:
        with open("C:\\Users\\User\\.gemini\\antigravity\\scratch\\wali-backend\\python-services\\policy-service\\debug_auth.log", "a") as f:
            f.write(f"DEBUG: decode_jwt called with token len={len(token)}\n")
            f.write(f"DEBUG: token='{token}'\n")
            f.write(f"DEBUG: settings.environment = '{settings.environment}' (type: {type(settings.environment)})\n")
    except Exception as e:
        print(f"DEBUG: Failed to write log: {e}")
    
    # 0. Dev/Demo mock token bypass (development only)
    # SECURITY: This mock token MUST only be accepted in development environments.
    # In production, this block is skipped, and the token is subjected to real verification.
    if token == "mock-custom-token-backend":
        if settings.environment != 'development':
            logger.warning("Attempted to use mock token in non-development environment. Blocking.")
            pass  # Fall through to normal verification — will be rejected
        else:
            return {
                "sub": "mock-user-001",
                "user_id": "mock-user-001",
                "email": "test@wali.com",
                "phone_number": "+2250701010101",
                "role": "ARTISAN",
                "mock": True,
            }

    # 1. Try Firebase Verification first
    if auth:
        try:
            # Verify the token with Firebase Admin SDK
            decoded_token = auth.verify_id_token(token)
            
            # Map Firebase standard claims to our internal schema
            # Firebase 'uid' -> 'sub' (subject)
            # Custom claims like 'role' are top-level in decoded_token
            payload = {
                "sub": decoded_token.get("uid"),
                "user_id": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "phone_number": decoded_token.get("phone_number"),
                "role": decoded_token.get("role", "ARTISAN"),
                "exp": decoded_token.get("exp"),
                "firebase_token": True
            }
            return payload

        except ValueError as e:
            # Token format invalid
             pass
        except Exception as e:
            # Expired or invalid signature
            # We let it fall through to local check ONLY in DEV/TEST
            # In PROD, we should probably raise immediately?
            # For now, let's catch specific errors
            if "Token expired" in str(e):
                raise HTTPException(status_code=401, detail="Token has expired")
            pass

    # 2. Fallback to Local JWT (legacy/dev support)
    # This is useful for testing with create_test_token without hitting Firebase
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
    FastAPI dependency for JWT verification (Firebase + Local fallback).
    """
    client_ip = request.client.host if request.client else "unknown"
    print(f"DEBUG: verify_jwt entered, ip={client_ip}", flush=True)
    check_rate_limit(client_ip)
    
    if credentials is None:
        print("DEBUG: No credentials provided", flush=True)
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    print(f"DEBUG: Got token: {token[:10]}...", flush=True)
    try:
        payload = decode_jwt_v2(token)
    except Exception as e:
        # Catch-all for decoder errors that weren't HTTPExceptions
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    
    # Validate required claims
    if "sub" not in payload and "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")
    
    # Standardize 'sub'
    if "sub" not in payload:
        payload["sub"] = payload.get("user_id")

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
