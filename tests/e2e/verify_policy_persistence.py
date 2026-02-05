
import sys
import os
import json
import uuid

# Add current directory to path
current_dir = os.getcwd()
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'services', 'policy-service'))

# Set env
os.environ["JWT_SECRET"] = "test"
os.environ["ESCROW_BANK_ACCOUNT"] = "123"
os.environ["OPERATING_BANK_ACCOUNT"] = "456"

# Force Mock DB
from app.core import database
database.USE_MOCK_DB = True
from app.core.database import get_db
from app.services.policy_service import PolicyService
from app.models.policy import CoverageType, PaymentFrequency, PolicyStatus

def verify_persistence():
    print("Testing Policy Persistence...")
    
    # Ensure no db file exists
    if os.path.exists("mock_db.json"):
        os.remove("mock_db.json")
        
    db = next(get_db())
    
    # Step 1: Create Policy
    user_id = uuid.uuid4()
    p = PolicyService.create_policy(
        db, 
        str(user_id), 
        CoverageType.HEALTH, 
        {"max_coverage_amount": 1000}, 
        PaymentFrequency.MONTHLY
    )
    pid = str(p.id)
    print(f"Created policy {pid}")
    
    del db
    
    # Check file exists and has data
    if not os.path.exists("mock_db.json"):
        print("FAIL: mock_db.json not created")
        return
        
    with open("mock_db.json") as f:
        data = json.load(f)
        if len(data.get("Policy", [])) != 1:
             print("FAIL: persisted data count mismatch")
             return
        if data["Policy"][0]["id"] != pid:
             print("FAIL: Persisted ID mismatch")
             return
             
    print("PASS: Persistence file written successfully")
    
    # Step 2: Reload
    # We need to reload the module to trigger load_db()? 
    # Or just call load_db() manually because we are in same process
    # In reality, a service restart implies new process.
    from app.core.mock_database import load_db, MOCK_DATA_STORE
    
    # Clear memory
    MOCK_DATA_STORE.clear()
    
    # Reload
    load_db()
    
    if len(MOCK_DATA_STORE.get("Policy", [])) != 1:
        print("FAIL: Failed to reload data")
    else:
        loaded_p = MOCK_DATA_STORE["Policy"][0]
        if str(loaded_p.id) == pid and loaded_p.status == PolicyStatus.PENDING:
             print("PASS: Data reloaded successfully")
        else:
             print(f"FAIL: Reloaded data mismatch: {loaded_p.id} vs {pid}")

if __name__ == "__main__":
    verify_persistence()
