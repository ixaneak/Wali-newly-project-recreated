"""Policy Service - FastAPI Application with Full Security Hardening."""
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time

# Configure logging with structured format
# Configure logging with structured format (ARTCI compliant JSON)
from app.core.logging import setup_structured_logging
setup_structured_logging()
logger = logging.getLogger(__name__)

# Initialize Sentry
from app.core.sentry import init_sentry
init_sentry()

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.error_handlers import register_exception_handlers
from app.routes import policies, claims, photos, admin_users, compliance, pharmacy, paydunya, auth, sar as sar_routes, analytics, admin_auth, mfa
from app.api import ussd, legal, health
from app.whatsapp.webhook_handler import router as whatsapp_router, init_webhook_handler
from app.whatsapp.state_machine import StateMachine
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.image_processor import ImageProcessor
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware, SecurityAuditMiddleware
from app.core.secure_auth import log_security_event
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

settings = get_settings()

# Create tables
try:
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    else:
        logger.warning("No DB engine available, skipping table creation")
except Exception as e:
    logger.warning(f"Failed to create tables (DB unreachable?): {e}")

# Initialize FastAPI with security-focused configuration
app = FastAPI(
    title="Wali B2B SaaS Platform",
    description="CIMA-compliant micro-insurance platform for pharmacy B2B SaaS",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

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

# Add staging origins if in staging environment
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
    max_age=600,  # 10 minutes
)

# ═════════════════════════════════════════════════════════════════
# ROUTE REGISTRATION
# ═════════════════════════════════════════════════════════════════

app.include_router(policies.router)
app.include_router(policies.policies_router)
app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(admin_users.router)
app.include_router(compliance.router)
app.include_router(pharmacy.router)
app.include_router(paydunya.router)
app.include_router(auth.router)
app.include_router(sar_routes.router)
app.include_router(analytics.router)
app.include_router(admin_auth.router)
app.include_router(mfa.router)
app.include_router(whatsapp_router)
app.include_router(ussd.router)
app.include_router(legal.router)
app.include_router(health.router)

logger.info("All routes registered successfully")

# ═════════════════════════════════════════════════════════════════
# WHATSAPP SERVICE INITIALIZATION
# ═════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def init_whatsapp_service():
    """Initialize WhatsApp service on startup."""
    try:
        # Get configuration from environment
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        app_secret = os.getenv("WHATSAPP_APP_SECRET")
        
        if all([phone_number_id, access_token]):
            # Initialize components
            state_machine = StateMachine()
            
            client = WhatsAppClient(
                phone_number_id=phone_number_id,
                access_token=access_token,
                app_secret=app_secret
            )
            
            image_processor = ImageProcessor()
            
            # Initialize webhook handler
            init_webhook_handler(state_machine, client, image_processor)
            
            logger.info("WhatsApp service initialized successfully")
        else:
            logger.warning("WhatsApp credentials not configured, skipping initialization")
            
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp service: {e}")

# ═════════════════════════════════════════════════════════════════
# HEALTH & MONITORING ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@app.head("/health", status_code=status.HTTP_200_OK)
@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")  # Higher limit for health checks
def health_check(request: Request):
    """Health check endpoint for Fly.io/K8s."""
    db_status = "unknown"
    try:
        if engine:
            # Simple connection test
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
        "service": "policy-service",
        "region": os.getenv("FLY_REGION", "local"),
        "environment": settings.environment,
        "database": db_status,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


@app.get("/health/detailed")
@limiter.limit("10/minute")
def health_check_detailed(request: Request):
    """Detailed health check with security metrics."""
    # Database check
    db_status = "unknown"
    db_latency_ms = 0
    try:
        from sqlalchemy import text
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - start) * 1000, 2)
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    # Memory usage (approximate)
    import psutil
    memory = psutil.virtual_memory()
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "policy-service",
        "version": "2.0.0",
        "environment": settings.environment,
        "region": os.getenv("FLY_REGION", "local"),
        "checks": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms,
            },
            "memory": {
                "percent": memory.percent,
                "available_mb": memory.available // (1024 * 1024),
            },
        },
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


@app.get("/")
def root():
    """Root endpoint - redirect to health."""
    return {
        "service": "Wali Policy Service",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/docs" if settings.environment != "production" else None,
        "health": "/health",
    }


# ═════════════════════════════════════════════════════════════════
# ERROR HANDLERS (Security-focused)
# ═════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - no stack traces in production."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Always log the full error
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )
    
    # Log security event for errors
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
    
    # Return safe error response
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
            }
        )
    else:
        # Development - include error details
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "request_id": request_id,
                "traceback": traceback.format_exc().split("\n"),
            }
        )


# ═════════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN EVENTS
# ═════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 60)
    logger.info("WALI Policy Service Starting")
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
        },
        severity="info"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("WALI Policy Service Shutting Down")
    
    log_security_event(
        event_type="service_shutdown",
        details={"timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
        severity="info"
    )


# Register exception handlers
register_exception_handlers(app)
