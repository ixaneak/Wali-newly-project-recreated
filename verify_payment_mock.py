import requests
import time

BASE_URL = "http://localhost:8082"

def verify_payment_mock():
    print("Verifying Payment Service Mock...")
    
    # 1. Initiate Payment
    payload = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "policy_id": "POL-12345678",
        "amount": 5000,
        "phone": "+2250102030405",
        "provider": "orange"
    }
    
    try:
        print(f"Initiating payment at {BASE_URL}/api/v1/payments/initiate...")
        resp = requests.post(f"{BASE_URL}/api/v1/payments/initiate", json=payload)
        resp.raise_for_status()
        txn = resp.json()
        print(f"Transaction Created: {txn['transaction_ref']} (Status: {txn['status']})")
        
        if txn['status'] != "success":
             print("FAILURE: Mock payment should be 'success'")
             return

        # 2. Verify Payment
        txn_ref = txn['transaction_ref']
        print(f"Verifying transaction {txn_ref}...")
        resp = requests.get(f"{BASE_URL}/api/v1/payments/verify/{txn_ref}?provider=orange")
        resp.raise_for_status()
        verify_data = resp.json()
        print(f"Verification Result: {verify_data['status']}")
        
        if verify_data['status'] == "success":
            print("SUCCESS: Payment Mock Verified")
        else:
            print("FAILURE: Verification returned non-success status")
            
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == "__main__":
    verify_payment_mock()
