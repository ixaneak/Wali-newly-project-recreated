"""
Security Dependencies for Admin API.

Rate limiting and authentication for admin endpoints.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.claims import Claim

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-min-32-chars-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting configuration
RATE_LIMIT_CLAIMS_PER_DAY = 5  # Max claims per artisan per day
RATE_LIMIT_WINDOW_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for JWT
security_bearer = HTTPBearer(auto_error=False)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)


class AdminUser:
    """Simple admin user model."""
    def __init__(self, id: str, email: str, role: str = "admin"):
        self.id = id
        self.email = email
        self.role = role
    
    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> AdminUser:
    """
    Validate JWT token and return admin user.
    
    This is a simplified version - in production you'd query the admin_users table.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        
        return AdminUser(id=user_id, email=email, role=role)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def require_admin(
    current_user: AdminUser = Depends(get_current_admin_user)
) -> AdminUser:
    """
    Dependency to require admin role.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_admin)])
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def check_claim_rate_limit(
    artisan_phone: str,
    db: AsyncSession
) -> bool:
    """
    Check if artisan has exceeded daily claim limit.
    
    Args:
        artisan_phone: Artisan's phone number (E.164 format)
        db: Database session
    
    Returns:
        True if rate limit OK, False if exceeded
    """
    try:
        # Count claims in last 24 hours
        one_day_ago = datetime.now(timezone.utc) - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        
        result = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.artisan_phone == artisan_phone,
                Claim.submitted_at >= one_day_ago
            )
        )
        claim_count = result.scalar()
        
        if claim_count >= RATE_LIMIT_CLAIMS_PER_DAY:
            logger.warning(
                f"RATE_LIMIT_EXCEEDED|"
                f"phone={artisan_phone}|"
                f"count={claim_count}|"
                f"limit={RATE_LIMIT_CLAIMS_PER_DAY}"
            )
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        # Fail open - allow claim if we can't check rate limit
        # (better than blocking legitimate claims due to DB error)
        return True


async def rate_limit_dependency(
    request: Request,
    artisan_phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    FastAPI dependency for rate limiting.
    
    Usage:
        @router.post("/claims")
        async def create_claim(
            request: Request,
            _: None = Depends(rate_limit_dependency),
            ...
        )
    """
    # Extract phone from request body or query param
    if not artisan_phone:
        # Try to get from request body
        try:
            body = await request.json()
            artisan_phone = body.get("artisan_phone")
        except:
            pass
    
    if not artisan_phone:
        raise HTTPException(
            status_code=400,
            detail="artisan_phone required for rate limiting"
        )
    
    if not await check_claim_rate_limit(artisan_phone, db):
        raise RateLimitExceeded(
            detail=f"Maximum {RATE_LIMIT_CLAIMS_PER_DAY} claims per {RATE_LIMIT_WINDOW_HOURS} hours exceeded"
        )


class RateLimitMiddleware:
    """
    Middleware for global rate limiting.
    
    Limits requests per IP address.
    """
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # In production, use Redis for distributed rate limiting
        self.requests = {}  # IP -> list of timestamps
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client IP
        client_ip = scope.get("client", ("unknown",))[0]
        
        # Check rate limit
        now = datetime.now(timezone.utc)
        if client_ip in self.requests:
            # Remove old requests outside window
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip]
                if (now - ts).total_seconds() < self.window_seconds
            ]
            
            if len(self.requests[client_ip]) >= self.max_requests:
                # Rate limit exceeded
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail": "Rate limit exceeded"}',
                })
                return
        
        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(now)
        
        await self.app(scope, receive, send)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data (must include "sub" for user ID)
        expires_delta: Token expiration time
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.
    
    Returns:
        Payload dict if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# Export
__all__ = [
    "get_current_admin_user",
    "require_admin",
    "check_claim_rate_limit",
    "rate_limit_dependency",
    "RateLimitMiddleware",
    "RateLimitExceeded",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "AdminUser",
]
