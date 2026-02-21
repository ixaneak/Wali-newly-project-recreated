import requests
import uuid
import json

BASE_URL = "http://127.0.0.1:8001/api/v1/claims"

# Test Data
# Use UUIDs as strings
USER_ID = str(uuid.uuid4())
POLICY_ID = str(uuid.uuid4())

def create_claim():
    print("--- Creating Claim (via /submit-json) ---")
    payload = {
        "user_id": USER_ID,
        "policy_id": POLICY_ID,
        "claim_type": "health",
        "description": "Consultation for headache verification script",
        "claimed_amount": 15000,
        "photos": ["http://minio:9001/mock/img1.jpg"] # Renamed from image_urls
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submit-json", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("Success!")
            return response.json()['id']
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error creating claim: {e}")
    return None

def list_claims(claim_id=None):
    print(f"\n--- Listing Claims for User {USER_ID} ---")
    try:
        # Route is /user/{user_id}
        url = f"{BASE_URL}/user/{USER_ID}"
        response = requests.get(url, timeout=10)
        print(f"GET {url} Status: {response.status_code}")
        
        if response.status_code == 200:
            claims = response.json()
            print(f"Found {len(claims)} claims")
            for c in claims:
                print(f" - {c.get('claim_number')} ({c.get('status')}) - {c.get('description')}")
        else:
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error listing claims: {e}")

if __name__ == "__main__":
    cid = create_claim()
    if cid:
        list_claims(cid)
