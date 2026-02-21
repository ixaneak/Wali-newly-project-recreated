import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.pharmacy import PharmacyPartner, SubscriptionStatus
from app.models.policy import CoverageSubscription as Subscription, User

# Configure logger
logger = logging.getLogger(__name__)

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

class PharmacyVerifyRequest(BaseModel):
    """Request schema for pharmacy verification."""
    qr_token: str = Field(..., description="The QR token scanned from the policy card")
    location_lat: Optional[float] = Field(None, description="Latitude of the pharmacy")
    location_lon: Optional[float] = Field(None, description="Longitude of the pharmacy")

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
    logger.info(f"Pharmacy login attempt: {credentials.email}")
    
    # SECURITY: No debug bypass - all authentication goes through database
    
    # 1. CHECK IF EXISTS
    try:
        pharma = db.query(PharmacyPartner).filter(PharmacyPartner.email == credentials.email).first()
        logger.debug(f"Pharmacy lookup result: {'found' if pharma else 'not found'}")
    except Exception as e:
        logger.error(f"Database error during pharmacy login: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication service error")
    
    # 2. AUTO-CREATE ONLY IF NEW (Development mode only with explicit flag)
    if not pharma:
        # Only auto-create in development with explicit enablement
        if (settings.environment == "development" and 
            getattr(settings, 'allow_demo_account_creation', False) and
            credentials.email in ['pharmacie@wali.com', 'pharmacy@wali.com', 'demo@wali.com']):
             logger.info(f"Auto-creating demo pharmacy account: {credentials.email}")
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
                 logger.error(f"Failed to create demo pharmacy: {str(e)}")
                 raise HTTPException(status_code=500, detail="Account creation failed")
        else:
            # In production, don't auto-create - require proper registration
            logger.warning(f"Login attempt for non-existent pharmacy: {credentials.email}")
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
    """Get pharmacy dashboard stats."""
    logger.debug(f"Stats request for API key: {x_api_key[:8]}..." if x_api_key else "No API key provided")
    
    # SECURITY: No debug key bypass - all requests must be authenticated
    
    # Validate API key presence
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
def verify_claim(
    request: PharmacyVerifyRequest, 
    pharma: PharmacyPartner = Depends(get_current_pharmacy), 
    db: Session = Depends(get_db)
):
    """
    Verify a member's coverage using QR token, member ID, or phone number.
    
    Returns coverage details if active, or appropriate status message if
    coverage is inactive or expired.
    """
    # 1. Validate input
    if not request.qr_token:
        raise HTTPException(status_code=400, detail="QR Token required")
    
    try:
        # 2. Look up by QR token
        subscription = db.query(Subscription).filter(
            Subscription.qr_token == request.qr_token
        ).first()
        
        # 3. Fallback: check if it's a member ID or Phone
        if not subscription:
            subscription = db.query(Subscription).join(User).filter(
                (User.id == request.qr_token) | 
                (User.phone == request.qr_token) | 
                (Subscription.subscription_number == request.qr_token)
            ).first()
    except Exception as e:
        logger.error(f"Database error during coverage verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification service error"
        )

    if not subscription:
        raise HTTPException(
            status_code=404, 
            detail="Couverture non trouvée ou code invalide"
        )
        
    # 2. Check Status
    if subscription.status != SubscriptionStatus.ACTIVE:
        return {
            "status": "inactive",
            "message": f"Assurance inactive ({subscription.status.value})"
        }
        
    # 3. Check Expiration
    if subscription.qr_expires_at and subscription.qr_expires_at < datetime.utcnow():
        return {
            "status": "expired",
            "message": "Code QR expiré. Veuillez rafraîchir la carte."
        }
        
    # 4. Success - Return Member Details
    # We need to fetch user details. The relationship might be lazy.
    user = db.query(User).filter(User.id == subscription.user_id).first()
    
    return {
        "status": "active",
        "memberId": subscription.subscription_number,
        "name": user.name if user else "Unknown",
        "plan": subscription.partner_product_id,
        "coverageLimit": 80, # Hardcoded for now, or fetch from config
        "copay": 20,
        "lastPayment": subscription.last_payment_date.strftime("%Y-%m-%d") if subscription.last_payment_date else "N/A"
    }

@router.post("/reimburse")
def request_reimbursement(
    request: ReimbursementRequest, 
    pharma: PharmacyPartner = Depends(get_current_pharmacy), 
    db: Session = Depends(get_db)
):
    """
    Submit a reimbursement request for processed medication.
    
    This is a placeholder endpoint - full implementation requires:
    - Medication code validation
    - Amount verification against coverage
    - Receipt upload handling
    - Partner insurer approval workflow
    """
    logger.info(
        f"Reimbursement request from {pharma.business_name}: "
        f"artisan={request.artisan_phone}, amount={request.amount}"
    )
    
    # Validation
    if request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # TODO-PROD: Implement full reimbursement workflow
    # 1. Validate artisan coverage
    # 2. Verify medication is in formulary
    # 3. Check amount against remaining coverage
    # 4. Create reimbursement record
    # 5. Submit to partner insurer for approval
    
    return {
        "status": "requested", 
        "message": "Reimbursement request submitted for review",
        "pharmacy_id": str(pharma.id),
        "amount_requested": request.amount,
        "estimated_processing_days": 3
    }
