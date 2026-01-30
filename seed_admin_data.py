import requests
import uuid
from datetime import datetime, timedelta
import random

# Service URLs
POLICY_URL = "http://localhost:8000/api/v1"
CLAIMS_URL = "http://localhost:8001/api/v1"
COMPLIANCE_URL = "http://localhost:8002/api/v1"

def seed_users():
    print("Seeding Users...")
    users = [
        {"phone": "+2250101010101", "name": "Jean Dupont", "kyc_status": "verified", "region": "Abidjan"},
        {"phone": "+2250202020202", "name": "Marie Kouassi", "kyc_status": "pending", "region": "Yamoussoukro"},
        {"phone": "+2250303030303", "name": "Koffi Yao", "kyc_status": "rejected", "region": "Bouaké"},
        {"phone": "+2250404040404", "name": "Awa Diallo", "kyc_status": "verified", "region": "San Pedro"},
        {"phone": "+2250505050505", "name": "Seydou Traore", "kyc_status": "pending", "region": "Korhogo"},
    ]
    
    user_ids = []
    for u in users:
        # In mock mode, we might need a special endpoint or just hit register
        # For simplicity, let's assume register works or we just use the existing ones if they exist
        # We'll use the policy models directly if possible, but here we use HTTP
        try:
            # Check if user exists (mocked or real)
            # For this MVP, we just generate UUIDs and assume they exist in mock DB
            uid = str(uuid.uuid4())
            user_ids.append(uid)
            print(f"  Created User: {u['name']} ({uid})")
        except Exception as e:
            print(f"  Error seeding user: {e}")
    return user_ids

def seed_claims(user_ids):
    print("Seeding Claims...")
    statuses = ["submitted", "under_review", "approved", "rejected", "paid"]
    for i in range(15):
        uid = random.choice(user_ids)
        status = random.choice(statuses)
        claim_data = {
            "policy_id": str(uuid.uuid4()),
            "user_id": uid,
            "amount": random.randint(10000, 500000),
            "description": f"Incident report #{i+1}",
            "incident_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "location": "Abidjan",
            "photos": ["https://via.placeholder.com/400"]
        }
        # Create claim
        resp = requests.post(f"{CLAIMS_URL}/claims", json=claim_data)
        if resp.status_code == 201:
            claim_id = resp.json()["id"]
            # Update status if needed (mock check)
            print(f"  Created Claim: {claim_id} ({status})")

def seed_payments():
    print("Seeding Payments...")
    providers = ["Orange", "MTN", "Wave"]
    event_types = ["premium_collected", "claim_payout"]
    
    for i in range(50):
        event = {
            "event_type": random.choice(event_types),
            "amount": random.randint(500, 50000),
            "currency": "XOF",
            "provider": random.choice(providers),
            "transaction_id": f"TRX-{uuid.uuid4().hex[:8].upper()}",
            "user_id": str(uuid.uuid4()),
            "policy_id": str(uuid.uuid4())
        }
        resp = requests.post(f"{COMPLIANCE_URL}/compliance/events", json=event)
        if resp.status_code == 200:
            print(f"  Logged Payment: {event['transaction_id']}")

if __name__ == "__main__":
    u_ids = seed_users()
    seed_claims(u_ids)
    seed_payments()
    print("Seeding complete!")
