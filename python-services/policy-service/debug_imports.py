import sys
import traceback

try:
    from app.models.pharmacy import PharmacyPartner, SubscriptionStatus
    print("Direct import from app.models.pharmacy successful")
except Exception as e:
    print("Direct import from app.models.pharmacy failed")
    traceback.print_exc()

try:
    from app.models import pharmacy
    print("Import app.models.pharmacy successful")
except Exception as e:
    print("Import app.models.pharmacy failed")
    traceback.print_exc()

try:
    import app.main
    print("Import app.main successful")
except Exception as e:
    print("Import app.main failed")
    traceback.print_exc()
