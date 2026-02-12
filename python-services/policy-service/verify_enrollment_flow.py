import sys
import os
import logging
from unittest.mock import MagicMock
from app.services.policy_service import EnrollmentService, PaymentFrequency

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

def test_enrollment_with_mock_partner():
    print("--- Starting SaaS Enrollment Integration Test ---")
    
    # Mock DB Session
    mock_db = MagicMock()
    
    # Config matching what mock partner expects
    product_id = "micro-health"
    config = {"coverage_amount": 1000000}
    
    print(f"1. Calling EnrollmentService for '{product_id}'...")
    print("   Expectation: Service calls http://localhost:8008/v1/quotes")
    
    try:
        subscription = EnrollmentService.create_enrollment(
            db=mock_db,
            user_id="user-123",
            partner_id="NSIA",
            partner_product_id=product_id,
            partner_product_config=config,
            payment_frequency=PaymentFrequency.MONTHLY
        )
        
        print(f"2. Subscription Created: {subscription.subscription_number}")
        print(f"   Partner Quoted Amount: {subscription.partner_quoted_amount}")
        
        # Verify price matches Mock Partner logic
        # micro-health is fixed at 500 in mock_partner.py
        if subscription.partner_quoted_amount == 500:
            print("✅ SUCCESS: Price 500 fetched from Mock Partner!")
        else:
            print(f"❌ FAILURE: Expected price 500, got {subscription.partner_quoted_amount}")
            exit(1)
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    test_enrollment_with_mock_partner()
