"""
Wali Incident Report Service — FastAPI Application with Full Security Hardening

Provides digital incident reporting technology to partner insurers.
Wali does NOT process insurance claims or make payouts.

NAF Code: 6201Z — Conseil en systèmes et logiciels informatiques
"""
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.error_handlers import register_exception_handlers
from app.routes import claims, photos, compliance
from app.core.security_headers import SecurityHeadersMiddleware, SecurityAuditMiddleware
from app.core.secure_auth import log_security_event
from app.core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import app.models.stubs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize FastAPI with security-focused configuration
app = FastAPI(
    title="Wali Incident Report Service",
    description=(
        "CIMA-compliant B2B SaaS incident reporting technology for partner insurers. "
        "Wali is a software vendor (NAF 6201Z), NOT a claims processor."
    ),
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

register_exception_handlers(app)

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═════════════════════════════════════════════════════════════════
# SECURITY MIDDLEWARE (CIMA Compliant)
# ═════════════════════════════════════════════════════════════════

# 1. Security Headers (OWASP recommended)
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
    "https://www.wali.ci",
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
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

app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(compliance.router)

logger.info("All routes registered successfully")


@app.head("/health", status_code=status.HTTP_200_OK)
@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
def health_check(request: Request):
    """SaaS platform health check with security headers."""
    db_status = "unknown"
    try:
        if engine:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
        logger.error(f"Health check DB error: {e}")
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "wali-incident-service",
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "is_claims_processor": False,
        "environment": settings.environment,
        "database": db_status,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


@app.get("/")
def root():
    return {
        "service": "Wali Incident Report Service",
        "version": "2.0.0",
        "model": "B2B_SAAS",
        "status": "operational",
        "documentation": "/docs" if settings.environment != "production" else None,
        "health": "/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - no stack traces in production."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )
    
    log_security_event(
        event_type="unhandled_exception",
        ip_address=request.client.host if request.client else None,
        details={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "request_id": request_id,
        },
        severity="error"
    )
    
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
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
    logger.info("=" * 60)
    logger.info("WALI Incident Report Service Starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Region: {os.getenv('FLY_REGION', 'local')}")
    logger.info("=" * 60)
    
    # Log security configuration
    log_security_event(
        event_type="service_startup",
        details={
            "environment": settings.environment,
            "region": os.getenv("FLY_REGION", "local"),
            "version": "2.0.0",
            "service": "claims-service",
        },
        severity="info"
    )

    # Initialize Firebase Admin SDK
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized")
            else:
                logger.warning("Firebase credentials not found, running without Firebase")
    except Exception as e:
        logger.warning(f"Firebase initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("WALI Incident Report Service Shutting Down")
    
    log_security_event(
        event_type="service_shutdown",
        details={
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "service": "claims-service",
        },
        severity="info"
    )
