from app.core.database import engine, Base
from app.models.policy import User, Policy
from app.models.claim import Claim

print("Resetting database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database reset complete.")
