from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

Base = declarative_base()

# Import models to ensure they are registered with Base metadata
# This is needed for auto-migration/creation of tables
# logic moved to main.py or init_db.py usually, but good to have base know about them if possible, 
# or just ensure they are imported before Base.metadata.create_all() is called.


try:
    database_url = settings.database_url
    
    # Fix for SQLAlchemy 1.4+ with postgres://
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://")
        
    connect_args = {}
    # Dialect-specific engine arguments
    engine_kwargs = {
        "pool_pre_ping": True,
        "echo": settings.environment == "development",
        "connect_args": connect_args,
    }
    
    if "sqlite" not in database_url:
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
        })
    else:
        # SQLite specific: allow multi-thread access for testing
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(
        database_url, 
        **engine_kwargs
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
except Exception as e:
    logger.error(f"Failed to create DB engine: {e}")
    engine = None
    SessionLocal = None

def get_db():
    if SessionLocal is None:
        raise Exception("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
