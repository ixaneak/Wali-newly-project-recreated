from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
import logging

from app.core.config import get_settings
# from app.core.mock_database import MockSession # Removed to avoid circular import

settings = get_settings()
logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Global state for DB connectivity
USE_MOCK_DB = False

try:
    # PROD: Fly.io provides DATABASE_URL
    # DEV: Set DATABASE_URL in .env
    database_url = settings.database_url
    
    if not database_url or "sqlite" in database_url:
        # In production, this should fail if not properly configured
        pass 

    # Create database engine
    connect_args = {}
    
    if database_url.startswith("postgres"):
        # Fix for SQLAlchemy 1.4+ handling of postgres:// URI
        database_url = database_url.replace("postgres://", "postgresql://")
        connect_args["connect_timeout"] = 10
    
    # Dialect-specific engine arguments
    engine_kwargs = {
        "pool_pre_ping": True,
        "echo": settings.environment == "development",
        "connect_args": connect_args,
        "pool_size": 10,
        "max_overflow": 20,
    }

    engine = create_engine(database_url, **engine_kwargs)
    
    # Session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
except Exception as e:
    logger.error(f"Failed to create DB engine: {e}")
    # CRITICAL: Do not fallback to mock in production
    if settings.environment == "production":
        raise
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

# Read replica support (optional) - bypassed for now
get_replica_db = get_db
