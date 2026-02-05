"""
Shared JWT Authentication Middleware for Wali Python Services.

Usage:
    from shared.auth.jwt import verify_token, get_current_user
    
    @app.post("/protected", dependencies=[Depends(verify_token)])
    async def protected_route():
        ...
    
    # Or get user info:
    @app.post("/user-route")
    async def user_route(user: dict = Depends(get_current_user)):
        user_id = user["sub"]
        ...
"""
import os
import logging
from typing import Optional
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Security scheme
security = HTTPBearer(auto_error=True)


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


def create_token(user_id: str, role: str = "user", extra_claims: dict = None) -> str:
    """
    Create a new JWT token.
    
    Args:
        user_id: The user's unique identifier
        role: User role (e.g., 'user', 'admin')
        extra_claims: Additional claims to include
    
    Returns:
        Encoded JWT token
    """
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode
    
    Returns:
        Decoded token payload
    
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    FastAPI dependency to verify JWT token.
    
    Returns the raw token if valid.
    Raises 401 if invalid.
    
    Usage:
        @app.post("/endpoint", dependencies=[Depends(verify_token)])
    """
    token = credentials.credentials
    
    try:
        decode_token(token)  # Validate
        return token
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    FastAPI dependency to get current user from JWT.
    
    Returns the decoded token payload with user info.
    Raises 401 if invalid.
    
    Usage:
        @app.post("/endpoint")
        async def endpoint(user: dict = Depends(get_current_user)):
            user_id = user["sub"]
            role = user["role"]
    """
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        return payload
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    user: dict = Depends(get_current_user)
) -> dict:
    """
    FastAPI dependency to require admin role.
    
    Usage:
        @app.post("/admin-only", dependencies=[Depends(require_admin)])
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# Optional: For services that need to validate tokens from other services
def validate_service_token(token: str, required_service: Optional[str] = None) -> dict:
    """
    Validate a service-to-service token.
    
    Args:
        token: The JWT token
        required_service: If provided, validates the 'service' claim matches
    
    Returns:
        Decoded token payload
    
    Raises:
        AuthenticationError: If invalid or unauthorized
    """
    payload = decode_token(token)
    
    if required_service and payload.get("service") != required_service:
        raise AuthenticationError(f"Token not authorized for service: {required_service}")
    
    return payload
