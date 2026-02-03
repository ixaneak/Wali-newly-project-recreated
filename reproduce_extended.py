import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_complex_payloads():
    # 1. Long UID (Firebase style)
    user_id = "firebase-user-" + str(uuid.uuid4()) + "-extralongtokenpart"
    print(f"Testing with long user_id: {user_id}")
    
    payload = {
        "user_id": user_id,
        "coverage_type": "bundle",
        "coverage_details": {
            "max_coverage_amount": 500000,
            "description": "Test Policy with 🚀 emojis and very long description to see if serialization breaks anything. " * 10
        },
        "payment_frequency": "monthly",
        "region": "Abidjan"
    }
    
    try:
        print("Creating policy...")
        resp = requests.post(f"{BASE_URL}/api/v1/policies/", json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Error Response: {resp.text}")
        else:
            policy = resp.json()
            print(f"Success! ID: {policy['id']}")
            
            # Try to fetch it
            print("Fetching back...")
            resp = requests.get(f"{BASE_URL}/api/v1/policies/user/{user_id}")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Fetched {len(resp.json())} policies.")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_complex_payloads()
