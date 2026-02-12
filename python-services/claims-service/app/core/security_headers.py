from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS - 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Content-Security-Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https://storage.googleapis.com https://firebasestorage.googleapis.com; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com;"
        
        return response
