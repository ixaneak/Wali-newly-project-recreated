import requests
import uuid

POL_URL = "https://wali-policy-service.fly.dev"
PAY_URL = "https://wali-payment-service.fly.dev"

def test_create_policy():
    print(f"Testing Policy Creation against {POL_URL}...")
    
    user_id = '550e8400-e29b-41d4-a716-446655440000' # Mock User ID
    payload = {
        "user_id": user_id,
        "coverage_type": "health",
        "coverage_details": {
            "max_coverage_amount": 50000
        },
        "payment_frequency": "monthly",
        "region": "Gagnoa"
    }
    
    try:
        resp = requests.post(f"{POL_URL}/api/v1/policies/", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 201:
            print("Success! Policy Created.")
            data = resp.json()
            print(f"Policy ID: {data['id']}")
            return data['id'], user_id
        else:
            print("Failed!")
            print(resp.text)
            return None, None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None, None

def test_payment(policy_id, user_id):
    if not policy_id: return
    print(f"\nTesting Payment Initiation against {PAY_URL}...")
    
    payload = {
        "user_id": user_id,
        "policy_id": policy_id,
        "amount": 150,
        "phone": "+2250123456789",
        "provider": "orange"
    }
    
    try:
        resp = requests.post(f"{PAY_URL}/api/v1/payments/initiate", json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
             print("Success! Payment Initiated.")
             print(resp.json())
        else:
             print("Payment Failed!")
             print(resp.text)
    except Exception as e:
         print(f"Payment Connection Error: {e}")

if __name__ == "__main__":
    pid, uid = test_create_policy()
    if pid:
        test_payment(pid, uid)
