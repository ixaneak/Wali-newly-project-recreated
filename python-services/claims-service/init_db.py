import sys
import os

# Fix path for release command to ensure 'app' module is found
sys.path.append(os.getcwd())

from app.core.database import engine, Base
# Import model directly to register it with Base.metadata
# We don't rely on app.models package export to avoid potential import loops or missing exports
from app.models.claim import Claim 

def init_database():
    print("Initializing database...")
    # This creates the 'incident_reports' table
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
