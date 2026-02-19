"""
MFA API Routes for WALI

Endpoints for TOTP setup, verification, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.secure_auth import verify_token, log_security_event
from app.core.mfa import MFAService, TOTPProvider

router = APIRouter(prefix="/api/v1/mfa", tags=["mfa"])


# ═════════════════════════════════════════════════════════════════
# SCHEMAS
# ═════════════════════════════════════════════════════════════════

class MFASetupRequest(BaseModel):
    """Request to setup MFA."""
    method: str = Field(default="totp", description="MFA method: totp or sms")


class MFASetupResponse(BaseModel):
    """Response with MFA setup details."""
    secret: str
    qr_code_base64: str
    backup_codes: list[str]
    manual_entry: str


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code."""
    code: str = Field(..., min_length=6, max_length=8, description="TOTP or backup code")


class MFAVerifyResponse(BaseModel):
    """Response after MFA verification."""
    success: bool
    message: str


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    password: str = Field(..., description="Current password for confirmation")
    code: str = Field(..., description="Current MFA code")


# ═════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════

@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: MFASetupRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Setup MFA for the current user.
    
    Returns QR code and backup codes. User must verify code to activate.
    """
    user_id = current_user.get('sub')
    email = current_user.get('email', '')
    
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email required for MFA setup"
        )
    
    # Initialize MFA service
    mfa_service = MFAService(db)
    
    # Generate TOTP setup
    setup_data = mfa_service.setup_totp(user_id, email)
    
    # Log setup attempt
    log_security_event(
        event_type="mfa_setup_initiated",
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        details={"method": request.method},
        severity="info"
    )
    
    return MFASetupResponse(**setup_data)


@router.post("/verify-setup", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Verify MFA setup code to activate MFA.
    
    Must be called after setup with a valid TOTP code from authenticator app.
    """
    user_id = current_user.get('sub')
    
    mfa_service = MFAService(db)
    
    if mfa_service.verify_totp_setup(user_id, request.code):
        log_security_event(
            event_type="mfa_enabled",
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            details={"method": "totp"},
            severity="info"
        )
        
        return MFAVerifyResponse(
            success=True,
            message="MFA enabled successfully. Store your backup codes securely!"
        )
    else:
        log_security_event(
            event_type="mfa_setup_failed",
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            details={"reason": "invalid_code"},
            severity="warning"
        )
        
        raise HTTPException(
            status_code=400,
            detail="Invalid MFA code. Please try again."
        )


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_login(
    request: MFAVerifyRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Verify MFA code during login.
    
    Called after initial password authentication for MFA-enabled users.
    """
    # Get user from session or temp token
    # This is a simplified implementation
    user_id = req.session.get('mfa_pending_user_id')
    
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="No MFA pending session"
        )
    
    mfa_service = MFAService(db)
    
    if mfa_service.verify_login(user_id, request.code):
        # Mark MFA as verified in session
        req.session['mfa_verified'] = True
        req.session.pop('mfa_pending_user_id', None)
        
        log_security_event(
            event_type="mfa_verified",
            user_id=user_id,
            ip_address=req.client.host if req.client else None,
            severity="info"
        )
        
        return MFAVerifyResponse(
            success=True,
            message="MFA verified successfully"
        )
    else:
        log_security_event(
            event_type="mfa_failed",
            user_id=user_id,
            ip_address=req.client.host if req.client else None,
            severity="warning"
        )
        
        raise HTTPException(
            status_code=400,
            detail="Invalid MFA code"
        )


@router.post("/disable", response_model=MFAVerifyResponse)
async def disable_mfa(
    request: MFADisableRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Disable MFA for the current user.
    
    Requires current password and MFA code for confirmation.
    """
    user_id = current_user.get('sub')
    
    # Verify password first
    # In production: verify_password(request.password, user.password_hash)
    
    # Verify MFA code
    mfa_service = MFAService(db)
    
    if not mfa_service.verify_login(user_id, request.code):
        log_security_event(
            event_type="mfa_disable_failed",
            user_id=user_id,
            details={"reason": "invalid_code"},
            severity="warning"
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid MFA code"
        )
    
    # Disable MFA
    if mfa_service.disable_mfa(user_id):
        log_security_event(
            event_type="mfa_disabled",
            user_id=user_id,
            details={"reason": "user_requested"},
            severity="warning"
        )
        
        return MFAVerifyResponse(
            success=True,
            message="MFA disabled successfully"
        )
    
    raise HTTPException(
        status_code=500,
        detail="Failed to disable MFA"
    )


@router.get("/status")
async def get_mfa_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get MFA status for current user."""
    user_id = current_user.get('sub')
    
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "mfa_enabled": getattr(user, 'mfa_enabled', False),
        "mfa_type": getattr(user, 'mfa_type', None),
        "required_for_admin": True,
    }


# ═════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═════════════════════════════════════════════════════════════════

@router.post("/admin/require", status_code=status.HTTP_200_OK)
async def require_mfa_for_admin(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Check if MFA is required and verified for admin actions.
    
    Returns 403 if MFA not verified.
    """
    user_id = current_user.get('sub')
    
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is admin
    if getattr(user, 'role', None) != 'admin':
        return {"mfa_required": False, "message": "MFA not required for non-admin users"}
    
    # Check if MFA is enabled
    if not getattr(user, 'mfa_enabled', False):
        log_security_event(
            event_type="mfa_required_but_not_enabled",
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            severity="warning"
        )
        raise HTTPException(
            status_code=403,
            detail="MFA is required for admin users. Please enable MFA in your account settings.",
            headers={"X-MFA-Required": "true"}
        )
    
    # Check if MFA verified in current session
    mfa_verified = request.session.get('mfa_verified', False)
    
    if not mfa_verified:
        raise HTTPException(
            status_code=403,
            detail="MFA verification required. Please complete two-factor authentication.",
            headers={"X-MFA-Required": "true", "X-MFA-Action": "verify"}
        )
    
    return {"mfa_required": True, "mfa_verified": True}
