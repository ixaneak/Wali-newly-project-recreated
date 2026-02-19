"""
Database Configuration for Policy Service

Uses shared wali_core.database module for optimized connection pooling.
Supports both client-side (QueuePool) and server-side (PgBouncer) pooling.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Global state for DB connectivity
USE_MOCK_DB = False

try:
    # Import shared database module
    import sys
    from pathlib import Path
    
    # Add shared module to path if needed
    shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    
    from wali_core.database import create_engine_with_pool, DatabaseManager
    
    # Use shared pooling configuration
    database_url = settings.database_url
    
    if "sqlite" in database_url:
        # SQLite local development support
        engine = create_engine(
            database_url, 
            connect_args={"check_same_thread": False}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine created for SQLite")
        
    elif database_url:
        # Fix for SQLAlchemy 1.4+ handling of postgres:// URI
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://")
        
        # Create engine using shared pooling configuration
        engine = create_engine_with_pool(database_url, service_name='policy-service')
        
        # Session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info("Database engine created with optimized pooling (QueuePool or NullPool)")
    else:
        raise ValueError("Invalid DATABASE_URL")
    
except Exception as e:
    logger.error(f"Failed to create DB engine with shared pooling: {e}")
    
    # CRITICAL: Do not fallback to mock in production
    if settings.environment == "production":
        raise
    
    # Fallback for development
    USE_MOCK_DB = True
    engine = None
    SessionLocal = None


def get_db():
    """Dependency for getting database sessions."""
    # Explicit Mock Override
    if settings.use_mock_db:
        from app.core.mock_database import MockSession
        yield MockSession()
        return

    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.error(f"DB Connection failed: {e}")
        raise


def get_db_with_pool_status():
    """Get DB session with pool status information."""
    try:
        from wali_core.database import check_database_health
        health = check_database_health(engine)
        logger.debug(f"Database pool health: {health}")
    except Exception as e:
        logger.debug(f"Could not get pool status: {e}")
    
    return get_db()


# Read replica support (optional) - bypassed for now
get_replica_db = get_db


# Export for compatibility
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db', 'get_replica_db']
