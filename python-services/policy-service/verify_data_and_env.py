import os
from app.core.database import SessionLocal
from app.models.policy import User, CoverageSubscription

print("--- ENV CHECK ---")
print(f"DATABASE_URL env: {os.environ.get('DATABASE_URL')}")
from app.core.config import get_settings
print(f"Config database_url: {get_settings().database_url}")

print("\n--- DATA CHECK ---")
db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"Users count: {len(users)}")
    for u in users:
        print(f"User: {u.id} - {u.phone}")

    enrollments = db.query(CoverageSubscription).all()
    print(f"Enrollments count: {len(enrollments)}")
    for e in enrollments:
        print(f"Enrollment: {e.subscription_number} - User: {e.user_id} - QR: {e.qr_token}")
except Exception as e:
    print(f"Error querying DB: {e}")
finally:
    db.close()

print("\n--- LOG FILE CONTENT ---")
try:
    with open("enrollment_output.txt", "r", encoding="utf-16") as f:
        print(f.read())
except Exception as e:
    try:
         with open("enrollment_output.txt", "r") as f:
            print(f.read())
    except:
        print("Could not read log file")
