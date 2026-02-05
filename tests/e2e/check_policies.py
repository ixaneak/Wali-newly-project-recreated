import requests
import json

POL_URL = "https://wali-policy-service.fly.dev"
USER_ID = '550e8400-e29b-41d4-a716-446655440000'

def check_policies():
    print(f"Fetching policies for user {USER_ID}...")
    try:
        resp = requests.get(f"{POL_URL}/api/v1/policies/user/{USER_ID}", timeout=30)
        resp.raise_for_status()
        policies = resp.json()
        print(f"Found {len(policies)} policies:")
        for p in policies:
            print(f"- {p['policy_number']}: {p['status']} ({p['id']})")
    except Exception as e:
        print(f"Failed to fetch policies: {e}")

if __name__ == "__main__":
    check_policies()
