import requests
import uuid
import io

# Configuration
POL_URL = "https://wali-policy-service.fly.dev"
CLAIM_URL = "https://wali-claims-service.fly.dev"

def test_claims_flow():
    # 1. Create a Policy first to get an ID
    user_id = '550e8400-e29b-41d4-a716-446655440000' # Mock User
    payload = {
        "user_id": user_id,
        "coverage_type": "health",
        "coverage_details": {"max_coverage_amount": 50000},
        "payment_frequency": "monthly",
        "region": "Gagnoa"
    }
    
    print("Creating policy...")
    try:
        resp = requests.post(f"{POL_URL}/api/v1/policies/", json=payload, timeout=30)
        resp.raise_for_status()
        policy_data = resp.json()
        policy_id = policy_data['id']
        print(f"Policy Created: {policy_id}")
    except Exception as e:
        print(f"Policy creation failed: {e}")
        return

    # 2. Submit Claim
    print(f"Submitting claim for {policy_id}...")
    
    # Create dummy image
    img_byte_arr = io.BytesIO()
    img_byte_arr.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
    img_byte_arr.seek(0)

    claim_data = {
        "user_id": user_id,
        "policy_id": policy_id,
        "claim_type": "health",
        "description": "Test verification claim",
        "claimed_amount": 15000
    }
    
    files = {
        "images": ("evidence.png", img_byte_arr, "image/png")
    }
    
    try:
        resp = requests.post(f"{CLAIM_URL}/api/v1/claims/", data=claim_data, files=files, timeout=30)
        print(f"Claim Response Status: {resp.status_code}")
        if resp.status_code == 201:
            claim = resp.json()
            print(f"Claim Submitted Successfully: {claim['id']}")
            print(f"Status: {claim['status']}")
            print(f"Fraud Score: {claim['fraud_score']}")
        else:
            print(f"Claim Submission Failed: {resp.text}")
            
    except Exception as e:
        print(f"Claim submission failed: {e}")

if __name__ == "__main__":
    test_claims_flow()
