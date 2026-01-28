import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"
MOCK_DB_FILE = "services/policy-service/mock_db.json"

def verify_mock_persistence():
    print("Verifying Mock Persistence...")
    
    # 1. Create a Policy
    payload = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "coverage_type": "health",
        "coverage_details": {"max_coverage_amount": 100000},
        "payment_frequency": "monthly",
        "region": "Abidjan"
    }
    
    try:
        print(f"Creating policy at {BASE_URL}/api/v1/policies...")
        # Note: Adjust endpoint if needed based on actual routes
        resp = requests.post(f"{BASE_URL}/api/v1/policies", json=payload)
        resp.raise_for_status()
        policy = resp.json()
        print(f"Policy Created: {policy['id']}")
        
        # 2. Check mock_db.json
        # Wait a moment for async file write if any (though mock db syncs directly)
        time.sleep(1)
        
        if os.path.exists(MOCK_DB_FILE):
             with open(MOCK_DB_FILE, 'r') as f:
                 data = json.load(f)
                 policies = data.get("Policy", [])
                 found = any(p['id'] == policy['id'] for p in policies)
                 
                 if found:
                     print("SUCCESS: Policy found in mock_db.json")
                 else:
                     print("FAILURE: Policy NOT found in mock_db.json")
        else:
             print(f"FAILURE: {MOCK_DB_FILE} does not exist.")
             
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == "__main__":
    verify_mock_persistence()
