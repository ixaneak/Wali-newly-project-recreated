from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.database import get_db
from app.models.pharmacy import PharmacyPartner, SubscriptionStatus
from app.core.config import get_settings

router = APIRouter(
    prefix="/api/v1/pharmacy",
    tags=["Pharmacy B2B SaaS"],
)

settings = get_settings()

# Security Config
SECRET_KEY = settings.jwt_secret or "CHANGE_THIS_IN_PRODUCTION_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours for B2B

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Schemas ─────────────────────────────────────────────────────

class PharmacyLoginRequest(BaseModel):
    email: str
    password: str

class VerificationRequest(BaseModel):
    qr_token: str # Format: PHONE:POLICY_ID

class ReimbursementRequest(BaseModel):
    artisan_phone: str
    amount: float
    medication_code: str

# ── Helpers ─────────────────────────────────────────────────────

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ── Dependency ──────────────────────────────────────────────────

def get_current_pharmacy(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    pharma = db.query(PharmacyPartner).filter(PharmacyPartner.api_key == x_api_key).first()
    if not pharma:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    # Check Subscription
    if not pharma.check_subscription():
        db.commit() # Save status update
        raise HTTPException(
            status_code=402, 
            detail="Subscription Required. Trial Ended or Suspended."
        )
        
    return pharma

# ── Endpoints ───────────────────────────────────────────────────

@router.post("/auth/login")
def login(credentials: PharmacyLoginRequest, db: Session = Depends(get_db)):
    print(f"🔔 LOGIN ATTEMPT: {credentials.email}")
    
    # HARDCODED BYPASS FOR DEBUGGING
    if (credentials.email == "pharmacie@wali.com" or credentials.email == "pharmacy@wali.com") and credentials.password == "pharma1234":
        print("✅ DEBUG: Bypassing DB for pharmacie@wali.com")
        return {
            "access_token": "debug_token",
            "token_type": "bearer",
            "business_name": "Pharmacie Debug",
            "subscription_status": "trial",
            "api_key": "debug_key"
        }

    # 1. CHECK IF EXISTS
    try:
        pharma = db.query(PharmacyPartner).filter(PharmacyPartner.email == credentials.email).first()
        print(f"📊 DB RESULT: {pharma}")
    except Exception as e:
        print(f"❌ DB ERROR: {str(e)}")
        # If we failed to query, maybe the table is missing as user suggested
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    
    # 2. AUTO-CREATE ONLY IF NEW (Demo/Dev mode)
    if not pharma:
        # Create demo account only for specific emails
        if credentials.email in ['pharmacie@wali.com', 'pharmacy@wali.com', 'demo@wali.com', 'pharmacie@demo.ci']:
             print("🆕 Creating new pharmacy...")
             try:
                 pharma = PharmacyPartner(
                     email=credentials.email,
                     password_hash=get_password_hash(credentials.password),
                     business_name="Pharmacie Demo",
                     subscription_status=SubscriptionStatus.TRIAL,
                     api_key=secrets.token_urlsafe(32)
                 )
                 db.add(pharma)
                 db.commit()
                 db.refresh(pharma)
             except Exception as e:
                 print(f"❌ CREATE ERROR: {str(e)}")
                 raise HTTPException(status_code=500, detail=f"Create Failed: {str(e)}")
        else:
            raise HTTPException(status_code=401, detail="Email non reconnu")
    
    # 3. VERIFY PASSWORD
    else:
        if not verify_password(credentials.password, pharma.password_hash):
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    
    # 4. CHECK SUBSCRIPTION
    if not pharma.check_subscription():
        db.commit()
        raise HTTPException(
            status_code=403, 
            detail="Période d'essai terminée. Payez 50,000 FCFA."
        )
    
    # 5. GENERATE TOKEN
    access_token = create_access_token(
        data={
            "sub": str(pharma.id), 
            "role": "pharmacy", 
            "email": pharma.email,
            "name": pharma.business_name
        }
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "business_name": pharma.business_name,
        "subscription_status": pharma.subscription_status.value,
        "api_key": pharma.api_key
    }

@router.get("/stats")
def get_stats(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Get pharmacy dashboard stats. Supports debug_key for demo mode."""
    print(f"📊 STATS REQUEST: api_key={x_api_key}")
    
    # Debug/demo mode
    if x_api_key == "debug_key":
        from datetime import datetime, timedelta
        return {
            "id": "debug-pharmacy-id",
            "name": "Pharmacie Demo",
            "email": "pharmacie@wali.com",
            "subscription_status": "trial",
            "trial_ends_at": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "verifications_today": 12,
            "api_quota_remaining": 488,
            "api_key": "debug_key",
        }
    
    # Real mode: look up pharmacy by API key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    pharma = db.query(PharmacyPartner).filter(PharmacyPartner.api_key == x_api_key).first()
    if not pharma:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return {
        "id": str(pharma.id),
        "name": pharma.business_name,
        "email": pharma.email,
        "subscription_status": pharma.subscription_status.value if pharma.subscription_status else "trial",
        "trial_ends_at": pharma.trial_ends_at.isoformat() if hasattr(pharma, 'trial_ends_at') and pharma.trial_ends_at else None,
        "verifications_today": getattr(pharma, 'verifications_today', 0),
        "api_quota_remaining": getattr(pharma, 'api_quota_remaining', 500),
        "api_key": pharma.api_key,
    }

@router.post("/verify")
def verify_claim(request: VerificationRequest, pharma: PharmacyPartner = Depends(get_current_pharmacy), db: Session = Depends(get_db)):
    # Simple placeholder for now
    return {"status": "verified", "message": "Coverage confirmed"}

@router.post("/reimburse")
def request_reimbursement(request: ReimbursementRequest, pharma: PharmacyPartner = Depends(get_current_pharmacy), db: Session = Depends(get_db)):
    # Simple placeholder for now
    return {"status": "requested", "message": "Reimbursement request submitted"}
