
import sys
import os
import logging
from datetime import datetime
import uuid

# Add current directory to path
current_dir = os.getcwd()
sys.path.append(current_dir)
# Add policy service root
sys.path.append(os.path.join(current_dir, 'services', 'policy-service'))

# Set required environment variables
os.environ["JWT_SECRET"] = "test-secret-policy-mock"
os.environ["ESCROW_BANK_ACCOUNT"] = "1234567890"
os.environ["OPERATING_BANK_ACCOUNT"] = "0987654321"

# Force Mock DB
from app.core import database
database.USE_MOCK_DB = True
from app.core.database import get_db
from app.models.policy import Policy, PolicyStatus, CoverageType, PaymentFrequency
from app.services.policy_service import PolicyService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_policy_service():
    logger.info("Starting Policy Service Verification (Mock DB)...")
    
    # Get session
    db = next(get_db())
    
    user_id = str(uuid.uuid4())
    
    # Test 1: Create Policy
    logger.info("Test 1: Create Policy...")
    policy = PolicyService.create_policy(
        db=db,
        user_id=user_id,
        coverage_type=CoverageType.HEALTH,
        coverage_details={"max_coverage_amount": 1000000},
        payment_frequency=PaymentFrequency.MONTHLY,
        region="Abidjan"
    )
    logger.info(f"Created Policy: {policy.id} ({policy.status.value})")
    
    if policy.status == PolicyStatus.PENDING:
        logger.info("PASS: Policy created in PENDING state")
    else:
        logger.error(f"FAIL: Policy status is {policy.status}")

    # Test 2: Activate Policy
    logger.info("\nTest 2: Activate Policy...")
    active_policy = PolicyService.activate_policy(
        db=db,
        policy_id=str(policy.id),
        transaction_ref="TXN-12345"
    )
    if active_policy.status == PolicyStatus.ACTIVE:
        logger.info("PASS: Policy activated")
    else:
         logger.error(f"FAIL: Policy status is {active_policy.status}")

    # Test 3: Get User Policies
    logger.info("\nTest 3: Get User Policies...")
    policies = PolicyService.get_user_policies(db, user_id)
    if len(policies) == 1 and policies[0].id == policy.id:
         logger.info("PASS: Found user policy")
    else:
         logger.error(f"FAIL: Found {len(policies)} policies")

if __name__ == "__main__":
    try:
        verify_policy_service()
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
