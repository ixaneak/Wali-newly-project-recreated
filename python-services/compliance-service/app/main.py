"""
Wali Compliance Service — FastAPI Application with Security Hardening.

B2B SaaS platform compliance, reporting, and audit trails.
Wali is a software vendor (NAF 6201Z), NOT an insurer or broker.
"""
from fastapi import FastAPI, status, Request
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

from app.routes import compliance, dashboard
from app.models.financial_event import FinancialEvent
from app.models.tax_exemption import TaxExemptionTracking

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize FastAPI with security-focused configuration
app = FastAPI(
    title="Wali Compliance Service",
    description=(
        "B2B SaaS platform compliance and audit trails. "
        "Wali is a software vendor (NAF 6201Z), NOT an insurer."
    ),
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

# ═════════════════════════════════════════════════════════════════
# ROUTE REGISTRATION
# ═════════════════════════════════════════════════════════════════

app.include_router(compliance.router)
app.include_router(dashboard.router)


# ═════════════════════════════════════════════════════════════════
# HEALTH & MONITORING ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    """Health check endpoint."""
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
        "service": "wali-compliance-service",
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "is_insurer": False,
        "database": db_status,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


@app.get("/")
def root():
    return {
        "service": "Wali Compliance Service",
        "version": "2.0.0",
        "model": "B2B_SAAS",
    }


# ═════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - no stack traces in production."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True
    )
    
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": request_id}
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
    logger.info("WALI Compliance Service Starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("WALI Compliance Service Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
