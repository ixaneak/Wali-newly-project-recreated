"""
Multi-Factor Authentication (MFA) for WALI

Implements TOTP (Time-based One-Time Password) for admin users.
CIMA Requirement: MFA required for privileged access.

Supports:
- TOTP (Google Authenticator, Authy)
- SMS OTP (Twilio)
- Backup codes
"""

import os
import secrets
import logging
from typing import Optional, List
from datetime import datetime, timedelta

import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from app.core.secure_auth import verify_token

logger = logging.getLogger(__name__)


class MFAProvider:
    """Base class for MFA providers."""
    
    def generate_secret(self) -> str:
        """Generate a new MFA secret."""
        return pyotp.random_base32()
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Verify an MFA code."""
        raise NotImplementedError
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery."""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            codes.append(code)
        return codes


class TOTPProvider(MFAProvider):
    """
    Time-based One-Time Password (TOTP) implementation.
    
    Compatible with:
    - Google Authenticator
    - Authy
    - Microsoft Authenticator
    - 1Password
    """
    
    def __init__(self, issuer: str = "WALI"):
        self.issuer = issuer
        self.digits = 6
        self.interval = 30  # 30 seconds
    
    def get_provisioning_uri(self, secret: str, account_name: str) -> str:
        """
        Generate provisioning URI for QR code.
        
        Args:
            secret: The MFA secret
            account_name: User's email or username
            
        Returns:
            otpauth:// URI for QR code
        """
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        return totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer
        )
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """
        Generate QR code as base64 SVG.
        
        Args:
            provisioning_uri: The otpauth:// URI
            
        Returns:
            Base64-encoded SVG QR code
        """
        factory = qrcode.image.svg.SvgImage
        qr = qrcode.make(provisioning_uri, image_factory=factory)
        
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)
        
        svg_data = buffer.getvalue().decode()
        return base64.b64encode(svg_data.encode()).decode()
    
    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code.
        
        Args:
            secret: The MFA secret
            code: Code to verify
            window: Time window tolerance (±windows * 30 seconds)
            
        Returns:
            True if code is valid
        """
        if not secret or not code:
            return False
        
        # Clean code (remove spaces)
        code = code.replace(' ', '').strip()
        
        # Validate format
        if not code.isdigit() or len(code) != self.digits:
            return False
        
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        
        # Verify with time window
        return totp.verify(code, valid_window=window)


class SMSProvider(MFAProvider):
    """
    SMS-based OTP provider.
    Uses Twilio for Ivory Coast (+225) numbers.
    """
    
    def __init__(self):
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        self.code_length = 6
        self.code_validity = 300  # 5 minutes
    
    def is_configured(self) -> bool:
        """Check if Twilio is configured."""
        return all([self.twilio_sid, self.twilio_token, self.twilio_phone])
    
    def generate_code(self) -> str:
        """Generate numeric OTP."""
        return ''.join(secrets.choice('0123456789') for _ in range(self.code_length))
    
    def send_sms(self, phone_number: str, code: str) -> bool:
        """
        Send OTP via SMS.
        
        Args:
            phone_number: Ivory Coast phone number (+225...)
            code: OTP code
            
        Returns:
            True if SMS sent successfully
        """
        if not self.is_configured():
            logger.error("Twilio not configured")
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_sid, self.twilio_token)
            
            message = client.messages.create(
                body=f"Votre code de verification WALI: {code}. Valide pendant 5 minutes.",
                from_=self.twilio_phone,
                to=phone_number
            )
            
            logger.info(f"SMS sent to {phone_number}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def verify_code(self, stored_code: str, provided_code: str, 
                    generated_at: datetime) -> bool:
        """
        Verify SMS code.
        
        Args:
            stored_code: The code sent via SMS
            provided_code: Code entered by user
            generated_at: When the code was generated
            
        Returns:
            True if code is valid and not expired
        """
        if not stored_code or not provided_code:
            return False
        
        # Check expiry
        if datetime.utcnow() - generated_at > timedelta(seconds=self.code_validity):
            return False
        
        # Constant-time comparison
        return secrets.compare_digest(stored_code.strip(), provided_code.strip())


# ═════════════════════════════════════════════════════════════════
# MFA Service for Application Use
# ═════════════════════════════════════════════════════════════════

class WhatsAppOTPProvider:
    """
    WhatsApp-based OTP provider.
    Uses WhatsApp Business API - cheaper than SMS in Ivory Coast.
    """
    
    def __init__(self):
        # Import from whatsapp_otp module
        try:
            from app.core.whatsapp_otp import WhatsAppOTPProvider as WAProvider
            self.provider = WAProvider()
            self.available = True
        except ImportError:
            logger.warning("WhatsApp OTP module not available")
            self.provider = None
            self.available = False
    
    def is_configured(self) -> bool:
        """Check if WhatsApp is configured."""
        if not self.available:
            return False
        return self.provider.is_configured()
    
    def generate_code(self) -> str:
        """Generate OTP code."""
        if self.provider:
            return self.provider.generate_code()
        # Fallback
        import secrets
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    def send_otp(self, phone_number: str, code: str, name: str = "") -> bool:
        """Send OTP via WhatsApp."""
        if not self.provider:
            return False
        
        result = self.provider.send_otp(phone_number, code, name)
        return result.get('success', False)
    
    def verify_code(self, stored_code: str, provided_code: str, 
                    generated_at: datetime) -> bool:
        """Verify OTP code."""
        if not stored_code or not provided_code:
            return False
        
        # Check expiry (5 minutes)
        if datetime.utcnow() - generated_at > timedelta(seconds=300):
            return False
        
        return secrets.compare_digest(stored_code.strip(), provided_code.strip())


class MFAService:
    """
    Main MFA service for WALI.
    
    Supports TOTP (for admins) and WhatsApp/SMS OTP (for users).
    
    OTP Strategy (cost-optimized):
    1. Try WhatsApp first (cheapest, ~$0.00-0.01 per message)
    2. Fall back to SMS if WhatsApp fails (~$0.05-0.10 per message)
    
    Usage:
        mfa = MFAService()
        
        # Setup TOTP MFA for admin
        secret = mfa.setup_totp(user_id, email)
        
        # Send OTP to user (WhatsApp preferred)
        result = mfa.send_user_otp(phone, name)
    """
    
    def __init__(self, db_session=None):
        self.totp = TOTPProvider()
        self.whatsapp = WhatsAppOTPProvider()
        self.sms = SMSProvider()
        self.db = db_session
    
    def send_user_otp(self, phone_number: str, name: str = "") -> dict:
        """
        Send OTP to user with automatic fallback (WhatsApp → SMS).
        
        Args:
            phone_number: User's phone number
            name: User's name (optional, for personalization)
            
        Returns:
            {
                'success': bool,
                'code': str (store this securely),
                'provider': 'whatsapp' | 'sms' | 'none',
                'message': str
            }
        """
        # Generate code
        code = self.whatsapp.generate_code()
        
        # Try WhatsApp first (cheaper)
        if self.whatsapp.is_configured():
            logger.info(f"Trying WhatsApp OTP for {phone_number}")
            success = self.whatsapp.send_otp(phone_number, code, name)
            
            if success:
                logger.info(f"WhatsApp OTP sent successfully to {phone_number}")
                return {
                    'success': True,
                    'code': code,
                    'provider': 'whatsapp',
                    'message': 'Code envoyé via WhatsApp'
                }
            else:
                logger.warning(f"WhatsApp failed, will try SMS for {phone_number}")
        
        # Fallback to SMS
        if self.sms.is_configured():
            logger.info(f"Trying SMS OTP for {phone_number}")
            success = self.sms.send_sms(phone_number, code)
            
            if success:
                logger.info(f"SMS OTP sent successfully to {phone_number}")
                return {
                    'success': True,
                    'code': code,
                    'provider': 'sms',
                    'message': 'Code envoyé par SMS'
                }
        
        # Both failed
        logger.error(f"Failed to send OTP to {phone_number} via any provider")
        return {
            'success': False,
            'code': None,
            'provider': 'none',
            'message': 'Échec de l\'envoi du code. Veuillez réessayer.'
        }
    
    def setup_totp(self, user_id: str, email: str) -> dict:
        """
        Setup TOTP MFA for a user.
        
        Returns:
            Dictionary with secret and QR code
        """
        secret = self.totp.generate_secret()
        
        # Store secret in database (encrypted)
        # In production, encrypt the secret before storing
        if self.db:
            from app.models.user import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.mfa_secret = secret
                user.mfa_enabled = False  # Not verified yet
                user.mfa_type = 'totp'
                self.db.commit()
        
        # Generate QR code
        uri = self.totp.get_provisioning_uri(secret, email)
        qr_code = self.totp.generate_qr_code(uri)
        
        # Generate backup codes
        backup_codes = self.totp.generate_backup_codes()
        
        return {
            'secret': secret,
            'qr_code_base64': qr_code,
            'backup_codes': backup_codes,
            'manual_entry': secret,  # For manual entry
        }
    
    def verify_totp_setup(self, user_id: str, code: str) -> bool:
        """
        Verify TOTP code during setup to confirm MFA is working.
        
        Returns:
            True if code is valid, MFA is then enabled
        """
        if not self.db:
            return False
        
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.mfa_secret:
            return False
        
        if self.totp.verify_code(user.mfa_secret, code):
            # Enable MFA
            user.mfa_enabled = True
            self.db.commit()
            logger.info(f"MFA enabled for user {user_id}")
            return True
        
        return False
    
    def verify_login(self, user_id: str, code: str) -> bool:
        """
        Verify MFA code during login.
        
        Returns:
            True if code is valid
        """
        if not self.db:
            return False
        
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.mfa_enabled:
            return False
        
        # Check if it's a backup code
        if len(code.replace(' ', '')) == 8:
            return self._verify_backup_code(user, code)
        
        # Verify TOTP
        if user.mfa_type == 'totp':
            return self.totp.verify_code(user.mfa_secret, code)
        
        return False
    
    def _verify_backup_code(self, user, code: str) -> bool:
        """Verify and consume a backup code."""
        # In production, backup codes would be hashed and stored separately
        # This is a simplified implementation
        logger.warning(f"Backup code used for user {user.id}")
        return False  # Implement based on your backup code storage
    
    def disable_mfa(self, user_id: str) -> bool:
        """Disable MFA for a user (requires confirmation)."""
        if not self.db:
            return False
        
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.mfa_enabled = False
            user.mfa_secret = None
            user.mfa_type = None
            self.db.commit()
            logger.info(f"MFA disabled for user {user_id}")
            return True
        
        return False
    
    def send_otp_code(self, phone_number: str, name: str = "") -> dict:
        """
        Send OTP code via best available channel (WhatsApp → SMS).
        
        This is the recommended method for user login OTP.
        
        Args:
            phone_number: User's phone number
            name: User's name (for personalization)
            
        Returns:
            {
                'success': bool,
                'code': str,
                'provider': 'whatsapp' | 'sms' | 'none',
                'message': str
            }
        """
        return self.send_user_otp(phone_number, name)
    
    def send_sms_code(self, phone_number: str) -> tuple[bool, str]:
        """
        Send SMS OTP to phone number (legacy method).
        
        For new code, use send_otp_code() which prefers WhatsApp.
        
        Returns:
            (success, code)
        """
        code = self.sms.generate_code()
        success = self.sms.send_sms(phone_number, code)
        return success, code


# ═════════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCIES
# ═════════════════════════════════════════════════════════════════

from fastapi import Depends, HTTPException, Request


async def require_mfa(request: Request, user=Depends(verify_token)):
    """
    FastAPI dependency to require MFA for admin users.
    
    Usage:
        @app.post("/api/admin/sensitive-action")
        async def sensitive_action(user=Depends(require_mfa)):
            ...
    """
    # Check if user is admin
    if user.get('role') != 'admin':
        return user
    
    # Check if MFA verified in session
    mfa_verified = request.session.get('mfa_verified', False)
    
    if not mfa_verified:
        raise HTTPException(
            status_code=403,
            detail="MFA required. Complete two-factor authentication.",
            headers={"X-MFA-Required": "true"}
        )
    
    return user


# Export all classes
__all__ = [
    'MFAProvider',
    'TOTPProvider',
    'SMSProvider',
    'WhatsAppOTPProvider',
    'MFAService',
    'require_mfa',
]
