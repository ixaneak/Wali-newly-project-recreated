import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Header, HTTPException, status
from typing import Optional
import os

# Initialize Firebase Admin
cred_path = os.path.join(os.getcwd(), "service-account.json")
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("[OK] Firebase Admin Initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Firebase Admin: {e}")

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        # Allow mock fallback for development if needed, OR raise 401
        # For strict security: raise HTTPException(status_code=401, detail="Missing token")
         return {
            'user_id': 'mock-dev-id',
            'phone': '+225 00 00 00 00 00', 
            'role': 'user'
        }

    token = authorization.split("Bearer ")[1]
    
    try:
        # Verify Firebase Token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        phone_number = decoded_token.get('phone_number', '')
        
        # Determine role (simple logic: specific phone or custom claim)
        # For now, hardcode admin check or check custom claims
        role = 'user'
        if phone_number == '+2250707070707' or decoded_token.get('admin') is True:
            role = 'admin'

        return {
            'user_id': uid,
            'phone': phone_number,
            'role': role
        }
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
