
import logging
logging.basicConfig(level=logging.ERROR)
from app.core.database import SessionLocal
from app.services.policy_service import EnrollmentService
from app.models.policy import User

db = SessionLocal()
try:
    user = db.query(User).filter(User.id == "mock-user-001").first()
    if user:
        print(f"User FOUND: {user.id} {user.name} {user.role}")
    else:
        print("User NOT FOUND")

    enrollments = EnrollmentService.get_user_enrollments(db, "mock-user-001")
    if enrollments:
        print(f"Enrollments FOUND: {len(enrollments)}")
        for e in enrollments:
            print(f" - {e.subscription_number} Status: {e.status} QR: {e.qr_token}")
    else:
        print("Enrollments NOT FOUND")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
