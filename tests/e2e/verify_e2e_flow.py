
import sys
import os
import json
import uuid
import time
import subprocess
import requests

# Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
STATE_FILE = os.path.join(BASE_DIR, "e2e_state.json")
POLICY_MS_DIR = os.path.join(ROOT_DIR, "python-services", "policy-service")
CLAIMS_MS_DIR = os.path.join(ROOT_DIR, "python-services", "claims-service")
PAYMENT_MS_DIR = os.path.join(ROOT_DIR, "go-services", "payment-service")

# Env Vars for Subprocesses
ENV_POLICY = os.environ.copy()
ENV_POLICY["JWT_SECRET"] = "test"
ENV_POLICY["ESCROW_BANK_ACCOUNT"] = "123"
ENV_POLICY["OPERATING_BANK_ACCOUNT"] = "456"
# Force persistence file usage (code already defaults to it)

ENV_CLAIMS = os.environ.copy()
ENV_CLAIMS["JWT_SECRET"] = "test"

ENV_PAYMENT = os.environ.copy()
ENV_PAYMENT["PORT"] = "8082"
ENV_PAYMENT["MOCK_PAYMENT_PROVIDERS"] = "true"
ENV_PAYMENT["JWT_SECRET"] = "dev-secret-change-in-production"


def save_state(data):
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f)

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

# ==================== SUBPROCESS STEPS ====================

def step_create_policy():
    print("[Step 1] Creating Policy (Python)...")
    sys.path.append(POLICY_MS_DIR)
    
    # Configure DB
    from app.core.config import get_settings
    settings = get_settings()
    settings.use_mock_db = True
    from app.core import database
    from app.core.database import get_db
    from app.services.policy_service import PolicyService
    from app.models.policy import ProductType, PaymentFrequency
    
    db = next(get_db())
    user_id = str(uuid.uuid4())
    
    policy = PolicyService.create_enrollment(
        db, user_id, "NSIA", ProductType.HEALTH.value, {"coverage_amount": 50000}, PaymentFrequency.MONTHLY, True
    )
    
    print(f"Policy Created: {policy.id}")
    save_state({"policy_id": str(policy.id), "user_id": user_id, "amount": policy.partner_quoted_amount})

def step_activate_policy():
    print("[Step 3] Activating Policy (Python)...")
    state = load_state()
    sys.path.append(POLICY_MS_DIR)
    
    from app.core.config import get_settings
    settings = get_settings()
    settings.use_mock_db = True
    from app.core import database
    from app.core.database import get_db
    from app.services.policy_service import PolicyService
    from app.models.policy import PolicyStatus
    
    db = next(get_db())
    policy = PolicyService.confirm_enrollment(db, state["policy_id"], state["tx_ref"])
    
    if policy.status == PolicyStatus.ACTIVE:
        print("Policy Activated Successfully")
    else:
        print(f"FAIL: Policy status is {policy.status}")
        sys.exit(1)

def step_create_claim():
    print("[Step 5] Creating Claim (Python)...")
    state = load_state()
    sys.path.append(CLAIMS_MS_DIR)
    import os
    os.environ["JWT_SECRET"] = "test"
    from app.core.config import get_settings
    settings = get_settings()
    settings.use_mock_db = True
    from app.core import database
    from app.core.database import get_db
    from app.models.claim import Claim, ClaimStatus
    
    db = next(get_db())
    c = Claim(
        user_id=state["user_id"],
        subscription_id=state["policy_id"],
        incident_number="CLM-E2E-001",
        incident_type="health",
        description="E2E Flow Claim",
        reported_amount=10000,
        image_hashes=["hash1", "hash2"],
        status=ClaimStatus.SUBMITTED
    )
    db.add(c)
    db.commit()
    print(f"Claim Created: {c.id}")
    state["claim_id"] = str(c.id)
    save_state(state)

# ==================== ORCHESTRATOR ====================

def run_orchestrator():
    print("=== Starting E2E Mock Verification Flow ===")
    
    # Cleanup
    # Note: State file is in BASE_DIR. Service mock DBs are in valid service dirs.
    cleanup_files = [
        STATE_FILE,
        os.path.join(POLICY_MS_DIR, "mock_db.json"),
        os.path.join(CLAIMS_MS_DIR, "claims_mock_db.json")
    ]
    for f in cleanup_files:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass
            
    SCRIPT_PATH = os.path.abspath(__file__)

    # 1. Run Step 1 (Create Policy) - Run in Policy Dir
    subprocess.run([sys.executable, SCRIPT_PATH, "step_create_policy"], env=ENV_POLICY, cwd=POLICY_MS_DIR, check=True)
    
    # 2. Start Go Service
    print("[Step 2] Starting Payment Service (Go)...")
    go_path = r"C:\Program Files\Go\bin\go.exe"
    proc_payment = subprocess.Popen(
        [go_path, "run", "."], cwd=PAYMENT_MS_DIR, env=ENV_PAYMENT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    
    try:
        # Wait for healthy
        time.sleep(5)
        
        # Load state to get params
        state = load_state()
        
        # Call Payment API
        import jwt, uuid
        token = jwt.encode({"sub": state["user_id"], "role": "USER", "exp": int(time.time()) + 3600}, "dev-secret-change-in-production", algorithm="HS256")
        
        print("Initiating Payment...")
        resp = requests.post("http://localhost:8082/api/v1/payments/initiate", json={
            "user_id": state["user_id"],
            "policy_id": state["policy_id"],
            "amount": state["amount"],
            "currency": "XOF",
            "phone": "07000000",
            "provider": "orange",
            "idempotency_key": str(uuid.uuid4())
        }, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code >= 400:
            print(f"Payment API Error: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        tx_ref = data["transaction_ref"]
        print(f"Payment Successful. Ref: {tx_ref}")
        
        state["tx_ref"] = tx_ref
        save_state(state)
        
        # 3. Run Step 3 (Activate)
        subprocess.run([sys.executable, SCRIPT_PATH, "step_activate_policy"], env=ENV_POLICY, cwd=POLICY_MS_DIR, check=True)
        
        # 4. Run Step 5 (Create Claim) - Intentionally skipping Step 4 (Verify Payment) as Activate implies it
        subprocess.run([sys.executable, SCRIPT_PATH, "step_create_claim"], env=ENV_CLAIMS, cwd=CLAIMS_MS_DIR, check=True)
        
        print("\n=== E2E Flow Completed Successfully ===")
        
    except Exception as e:
        print(f"\nFAIL: E2E Flow Failed: {e}")
        if proc_payment.poll() is not None:
            print("Payment Service Output:")
            print(proc_payment.stdout.read())
            print(proc_payment.stderr.read())
            
    finally:
        print("Stopping Payment Service...")
        proc_payment.terminate()
        try:
            proc_payment.wait(timeout=2)
        except:
             proc_payment.kill()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "step_create_policy":
            step_create_policy()
        elif cmd == "step_activate_policy":
            step_activate_policy()
        elif cmd == "step_create_claim":
            step_create_claim()
    else:
        run_orchestrator()
