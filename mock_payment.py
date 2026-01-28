from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid

app = FastAPI(title="Wali Mock Payment Service (Python)")

# CORS to allow PWA access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PaymentInit(BaseModel):
    amount: float
    provider: str
    phone_number: str
    policy_id: str
    user_id: str

@app.post("/api/v1/payments/initiate")
async def initiate_payment(data: PaymentInit):
    print(f"💰 Initiating Payment: {data.amount} FCFA via {data.provider} for {data.phone_number}")
    return {
        "status": "pending",
        "reference": str(uuid.uuid4()),
        "payment_url": "http://localhost:3000/payment-success-mock", # Mock redirection
        "message": "Payment initiated successfully"
    }

@app.get("/api/v1/payments/verify/{ref}")
async def verify_payment(ref: str, provider: str):
    print(f"✅ Verifying Payment: {ref} ({provider})")
    # Always simulate success for local dev
    return {
        "status": "success",
        "reference": ref,
        "provider": provider,
        "transaction_id": f"TXN_{ref[:8]}",
        "amount": 5000,
        "currency": "XOF"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "mock-payment-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
