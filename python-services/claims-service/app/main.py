"""Claims Service - FastAPI Application."""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.error_handlers import register_exception_handlers
from app.routes import claims, photos, compliance
import app.models.stubs  # Register stub models for ForeignKeys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Wali Claims Service",
    description="Insurance claims processing with fraud detection for Côte d'Ivoire",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register security error handlers (sanitizes all exceptions)
register_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(claims.router)
app.include_router(photos.router)
app.include_router(compliance.router)

# Health check endpoint (no auth required)
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {
        "status": "healthy",
        "service": "claims-service",
        "environment": settings.environment
    }

# Root endpoint (no auth required)
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "Wali Claims Service",
        "version": "1.0.0",
        "docs": "/docs"
    }



# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info(f"Starting Claims Service in {settings.environment} mode")
    logger.info(f"MinIO endpoint: {settings.minio_endpoint}")
    logger.info(f"Max image size: {settings.max_image_size_mb}MB")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Claims Service")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.environment == "development"
    )
