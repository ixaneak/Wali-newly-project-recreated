import os
# Force SQLite for testing before ANY other imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
print(f"DEBUG: ENV SET: {os.environ['DATABASE_URL']}")

import requests
import uuid
from app.core.config import get_settings
settings = get_settings()
print(f"DEBUG: SETTINGS URL: {settings.database_url}")


import time
import sys

# BASE_URL = "http://localhost:8080" # If running via Docker/Uvicorn
# But since we might not be able to run long-lived process easily, 
# I might need to run this as a test within the same process or hope I can start background task.
# For now, let's create a script that I can run with `python verification_script.py` which 
# theoretically could be run against a running server.

# HOWEVER, in this environment, I can't easily start a server and keep it running while I run another script.
# So I will write a script that imports the app and uses TestClient.

from fastapi.testclient import TestClient
from main import app
from app.core.database import Base, engine, SessionLocal
# Import models so they are registered with Base
from app.models.payment import PaymentTransaction
from app.models.policy import CoverageSubscription, SubscriptionStatus

# Setup Test DB
print(f"DEBUG: Tables in metadata: {Base.metadata.tables.keys()}")
Base.metadata.create_all(bind=engine)


client = TestClient(app)

def setup_test_policy():
    db = SessionLocal()
    policy_id = str(uuid.uuid4())
    policy = CoverageSubscription(
        id=policy_id,
        status=SubscriptionStatus.PENDING,
        mobile_money_ref=None
    )
    db.add(policy)
    db.commit()
    db.close()
    print(f"[SETUP] Created pending policy: {policy_id}")
    return policy_id

def verify_policy_active(policy_id):
    db = SessionLocal()
    policy = db.query(CoverageSubscription).filter(CoverageSubscription.id == policy_id).first()
    active = policy.status == SubscriptionStatus.ACTIVE
    ref = policy.mobile_money_ref
    db.close()
    if active:
        print(f"[VERIFY] SUCCESS: Policy {policy_id} is ACTIVE with ref {ref}")
    else:
        print(f"[VERIFY] FAILED: Policy {policy_id} is {policy.status}")
    return active

def test_orange_money():
    print("\n--- Testing Orange Money Webhook ---")
    policy_id = setup_test_policy()
    payload = {
        "notif_token": os.getenv("ORANGE_MONEY_NOTIF_TOKEN", "dummy_test_token"),
        "txnid": f"OM-{uuid.uuid4()}",
        "ref_id": policy_id,
        "amount": 5000,
        "status": "SUCCESS"
    }
    response = client.post("/webhooks/orange-money", json=payload)
    print(f"Response: {response.status_code} {response.json()}")
    verify_policy_active(policy_id)

def test_wave():
    print("\n--- Testing Wave Webhook ---")
    policy_id = setup_test_policy()
    payload = {
        "id": f"WV-{uuid.uuid4()}",
        "amount": "5000",
        "checkout_status": "complete",
        "client_reference": policy_id
    }
    response = client.post("/webhooks/wave", json=payload)
    print(f"Response: {response.status_code} {response.json()}")
    verify_policy_active(policy_id)
    
def test_mtn_momo():
    print("\n--- Testing MTN MoMo Webhook ---")
    policy_id = setup_test_policy()
    payload = {
        "financialTransactionId": f"MTN-{uuid.uuid4()}",
        "externalId": policy_id,
        "amount": "5000",
        "currency": "XOF",
        "status": "SUCCESSFUL"
    }
    response = client.post("/webhooks/mtn-momo", json=payload)
    print(f"Response: {response.status_code} {response.json()}")
    verify_policy_active(policy_id)

def test_mock_payment():
    print("\n--- Testing Mock Payment Endpoint ---")
    policy_id = setup_test_policy()
    # Need to simulate partner_id for logic to work, but our setup_test_policy doesn't set it.
    # It defaults to None, and our mock code defaults to NSIA.
    
    payload = {
        "policy_id": policy_id,
        "phone": "+22507070707",
        "amount": 1000
    }
    response = client.post("/test/mock-payment", params=payload) # Query params or body? Definition uses query params for primitives by default in FastAPI if not Pydantic model
    # Wait, my implementation: def mock_payment(policy_id: str, ...):
    # In FastAPI, scalar types are query parameters by default. Pydantic models are body.
    # So I should send as query params.
    response = client.post(f"/test/mock-payment?policy_id={policy_id}&amount=1000")
    
    print(f"Response: {response.status_code} {response.json()}")
    verify_policy_active(policy_id)

if __name__ == "__main__":
    try:
        test_orange_money()
        test_wave()
        test_mtn_momo()
        test_mock_payment()
        print("\nALL TESTS COMPLETED")

    except Exception as e:
        print(f"TEST FAILED: {e}")
