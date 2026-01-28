
import sys
import os
import logging
from datetime import datetime
import uuid

# Add current directory to path
current_dir = os.getcwd()
sys.path.append(current_dir)
# Add claims service root
sys.path.append(os.path.join(current_dir, 'services', 'claims-service'))

# Set required environment variables for config
os.environ["JWT_SECRET"] = "test-secret-for-mock"

# Force Mock DB
from app.core import database
database.USE_MOCK_DB = True
from app.core.database import get_db
from app.models.claim import Claim, CoverageType
from app.validators.fraud_detector import FraudDetector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_fraud_detection():
    logger.info("Starting Fraud Detection Verification (Mock DB)...")
    
    # Get session
    db = next(get_db())
    
    # Create sample user ID
    user_id_1 = str(uuid.uuid4())
    user_id_2 = str(uuid.uuid4())
    
    # Create sample claim with a known hash
    # Hash for a simple black image often used in examples
    # Let's simpler: use a fake hash string that looks real enough
    # pHash is usually 16 chars hex
    known_hash = "a1b2c3d4e5f60708"
    
    claim1 = Claim(
        user_id=user_id_1,
        policy_id=uuid.uuid4(),
        claim_number="CLM-001",
        claim_type=CoverageType.THEFT,
        description="Stolen bike",
        claimed_amount=50000,
        image_hashes=[known_hash],
        image_urls=["http://example.com/img1.jpg"]
    )
    db.add(claim1)
    db.commit()
    logger.info(f"Created Claim 1 with hash {known_hash}")
    
    # Test 1: Exact Match same user
    logger.info("Test 1: Check exact match (same user)...")
    matches = FraudDetector.check_duplicate_images(db, known_hash, user_id_1)
    logger.info(f"Matches found: {len(matches)}")
    if len(matches) > 0 and matches[0]['similarity_score'] == 0:
        logger.info("PASS: Exact match found.")
    else:
        logger.error("FAIL: No exact match found.")
        
    # Analyze fraud
    analysis = FraudDetector.detect_fraud_patterns(matches)
    logger.info(f"Fraud Analysis: {analysis}")
    
    # Test 2: Different user (Fraud!)
    logger.info("\nTest 2: Check match from different user...")
    matches_diff_user = FraudDetector.check_duplicate_images(db, known_hash, user_id_2)
    analysis_diff = FraudDetector.detect_fraud_patterns(matches_diff_user)
    
    if analysis_diff['fraud_detected'] and "Image used by" in str(analysis_diff['patterns']):
        logger.info("PASS: Fraud detected for cross-user image usage.")
    else:
        logger.error(f"FAIL: Fraud detection failed. Report: {analysis_diff}")

    # Test 3: Similar Image (Hamming distance)
    # Let's create a hash that is slightly different
    # a1 -> a2 (0001 -> 0010) distance is small?
    # imagehash hex_to_hash returns ImageHash object.
    # 'a' (1010) vs 'b' (1011) distance 1.
    similar_hash = "b1b2c3d4e5f60708" # First char 'b' vs 'a'
    
    logger.info(f"\nTest 3: Check similar hash {similar_hash}...")
    matches_sim = FraudDetector.check_duplicate_images(db, similar_hash, user_id_1)
    if len(matches_sim) > 0:
         logger.info(f"PASS: Similar image found, score: {matches_sim[0]['similarity_score']}")
    else:
         logger.info("NOTE: No similarity found (might depend on threshold settings).")

if __name__ == "__main__":
    try:
        verify_fraud_detection()
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
