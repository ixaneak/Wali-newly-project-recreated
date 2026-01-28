import requests
import uuid

# Configuration
POL_URL = "https://wali-policy-service.fly.dev"

def test_pdf_download():
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

    # 2. Download Certificate
    print(f"Downloading certificate for {policy_id}...")
    try:
        pdf_resp = requests.get(f"{POL_URL}/api/v1/policies/{policy_id}/certificate", timeout=30)
        pdf_resp.raise_for_status()
        
        content_type = pdf_resp.headers.get("Content-Type", "")
        print(f"Status: {pdf_resp.status_code}")
        print(f"Content-Type: {content_type}")
        print(f"Size: {len(pdf_resp.content)} bytes")
        
        if "application/pdf" in content_type and len(pdf_resp.content) > 100:
            print("SUCCESS: Valid PDF received.")
        else:
            print("FAILURE: Response does not look like a PDF.")
            
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == "__main__":
    test_pdf_download()
