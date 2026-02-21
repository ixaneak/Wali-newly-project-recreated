
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1/pharmacy"
EMAIL = "pharmacie@demo.ci"
PASSWORD = "password123"

def print_step(msg):
    print(f"\n[STEP] {msg}")

def print_success(msg):
    print(f"✅ {msg}")

def print_fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def main():
    print("=== Verifying Pharmacy B2B Flow ===")
    
    # 1. Login
    print_step(f"Logging in as {EMAIL}...")
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={
            "email": EMAIL,
            "password": PASSWORD
        }, timeout=10)
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            api_key = data.get("api_key")
            print_success("Login Successful")
            print(f"   Token: {token[:10]}...")
            print(f"   API Key: {api_key[:10]}...")
            print(f"   Status: {data.get('subscription_status')}")
        else:
            print_fail(f"Login Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print_fail(f"Connection Error: {e}")

    # 2. Get Stats
    print_step("Fetching Pharmacy Stats...")
    headers = {"X-API-Key": api_key}
    try:
        res = requests.get(f"{BASE_URL}/stats", headers=headers, timeout=10)
        if res.status_code == 200:
            stats = res.json()
            print_success("Stats Fetched")
            print(f"   Name: {stats.get('name')}")
            print(f"   Quota: {stats.get('api_quota_remaining')}")
        else:
            print_fail(f"Get Stats Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print_fail(f"Request Error: {e}")

    # 3. Verify Coverage (Active)
    print_step("Verifying Coverage (Active Artisan)...")
    try:
        res = requests.post(f"{BASE_URL}/verify-coverage", json={
            "qr_token": "0707070701:POL-123"
        }, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'active':
                print_success("Verification Result: ACTIVE")
                print(f"   Max Reimbursement: {data.get('max_reimbursement')}")
            else:
                print_fail(f"Expected ACTIVE, got {data['status']}")
        else:
             print_fail(f"Verification Failed: {res.status_code} - {res.text}")

    except Exception as e:
        print_fail(f"Request Error: {e}")

    # 4. Verify Coverage (Inactive/Mock)
    print_step("Verifying Coverage (Inactive Artisan)...")
    try:
        res = requests.post(f"{BASE_URL}/verify-coverage", json={
            "qr_token": "0707070700:POL-INVALID" # Ends with 00 -> Inactive
        }, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'inactive':
                print_success("Verification Result: INACTIVE (As Expected)")
            else:
                print_fail(f"Expected INACTIVE, got {data['status']}")
        else:
             print_fail(f"Verification Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print_fail(f"Request Error: {e}")

    print("\n=== ✅ All Checks Passed ===")

if __name__ == "__main__":
    main()
