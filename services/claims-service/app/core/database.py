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
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.environment == "development",
        connect_args={"connect_timeout": 3}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Failed to create DB engine: {e}")
    USE_MOCK_DB = True

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
