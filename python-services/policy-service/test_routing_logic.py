import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Add current directory to path
sys.path.append(os.getcwd())

# Configuration
os.environ["PAYDUNYA_MODE"] = "test"
os.environ["PAYDUNYA_MASTER_KEY"] = "test"
os.environ["PAYDUNYA_PRIVATE_KEY"] = "test"
os.environ["PAYDUNYA_TOKEN"] = "test"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print("--- Importing Modules ---")
    from app.core.database import Base
    from app.models.policy import CoverageSubscription, SubscriptionStatus, PaymentFrequency
    from app.models.partner import Partner
    from app.models.paydunya_transaction import PaydunyaTransaction
    from app.services.paydunya_service import create_paydunya_invoice
    print("✅ Imports successful")

    # Setup DB
    print("--- Setting up In-Memory DB ---")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    print("✅ Schema created")

    # Seed Data
    print("--- Seeding Data ---")
    partner = Partner(
        id="NSIA",
        name="NSIA Assurance",
        license_number="CIMA-123",
        collection_account_id="nsia_paydunya_account"
    )
    db.add(partner)
    
    sub_id = uuid.uuid4()
    subscription = CoverageSubscription(
        id=sub_id,
        user_id="user-123",
        subscription_number="SUB-001",
        partner_id="NSIA",
        partner_product_id="SANTE-PLUS",
        partner_product_config={"cover": "full"},
        partner_quoted_amount=5000,
        payment_frequency=PaymentFrequency.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now()
    )
    db.add(subscription)
    db.commit()
    print(f"✅ Seeding complete. Sub ID: {sub_id}")

    # Test Logic
    print("--- Testing Payment Routing ---")
    response = create_paydunya_invoice(
        db=db,
        subscription_id=str(sub_id),
        user_phone="0700000000",
        user_name="Test Artisan"
    )

    print(f"Response: {response}")

    # Verify Logic
    txn = db.query(PaydunyaTransaction).filter(PaydunyaTransaction.subscription_id == sub_id).first()
    if txn:
        print(f"✅ Transaction recorded. Internal Ref: {txn.internal_ref}")
        print(f"✅ Wali Role: {txn.metadata_json.get('wali_role')}")
        print(f"✅ Partner ID: {txn.metadata_json.get('partner_id')}")
        
        if txn.metadata_json.get('wali_role') == 'technology_provider':
            print("🚀 SUCCESS: Payment routing verified as Technology Provider model.")
        else:
            print("❌ FAILURE: Incorrect role.")
    else:
        print("❌ FAILURE: No transaction recorded.")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
