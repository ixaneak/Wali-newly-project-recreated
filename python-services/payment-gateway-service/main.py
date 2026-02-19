"""
Wali Payment Gateway Service — FastAPI Application with Security Hardening.

Microservice for handling mobile money payments with PCI-DSS aligned controls.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.security_headers import SecurityHeadersMiddleware, SecurityAuditMiddleware
from app.core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routes import webhooks

settings = get_settings()

# Create tables (for development convenience)
if engine:
    Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with security-focused configuration
app = FastAPI(
    title="Wali Payment Gateway Service",
    description="Microservice for handling mobile money payments with security controls",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═════════════════════════════════════════════════════════════════
# SECURITY MIDDLEWARE
# ═════════════════════════════════════════════════════════════════

# 1. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Security Audit Logging
app.add_middleware(SecurityAuditMiddleware)

# 3. Rate Limiting
app.add_middleware(SlowAPIMiddleware)

# 4. CORS - Strict configuration
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://wali.ci",
    "https://app.wali.ci",
    "https://admin.wali.ci",
]

if settings.environment == "staging":
    allowed_origins.extend([
        "https://staging.wali.ci",
        "https://staging-app.wali.ci",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Limited methods for payments
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-API-Key",
        "Accept",
        "Origin",
    ],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# ═════════════════════════════════════════════════════════════════
# ROUTE REGISTRATION
# ═════════════════════════════════════════════════════════════════

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Mock Endpoints (Dev/Test only)
if settings.environment != "production":
    from app.routes import mock
    app.include_router(mock.router, prefix="/test", tags=["mock"])


# ═════════════════════════════════════════════════════════════════
# HEALTH & MONITORING
# ═════════════════════════════════════════════════════════════════

@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "payment-gateway-service",
        "environment": settings.environment,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


@app.get("/")
def root():
    return {
        "service": "Wali Payment Gateway Service",
        "version": "1.0.0",
        "environment": settings.environment,
    }


# ═════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - no sensitive data in production."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Payment service error: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True
    )
    
    # Never expose internal errors in production for payments
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Payment processing error",
                "request_id": request_id,
                "message": "Please try again or contact support"
            }
        )
    else:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "request_id": request_id,
                "traceback": traceback.format_exc().split("\n"),
            }
        )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 60)
    logger.info("WALI Payment Gateway Service Starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("WALI Payment Gateway Service Shutting Down")
