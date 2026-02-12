from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import logging

from app.core.config import get_settings
from app.core.mock_database import MockSession

settings = get_settings()
logger = logging.getLogger(__name__)

Base = declarative_base()

USE_MOCK_DB = False

try:
    # PROD: Fly.io provides DATABASE_URL
    database_url = settings.database_url
    
    if database_url and database_url.startswith("postgres"):
        database_url = database_url.replace("postgres://", "postgresql://")
        
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.environment == "development",
        connect_args={"connect_timeout": 10}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to create DB engine: {e}")
    # CRITICAL: Do not fallback to mock in production
    if settings.environment == "production":
        raise
    USE_MOCK_DB = True

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
