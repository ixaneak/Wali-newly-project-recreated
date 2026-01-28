
import sys
import os
import json
import uuid

# Add current directory to path
current_dir = os.getcwd()
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'services', 'claims-service'))

# Set env
os.environ["JWT_SECRET"] = "test"

# Force Mock DB
from app.core import database
database.USE_MOCK_DB = True
from app.core.database import get_db
from app.models.claim import Claim, CoverageType, ClaimStatus

def verify_claims_persistence():
    print("Testing Claims Persistence...")
    
    # Ensure no db file exists
    if os.path.exists("claims_mock_db.json"):
        os.remove("claims_mock_db.json")
        
    db = next(get_db())
    
    # Step 1: Create Claim
    user_id = uuid.uuid4()
    p_id = uuid.uuid4()
    
    c = Claim(
        user_id=user_id,
        policy_id=p_id,
        claim_number="CLM-TEST-001",
        claim_type=CoverageType.HEALTH,
        description="Test claim persistence",
        claimed_amount=25000,
        image_hashes=["test_hash"],
        status=ClaimStatus.SUBMITTED
    )
    db.add(c)
    db.commit()
    
    cid = str(c.id)
    print(f"Created claim {cid}")
    
    # Check file exists
    if not os.path.exists("claims_mock_db.json"):
        print("FAIL: claims_mock_db.json not created")
        return
        
    # Reload
    from app.core.mock_database import load_db, MOCK_DATA_STORE
    
    MOCK_DATA_STORE.clear()
    load_db()
    
    if len(MOCK_DATA_STORE.get("Claim", [])) != 1:
        print("FAIL: Failed to reload claim data")
    else:
        loaded_c = MOCK_DATA_STORE["Claim"][0]
        if str(loaded_c.id) == cid and loaded_c.claim_type == CoverageType.HEALTH:
             print("PASS: Claim data reloaded successfully")
        else:
             print(f"FAIL: Reloaded data mismatch")

if __name__ == "__main__":
    verify_claims_persistence()
