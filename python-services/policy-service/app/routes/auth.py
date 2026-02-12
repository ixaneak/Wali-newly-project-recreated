from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import random
import logging
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
settings = get_settings()

class OTPRequest(BaseModel):
    phoneNumber: str
    recaptchaToken: str

# In-memory store for dev/demo purposes (Use Redis in production)
# Structure: {phone_number: {"code": "123456", "expires": timestamp}}
otp_store = {} 

async def verify_recaptcha(token: str) -> float:
    """Verifies reCAPTCHA v3 token and returns score."""
    # SKIP verification in test mode for specific tokens if needed, 
    # but strictly we should verify with Google
    
    # If no secret key is configured, warn and bypass (Dev Mode)
    # settings.recaptcha_secret_key needed
    secret_key = "YOUR_RECAPTCHA_SECRET_KEY" # TODO: Load from env
    
    if not secret_key or secret_key == "YOUR_RECAPTCHA_SECRET_KEY":
        logger.warning("Recaptcha secret not configured. Bypassing verification.")
        return 1.0

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": secret_key,
                    "response": token
                }
            )
            result = response.json()
            if not result.get("success"):
                logger.warning(f"Recaptcha verification failed: {result}")
                return 0.0
            return result.get("score", 0.0)
        except Exception as e:
            logger.error(f"Recaptcha connection error: {e}")
            raise HTTPException(status_code=500, detail="Security check failed")

@router.post("/send-otp")
async def send_otp(data: OTPRequest):
    logger.info(f"Received OTP request for {data.phoneNumber}")
    
    # 1. Verify reCAPTCHA
    # score = await verify_recaptcha(data.recaptchaToken)
    # if score < 0.5:
    #     logger.warning(f"Low recaptcha score: {score} for {data.phoneNumber}")
    #     raise HTTPException(status_code=403, detail="Suspicious activity detected")
    
    # 2. Generate OTP
    if data.phoneNumber == "+2250701010101" or data.phoneNumber.endswith("0701010101"):
        otp_code = "123456"
        logger.info(f"Test number detected, using fixed OTP: {otp_code}")
    else:
        otp_code = f"{random.randint(0, 999999):06d}"
    
    # 3. Store OTP (Mock Redis)
    otp_store[data.phoneNumber] = otp_code
    logger.info(f"Generated OTP for {data.phoneNumber}: {otp_code}")
    
    # 4. Send SMS via Africa's Talking (Mock)
    # In prod: AfricasTalkingGateway(username, key).sendMessage(phone, msg)
    print(f"===========================================")
    print(f"SMS to {data.phoneNumber}: Votre code Wali est {otp_code}")
    print(f"===========================================")
    
    return {"status": "success", "message": "OTP sent"}

@router.post("/verify-otp")
async def verify_otp(phoneNumber: str, code: str):
    stored_code = otp_store.get(phoneNumber)
    if not stored_code:
        raise HTTPException(status_code=400, detail="No OTP request found")
        
    if stored_code == code:
        # Success!
        # Generate Firebase Custom Token here (requires firebase-admin)
        # uid = get_or_create_user(phoneNumber)
        # token = auth.create_custom_token(uid)
        
        # for now return mock
        del otp_store[phoneNumber]
        return {"status": "success", "token": "mock-custom-token-backend"}
        
    raise HTTPException(status_code=400, detail="Invalid code")
