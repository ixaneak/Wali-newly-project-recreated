from app.core.database import SessionLocal
from app.services.policy_service import EnrollmentService
from app.models.policy import PaymentFrequency, SubscriptionStatus, ProductType
from datetime import datetime

db = SessionLocal()

try:
    # Check if enrollment already exists
    enrollments = EnrollmentService.get_user_enrollments(db, "mock-user-001")
    if enrollments:
        print(f"Enrollments exist: {len(enrollments)}")
        for e in enrollments:
            print(f"- {e.subscription_number} ({e.status}) QR: {e.qr_token}")
            
            # If QR token missing (old enrollment), generate it
            if not e.qr_token:
                 e.generate_qr_token()
                 db.commit()
                 print(f"  Generated QR: {e.qr_token}")
    else:
        print("Creating new enrollment...")
        subscription = EnrollmentService.create_enrollment(
            db=db,
            user_id="mock-user-001",
            partner_id="NSIA",
            partner_product_id="NSIA-HEALTH-01",
            partner_product_config={"coverage_amount": 1000000},
            payment_frequency=PaymentFrequency.MONTHLY,
            is_test=True # This sets status to ACTIVE and generates QR
        )
        print(f"Enrollment created: {subscription.subscription_number}")
        print(f"QR Token: {subscription.qr_token}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
