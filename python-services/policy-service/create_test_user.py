import uuid
from datetime import datetime
from app.core.database import SessionLocal
from app.models.policy import User, UserRole, KYCStatus

# Explicitly use UUID for ID if model requires it, but schema might use string
# Checking admin_users.py, it expects UUID for user_id in path? 
# "user_id: uuid.UUID" in route definition.
# So ID must be valid UUID.

db = SessionLocal()

# Use mock-user-001 to match frontend dev token
user_id = "mock-user-001"

try:
    user = User(
        id=str(user_id), # Ensure string
        phone="0701010101", # Matches mock auth phone if relevant
        name="Amadou Koné",
        role=UserRole.ARTISAN,
        kyc_status=KYCStatus.PENDING
        # created_at handled by DB
    )

    existing = db.query(User).filter(User.phone == "0701010101").first()
    if not existing:
        db.add(user)
        db.commit()
        print(f"User created: {user.id}")
    else:
        print(f"User exists: {existing.id}")

except Exception as e:
    print(f"Error creating user: {e}")
finally:
    db.close()
