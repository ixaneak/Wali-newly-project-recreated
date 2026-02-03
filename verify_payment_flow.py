import requests
import uuid
import json
import time
from sqlalchemy import create_engine, text

POLICY_URL = "http://localhost:8000"
PAYMENT_URL = "http://localhost:8080"
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

            conn.execute(
                text("INSERT INTO users (id, phone, name, kyc_status, role) VALUES (:uid, :phone, :name, 'verified', 'user')"),
                {"uid": user_id, "phone": "+22500000000", "name": "Payment Test User"}
            )
            conn.commit()
            print("   [DB] User inserted successfully.")
    except Exception as e:
        print(f"   [DB] Failed to insert user: {e}")

def verify_payment_flow():
    user_id = str(uuid.uuid4())
    print(f"\n=== verifying Payment & Activation Flow (User: {user_id}) ===")
    
    # 0. Setup User
    setup_user_in_db(user_id)
    
    # 1. Create Policy
    print("\n--- 1. Creating Policy ---")
    policy_payload = {
        "user_id": user_id,
        "coverage_type": "bundle",
        "coverage_details": {"max_coverage_amount": 50000},
        "payment_frequency": "monthly",
        "region": "Abidjan"
    }
    
    try:
        resp = requests.post(f"{POLICY_URL}/api/v1/policies/", json=policy_payload)
        resp.raise_for_status()
        policy = resp.json()
        policy_id = policy['id']
        print(f"[OK] Policy Created: {policy_id} (Status: {policy['status']})")
    except Exception as e:
        print(f"[ERROR] Policy setup failed: {e}")
        return

    # 2. Initiate Payment
    print("\n--- 2. Initiating Payment (Orange Money) ---")
    payment_payload = {
        "user_id": user_id,
        "policy_id": policy_id,
        "amount": 9900,
        "phone": "+2250707070707",
        "provider": "orange"
    }
    
    txn_ref = ""
    try:
        resp = requests.post(f"{PAYMENT_URL}/api/v1/payments/initiate", json=payment_payload)
        resp.raise_for_status()
        payment_res = resp.json()
        txn_ref = payment_res['transaction_ref']
        print(f"[OK] Payment Initiated: {payment_res['transaction_id']}")
        print(f"   Ref: {txn_ref}")
        print(f"   Status: {payment_res['status']}")
    except Exception as e:
        print(f"[ERROR] Payment initiation failed: {e}")
        if 'resp' in locals():
            print(f"Response: {resp.text}")
        # If payment service is down, we abort
        return

    # 3. Verify Payment
    print("\n--- 3. Verifying Payment Status ---")
    try:
        resp = requests.get(f"{PAYMENT_URL}/api/v1/payments/verify/{txn_ref}")
        resp.raise_for_status()
        verify_res = resp.json()
        print(f"[OK] Payment Status: {verify_res['status']}")
        
        if verify_res['status'] != 'SUCCESS':
            print("[WARNING] Payment not successful yet.")
    except Exception as e:
        print(f"[ERROR] Payment verification failed: {e}")

    # 4. Activate Policy
    print("\n--- 4. Activating Policy ---")
    activate_payload = {
        "transaction_ref": txn_ref
    }
    
    try:
        resp = requests.post(f"{POLICY_URL}/api/v1/policies/{policy_id}/activate", json=activate_payload)
        resp.raise_for_status()
        policy_updated = resp.json()
        print(f"[OK] Policy Updated Status: {policy_updated['status']}")
        
        if policy_updated['status'] == 'active':
             print("[SUCCESS]: Policy is ACTIVE!")
        else:
             print("[WARNING] Policy not active.")
             
    except Exception as e:
        print(f"[ERROR] Policy activation failed: {e}")
        if 'resp' in locals():
             print(resp.text)

if __name__ == "__main__":
    verify_payment_flow()
