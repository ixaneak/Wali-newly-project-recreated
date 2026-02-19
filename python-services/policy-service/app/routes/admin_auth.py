from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.secure_auth import verify_password, create_access_token, log_security_event
from app.models.policy import User, UserRole
import logging

import os
from app.core.config import get_settings

router = APIRouter(prefix="/auth/admin", tags=["auth"])
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Prevent enumeration
        log_security_event("admin_login_failed_user_not_found", details={"email": request.email}, severity="warning")
        logger.warning(f"Admin login failed: User not found {request.email}")
        raise HTTPException(status_code=400, detail="Identifiants invalides")
    
    if user.role != UserRole.ADMIN:
        log_security_event("admin_login_failed_role_mismatch", details={"email": request.email, "role": user.role}, severity="warning")
        logger.warning(f"Admin login failed: Invalid role {user.role} for {request.email}")
        raise HTTPException(status_code=403, detail="Accès non autorisé")
        
    is_valid = verify_password(request.password, user.password_hash)

    if not user.password_hash or not is_valid:
        log_security_event("admin_login_failed_bad_password", user_id=user.id, severity="warning")
        logger.warning(f"Admin login failed: Invalid password for {request.email}")
        raise HTTPException(status_code=400, detail="Identifiants invalides")
        
    # Success
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    log_security_event("admin_login_success", user_id=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }
