"""
Security Headers Middleware for Payment Gateway Service.

OWASP-recommended security headers for payment processing endpoints.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS (HTTP Strict Transport Security) - 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # X-Frame-Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy - Stricter for payments
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Permissions-Policy - Restrict all for payments
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        
        # Never cache payment endpoints
        if "/webhooks" in request.url.path or "/payment" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for security audit logging of payment operations."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log all payment-related requests
        if self._should_log(request, response):
            self._log_request(request, response, duration, request_id)
        
        response.headers["X-Request-ID"] = request_id
        return response
    
    def _should_log(self, request: Request, response: Response) -> bool:
        # Log all webhook calls
        if '/webhooks' in request.url.path:
            return True
        # Log all payment operations
        if '/payment' in request.url.path:
            return True
        # Log errors
        if response.status_code >= 400:
            return True
        return False
    
    def _log_request(self, request: Request, response: Response, duration: float, request_id: str):
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')
        
        log_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'client_ip': client_ip,
            'user_agent': user_agent[:200],
        }
        
        if response.status_code >= 500:
            logger.error(f"PAYMENT_AUDIT: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"PAYMENT_AUDIT: {log_data}")
        else:
            logger.info(f"PAYMENT_AUDIT: {log_data}")


__all__ = ['SecurityHeadersMiddleware', 'SecurityAuditMiddleware']
