from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import os
import logging

from app.core.database import get_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Monitoring & Health"])

@router.get("/live")
async def liveness_probe():
    """Simple liveness probe for Kubernetes/Railway"""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_probe(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Complex readiness probe checking database and redis connections.
    """
    status_dict = {
        "database": "unknown",
        "redis": "unknown",
        "overall": "healthy"
    }
    
    # Check Postgres Connection
    try:
        await db.execute(text("SELECT 1"))
        status_dict["database"] = "healthy"
    except Exception as e:
        logger.error(f"Readiness Probe - Database Error: {e}")
        status_dict["database"] = "unhealthy"
        status_dict["overall"] = "unhealthy"
        
    # Check Redis Connection
    try:
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        status_dict["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Readiness Probe - Redis Error: {e}")
        status_dict["redis"] = "unhealthy"
        status_dict["overall"] = "unhealthy"
        
    if status_dict["overall"] != "healthy":
        response.status_code = 503
        
    return status_dict
