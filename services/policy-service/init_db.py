"""
Database initialization script.
Run this to create all tables including the new claims table.
"""
from app.core.database import engine, Base
from app.models import Policy, User, Claim
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        logger.info("Tables: users, policies, claims")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
