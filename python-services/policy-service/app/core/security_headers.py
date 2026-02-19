"""
Security Headers Middleware - CIMA Compliant

Implements OWASP-recommended security headers:
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Content-Security-Policy
- Referrer-Policy
- Permissions-Policy

CIMA Requirements:
- All financial data must be transmitted over HTTPS
- No mixed content allowed
- Secure cookie attributes required
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add comprehensive security headers to all responses.
    
    OWASP Reference:
    - https://owasp.org/www-project-secure-headers/
    - https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS (HTTP Strict Transport Security) - 1 year, include subdomains
        # CIMA Requirement: Enforce HTTPS for all financial transactions
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # X-Frame-Options - Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection - Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy - Mitigate XSS and data injection
        # Carefully configured for WALI's specific needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https://storage.googleapis.com https://firebasestorage.googleapis.com https://*.googleusercontent.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://*.googleapis.com https://*.firebaseio.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Permissions-Policy (formerly Feature-Policy) - Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(self), "
            "payment=(self), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        
        # Cache Control - Prevent caching of sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # X-Request-ID - For tracking and audit
        request_id = request.headers.get('X-Request-ID', '')
        if request_id:
            response.headers["X-Request-ID"] = request_id
        
        return response


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security audit logging.
    
    Logs all requests for compliance and security monitoring.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID if not present
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log security-relevant requests
        if self._should_log(request, response):
            self._log_request(request, response, duration, request_id)
        
        # Add request ID to response
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _should_log(self, request: Request, response: Response) -> bool:
        """Determine if request should be logged for security audit."""
        # Log all authentication attempts
        if '/auth' in request.url.path or '/login' in request.url.path:
            return True
        
        # Log admin actions
        if '/admin' in request.url.path:
            return True
        
        # Log errors (4xx, 5xx)
        if response.status_code >= 400:
            return True
        
        # Log SAR/compliance access
        if '/compliance' in request.url.path or '/sar' in request.url.path:
            return True
        
        return False
    
    def _log_request(self, request: Request, response: Response, duration: float, request_id: str):
        """Log request to security audit log."""
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
            'user_agent': user_agent[:200],  # Truncate long UA strings
        }
        
        # Log with appropriate level
        if response.status_code >= 500:
            logger.error(f"SECURITY_AUDIT: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"SECURITY_AUDIT: {log_data}")
        else:
            logger.info(f"SECURITY_AUDIT: {log_data}")


# Export middleware classes
__all__ = ['SecurityHeadersMiddleware', 'SecurityAuditMiddleware']
