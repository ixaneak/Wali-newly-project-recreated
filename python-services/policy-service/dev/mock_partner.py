from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockNSIA")

app = FastAPI(title="Mock NSIA Partner API", description="Simulates Insurer Core System")

# In-memory storage for simplicity
QUOTES = {}
POLICIES = {}
PAYMENTS = {}

class QuoteRequest(BaseModel):
    product_code: str
    coverage_amount: int

class PaymentConfirmation(BaseModel):
    payment_id: str
    amount: int
    timestamp: datetime

@app.get("/health")
def health_check():
    return {"status": "ok", "role": "insurer", "partner": "NSIA"}

@app.post("/v1/quotes")
async def create_quote(request: QuoteRequest):
    """
    Simulate underwriting: The PARTNER sets the price, not Wali.
    """
    logger.info(f"Received quote request for {request.product_code}")
    
    # Simple logic to simulate complex actuarial pricing
    if request.product_code == "micro-health":
        premium = 500  # Fixed price for health
    elif request.product_code == "accident-protection":
        premium = 1000
    else:
        # Dynamic pricing simulation
        premium = int(request.coverage_amount * 0.01) 

    quote_id = f"QUOTE-{uuid.uuid4().hex[:8].upper()}"
    
    quote = {
        "quote_id": quote_id,
        "product_code": request.product_code,
        "premium_amount": premium,
        "currency": "XOF",
        "valid_until": datetime.now().isoformat(),
        "underwritten_by": "NSIA Assurances",
        "terms": "Coverage subject to waiting period of 30 days."
    }
    
    QUOTES[quote_id] = quote
    return quote

@app.post("/v1/coverage/activate")
async def activate_coverage(quote_id: str, payment_ref: str):
    """
    Simulate policy issuance. Only the insurer can issue a policy.
    """
    if quote_id not in QUOTES:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    policy_id = f"NSIA-POL-{uuid.uuid4().hex[:8].upper()}"
    
    policy = {
        "policy_id": policy_id,
        "quote_id": quote_id,
        "status": "ACTIVE",
        "effective_date": datetime.now().isoformat(),
        "payment_ref": payment_ref,
        "certificate_url": f"https://mock-nsia.ci/certificates/{policy_id}"
    }
    
    POLICIES[policy_id] = policy
    logger.info(f"Policy issued: {policy_id}")
    return policy

@app.get("/v1/collection-account")
async def get_collection_account():
    """
    Returns the account where money should be sent.
    """
    return {
        "bank_name": "Ecobank CI",
        "account_number": "CI059 01001 12345678901 22",
        "mobile_money_merchant_id": "NSIA-COLLECTION-123",
        "account_holder": "NSIA Assurances SA"
    }

@app.post("/v1/webhooks/payment-received")
async def payment_webhook(data: PaymentConfirmation):
    """
    Webhook: Partner confirms they received money.
    In real life, this would call Wali's webhook to confirm enrollment.
    """
    logger.info(f"Money received by NSIA: {data.amount} XOF (Ref: {data.payment_id})")
    return {"status": "processed", "reconciliation_id": uuid.uuid4().hex}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
