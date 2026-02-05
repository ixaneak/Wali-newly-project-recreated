import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_flow():
    user_id = "test-user-" + str(int(time.time()))
    print(f"Testing flow for user: {user_id}")
    
    # 1. Create Policy
    create_payload = {
        "user_id": user_id,
        "coverage_type": "bundle",
        "coverage_details": {
            "max_coverage_amount": 500000,
            "description": "Test Policy"
        },
        "payment_frequency": "monthly",
        "region": "Abidjan"
    }
    
    try:
        print("Creating policy...")
        resp = requests.post(f"{BASE_URL}/api/v1/policies/", json=create_payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Error Response: {resp.text}")
            return
        
        policy = resp.json()
        print(f"Created Policy ID: {policy['id']}")
        
        # 2. Get User Policies (The "Reload" step)
        print("Fetching user policies...")
        resp = requests.get(f"{BASE_URL}/api/v1/policies/user/{user_id}")
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error Response: {resp.text}")
            return
            
        policies = resp.json()
        print(f"Found {len(policies)} policies")
        for p in policies:
            print(f" - {p['id']} ({p['status']})")

    except Exception as e:
        print(f"Test Failed with Exception: {e}")

if __name__ == "__main__":
    test_full_flow()
