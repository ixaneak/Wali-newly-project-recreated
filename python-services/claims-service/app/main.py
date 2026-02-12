"""
Wali Incident Report Service — FastAPI Application

Provides digital incident reporting technology to partner insurers.
Wali does NOT process insurance claims or make payouts.

NAF Code: 6201Z — Conseil en systèmes et logiciels informatiques
"""
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.error_handlers import register_exception_handlers
from app.routes import claims, photos, compliance
from app.core.security_headers import SecurityHeadersMiddleware
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

app = FastAPI(
    title="Wali Incident Report Service",
    description=(
        "B2B SaaS incident reporting technology for partner insurers. "
        "Wali is a software vendor (NAF 6201Z), NOT a claims processor."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

register_exception_handlers(app)

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security & CORS Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(compliance.router)


@app.head("/health", status_code=status.HTTP_200_OK)
@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def health_check(request: Request):
    """SaaS platform health check."""
    return {
        "status": "healthy",
        "service": "wali-incident-service",
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "is_claims_processor": False,
        "environment": settings.environment,
    }


@app.get("/")
def root():
    return {
        "service": "Wali Incident Report Service",
        "version": "2.0.0",
        "model": "B2B_SAAS",
        "docs": "/docs",
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Wali Incident Report Service (B2B SaaS)")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS origins: {settings.allowed_origins}")

    # Initialize Firebase Admin SDK
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized")
    except Exception as e:
        logger.warning(f"Firebase Admin SDK not available: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Wali Incident Report Service")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.environment == "development")
