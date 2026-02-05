"""Policy Service - FastAPI Application."""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.error_handlers import register_exception_handlers
from app.routes import policies, claims, photos, admin_users, compliance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Failed to create tables (DB unreachable?): {e}")

app = FastAPI(
    title="Wali Policy Service",
    description="Microservice for managing insurance policies and claims",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policies.router)
app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(admin_users.router)
app.include_router(compliance.router)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {
        "status": "healthy",
        "service": "policy-service",
        "environment": settings.environment
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
