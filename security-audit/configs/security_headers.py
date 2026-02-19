"""
Security Headers Middleware for WALI

Implements OWASP-recommended security headers for all API responses.
Add to each FastAPI service.
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    OWASP Reference:
    - https://owasp.org/www-project-secure-headers/
    - https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
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
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        
        # Strict Transport Security (HSTS)
        # Only enable in production with HTTPS
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Cache Control for sensitive endpoints
        if "/api/v1/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        
        return response


def setup_cors(app, allowed_origins=None):
    """
    Configure CORS with strict settings.
    
    NEVER use allow_origins=["*"] in production!
    """
    if allowed_origins is None:
        allowed_origins = [
            "https://wali.ci",
            "https://admin.wali.ci",
            "https://api.wali.ci",
            # Add staging environments
            "https://staging.wali.ci",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-API-Key",
        ],
        expose_headers=["X-Request-ID"],
        max_age=600,  # 10 minutes
    )


def add_security_middleware(app):
    """Add all security middleware to FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware added")
