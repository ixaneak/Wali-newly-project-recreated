import requests
import uuid
import io
import json
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://wali_local:wali_local_password@localhost:5432/wali"

def setup_user_in_db(user_id):
    try:
        print(f"   [DB] Inserting user {user_id} into database...")
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Check if exists
            res = conn.execute(text("SELECT id FROM users WHERE id = :uid"), {"uid": user_id})
            if res.fetchone():
                print("   [DB] User already exists.")
                return

            # Insert
            conn.execute(
                text("INSERT INTO users (id, phone, name, kyc_status, role) VALUES (:uid, :phone, :name, 'verified', 'user')"),
                {"uid": user_id, "phone": "+22500000000", "name": "Test User"}
            )
            conn.commit()
            print("   [DB] User inserted successfully.")
    except Exception as e:
        print(f"   [DB] Failed to insert user: {e}")

def verify_full_flow():
    # 1. Setup: Create User and Policy
    user_id = str(uuid.uuid4()) # Use proper UUID
    print(f"--- 1. Verification Setup (User: {user_id}) ---")
    
    # Prerequisite: Create user in DB (since we lack a registration endpoint in this mock flow)
    setup_user_in_db(user_id)
    
    policy_payload = {
        "user_id": user_id,
        "coverage_type": "bundle",
        "coverage_details": {"max_coverage_amount": 50000},
        "payment_frequency": "monthly",
        "region": "Abidjan"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/policies/", json=policy_payload)
        # Check for 500 error content
        if resp.status_code >= 400:
             print(f"❌ Policy setup failed ({resp.status_code}): {resp.text}")
             if resp.status_code == 500: return
        resp.raise_for_status()
        policy = resp.json()
        print(f"✅ Policy Created: {policy['id']}")
    except Exception as e:
        print(f"❌ Policy setup exception: {e}")
        return

    # 2. Upload Photo
    print("\n--- 2. Testing Photo Upload ---")
    img_byte_arr = io.BytesIO()
    # Tiny red dot PNG
    img_byte_arr.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x04\x01\x00q<\x00\x00\x00\x00IEND\xaeB`\x82')
    img_byte_arr.seek(0)
    
    files = [
        ('files', ('evidence1.png', img_byte_arr, 'image/png'))
    ]
    
    photo_urls = []
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/photos/upload-multiple", files=files)
        resp.raise_for_status()
        data = resp.json()
        print(f"✅ Photo Upload Response: {json.dumps(data, indent=2)}")
        
        if data['uploaded'] > 0:
             # Look for url in results
            photo_urls = [r.get('url') for r in data['results'] if r.get('url')]
            print(f"   Collected {len(photo_urls)} URLs: {photo_urls}")
        else:
            print("⚠️ No photos uploaded successfully")
            
    except Exception as e:
        print(f"❌ Photo upload failed: {e}")
        # Continue with empty photos to test claim submission anyway
    
    # 3. Submit Claim
    print("\n--- 3. Testing Claim Submission ---")
    claim_payload = {
        "user_id": user_id, 
        "claim_type": "medical",
        "amount": 25000.50,
        "description": "Medical consultation verification",
        "incident_date": "2024-02-01",
        "photos": photo_urls
    }
    
    # Claims endpoint needs Authorization for user_id usually, but mock might skip or use header?
    # Checking claims.py: get_current_user dependency.
    # In Mock/Dev mode, get_current_user often has a fallback or we need to simulate a token.
    # Let's check app/core/auth.py to see how to authenticate requests in dev.
    
    # SIMULATION: The auth.py likely decodes a token.
    # If using Mock, maybe we can pass a special header or just a dummy token if verify_token is mocked.
    
    # SIMULATION: The auth.py fallback allows unauthenticated requests to pass as 'mock-dev-id'
    # So we should NOT send a header that triggers strict validation if we don't have a real token.
    headers = {}
    
    try:
        # We need to simulate the user context. 
        # API requires current_user. If we don't send token, Auth.get_current_user returns 'mock-dev-id'.
        # But we created a SPECIFIC user_id in DB.
        # So using 'mock-dev-id' will cause a mismatch if the claim requires user_id to match?
        # claims.py: create_claim -> uses current_user['user_id'] as the claim user_id usually.
        # Let's check claims.py.
        
        # If claims.py overrides payload user_id with current_user['user_id'], then we need to insert 'mock-dev-id' into DB!
        # Let's insert 'mock-dev-id' as well just in case.
        setup_user_in_db('mock-dev-id')

        resp = requests.post(f"{BASE_URL}/api/v1/claims", json=claim_payload, headers=headers)
        
        if resp.status_code == 401 or resp.status_code == 403:
             print(f"⚠️ Auth Failed ({resp.status_code}). Checking if we can bypass...")
             # Inspecting response might give a clue
             print(resp.text)
        elif resp.status_code == 201:
            claim = resp.json()
            print(f"✅ Claim Submitted Successfully!")
            print(f"   ID: {claim['id']}")
            print(f"   Status: {claim['status']}")
            print(f"   Photos: {len(claim['photos'])}")
        else:
            print(f"❌ Claim Submission Failed: {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"❌ Claim submission exception: {e}")

if __name__ == "__main__":
    verify_full_flow()
