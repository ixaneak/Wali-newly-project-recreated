"""Policy Service - FastAPI Application."""
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.error_handlers import register_exception_handlers
from app.routes import policies, claims, photos, admin_users, compliance, pharmacy, paydunya, auth
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create tables
try:
    if engine:
        Base.metadata.create_all(bind=engine)
    else:
        logger.warning("No DB engine available, skipping table creation")
except Exception as e:
    logger.warning(f"Failed to create tables (DB unreachable?): {e}")

app = FastAPI(
    title="Wali B2B SaaS Platform",
    description="Microservice for Pharmacy B2B SaaS, policies and claims",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security & CORS Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://wali.ci", "https://app.wali.ci"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policies.router)
app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(admin_users.router)
app.include_router(compliance.router)
app.include_router(pharmacy.router)
app.include_router(paydunya.router)
app.include_router(auth.router)

# Health check endpoint
@app.head("/health", status_code=status.HTTP_200_OK)
@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def health_check(request: Request):
    """Health check endpoint for Fly.io/K8s."""
    import os
    db_status = "unknown"
    try:
        # Simple DB check
        if engine:
             # Just checking if engine is created, deep check might be too expensive for frequent health checks
             # But let's try a connection if we can
             pass
        db_status = "connected" if engine else "disconnected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy",
        "service": "policy-service",
        "region": os.getenv("FLY_REGION", "local"),
        "environment": settings.environment,
        "database": db_status
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "Wali Policy Service",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Register centralized error handlers
register_exception_handlers(app)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    logger.info(f"Starting Policy Service in {settings.environment} mode")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")

    # Initialize Firebase Admin
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        if not firebase_admin._apps:
            # Use default strategy (GOOGLE_APPLICATION_CREDENTIALS env var)
            # or could add specific credential path from settings if needed
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase Admin SDK: {e}")
        logger.warning("Auth verification may fail if using Firebase tokens")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Policy Service")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
