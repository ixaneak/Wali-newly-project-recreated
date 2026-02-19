"""
WhatsApp OTP Provider for WALI

Replaces expensive SMS (Twilio) with WhatsApp Business API.
WhatsApp messages are free for session messages after the 24-hour window.

Advantages over SMS:
- Lower cost (especially in Ivory Coast)
- Higher open rates (>90%)
- Rich media support
- End-to-end encryption
- No character limits

Providers Supported:
- WhatsApp Business API (Meta)
- Twilio WhatsApp
- MessageBird WhatsApp
"""

import os
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
import json

logger = logging.getLogger(__name__)


class WhatsAppOTPProvider:
    """
    WhatsApp OTP provider using WhatsApp Business API.
    
    Setup:
    1. Create WhatsApp Business Account
    2. Get API credentials from Meta Developer Portal
    3. Verify phone number
    4. Set environment variables
    """
    
    def __init__(self):
        # Meta WhatsApp Business API credentials
        self.api_token = os.getenv('WHATSAPP_API_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        
        # Fallback to Twilio WhatsApp if Meta not configured
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        # API endpoints
        self.meta_api_url = "https://graph.facebook.com/v18.0"
        
        # Template name for OTP (must be pre-approved by Meta)
        self.otp_template_name = os.getenv('WHATSAPP_OTP_TEMPLATE', 'wali_otp')
        
        # Code validity
        self.code_validity = 300  # 5 minutes
        self.code_length = 6
    
    def is_configured(self) -> bool:
        """Check if WhatsApp is properly configured."""
        # Check Meta API
        if all([self.api_token, self.phone_number_id]):
            return True
        
        # Check Twilio WhatsApp fallback
        if all([self.twilio_sid, self.twilio_token, self.twilio_whatsapp_number]):
            return True
        
        return False
    
    def generate_code(self) -> str:
        """Generate numeric OTP."""
        return ''.join(secrets.choice('0123456789') for _ in range(self.code_length))
    
    def format_phone_for_whatsapp(self, phone: str) -> str:
        """
        Format phone number for WhatsApp.
        
        WhatsApp requires international format with country code.
        Example: +225 07 07 07 07 07 → +2250707070707
        """
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        
        # Add country code if missing (assume Ivory Coast +225)
        if len(digits) == 10 and digits.startswith('0'):
            digits = '225' + digits[1:]
        elif len(digits) == 8:
            # Old format without 07 prefix
            digits = '225' + digits
        
        return f"+{digits}"
    
    def send_otp_via_meta_api(self, phone: str, code: str, name: str = "") -> Dict[str, Any]:
        """
        Send OTP via Meta WhatsApp Business API.
        
        Args:
            phone: Phone number in international format
            code: OTP code
            name: User's name (optional, for personalization)
            
        Returns:
            Dict with success status and message ID
        """
        if not self.api_token or not self.phone_number_id:
            return {
                'success': False,
                'error': 'Meta WhatsApp API not configured',
                'provider': 'none'
            }
        
        try:
            url = f"{self.meta_api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
            }
            
            # Format phone number
            to_phone = self.format_phone_for_whatsapp(phone)
            
            # Build message payload
            # Option 1: Use template message (required for first contact)
            if self.otp_template_name:
                payload = {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': to_phone,
                    'type': 'template',
                    'template': {
                        'name': self.otp_template_name,
                        'language': {'code': 'fr'},
                        'components': [
                            {
                                'type': 'body',
                                'parameters': [
                                    {'type': 'text', 'text': name or 'Utilisateur'},
                                    {'type': 'text', 'text': code},
                                    {'type': 'text', 'text': '5'},  # minutes validity
                                ]
                            }
                        ]
                    }
                }
            else:
                # Option 2: Use session message (if within 24h window)
                payload = {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': to_phone,
                    'type': 'text',
                    'text': {
                        'body': f"🔐 *Code de vérification WALI*\n\n"
                               f"Bonjour {name or ''},\n\n"
                               f"Votre code de vérification est : *{code}*\n\n"
                               f"Ce code est valable pendant 5 minutes.\n\n"
                               f"Ne partagez ce code avec personne.",
                        'preview_url': False
                    }
                }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                message_id = data.get('messages', [{}])[0].get('id')
                logger.info(f"WhatsApp OTP sent via Meta API to {phone}, message_id: {message_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'provider': 'meta_whatsapp'
                }
            else:
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Meta WhatsApp API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'meta_whatsapp'
                }
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp OTP via Meta: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'meta_whatsapp'
            }
    
    def send_otp_via_twilio_whatsapp(self, phone: str, code: str, name: str = "") -> Dict[str, Any]:
        """
        Send OTP via Twilio WhatsApp (fallback).
        
        Args:
            phone: Phone number
            code: OTP code
            name: User's name
            
        Returns:
            Dict with success status
        """
        if not all([self.twilio_sid, self.twilio_token, self.twilio_whatsapp_number]):
            return {
                'success': False,
                'error': 'Twilio WhatsApp not configured',
                'provider': 'none'
            }
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_sid, self.twilio_token)
            
            # Format phone for WhatsApp
            to_phone = self.format_phone_for_whatsapp(phone)
            
            # Send message
            message = client.messages.create(
                from_=f"whatsapp:{self.twilio_whatsapp_number}",
                to=f"whatsapp:{to_phone}",
                body=f"🔐 *Code de vérification WALI*\n\n"
                     f"Bonjour {name or ''},\n\n"
                     f"Votre code de vérification est : *{code}*\n\n"
                     f"Ce code est valable pendant 5 minutes.\n\n"
                     f"Ne partagez ce code avec personne."
            )
            
            logger.info(f"WhatsApp OTP sent via Twilio to {phone}, SID: {message.sid}")
            return {
                'success': True,
                'message_id': message.sid,
                'provider': 'twilio_whatsapp'
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp OTP via Twilio: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'twilio_whatsapp'
            }
    
    def send_otp(self, phone: str, code: str, name: str = "") -> Dict[str, Any]:
        """
        Send OTP via WhatsApp (primary method).
        
        Tries Meta API first, falls back to Twilio WhatsApp.
        
        Args:
            phone: Phone number
            code: OTP code
            name: User's name (optional)
            
        Returns:
            Dict with success status and provider used
        """
        # Try Meta API first (cheaper)
        if self.api_token and self.phone_number_id:
            result = self.send_otp_via_meta_api(phone, code, name)
            if result['success']:
                return result
            
            logger.warning(f"Meta API failed, trying Twilio: {result.get('error')}")
        
        # Fallback to Twilio WhatsApp
        if self.twilio_sid and self.twilio_token:
            result = self.send_otp_via_twilio_whatsapp(phone, code, name)
            if result['success']:
                return result
        
        # Both failed
        return {
            'success': False,
            'error': 'All WhatsApp providers failed',
            'provider': 'none'
        }
    
    def verify_code(self, stored_code: str, provided_code: str, 
                    generated_at: datetime) -> bool:
        """
        Verify OTP code.
        
        Args:
            stored_code: The code sent via WhatsApp
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
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(stored_code.strip(), provided_code.strip())


class OTPManager:
    """
    Unified OTP manager supporting both WhatsApp and SMS.
    
    Prefers WhatsApp (cheaper) but falls back to SMS if needed.
    """
    
    def __init__(self):
        self.whatsapp = WhatsAppOTPProvider()
        self.sms_provider = None  # Lazy load SMS only if needed
    
    def send_otp(self, phone: str, name: str = "", prefer_whatsapp: bool = True) -> Dict[str, Any]:
        """
        Send OTP to user.
        
        Args:
            phone: Phone number
            name: User's name
            prefer_whatsapp: Try WhatsApp first if True
            
        Returns:
            Dict with code, success status, and provider used
        """
        # Generate code
        code = self.whatsapp.generate_code()
        
        if prefer_whatsapp and self.whatsapp.is_configured():
            # Try WhatsApp first
            result = self.whatsapp.send_otp(phone, code, name)
            
            if result['success']:
                return {
                    'success': True,
                    'code': code,  # Return for storage (in production, store hashed)
                    'provider': result.get('provider', 'whatsapp'),
                    'message_id': result.get('message_id'),
                }
            
            logger.warning(f"WhatsApp failed, will try SMS: {result.get('error')}")
        
        # Fallback to SMS (Twilio)
        if not self.sms_provider:
            from app.core.mfa import SMSProvider
            self.sms_provider = SMSProvider()
        
        if self.sms_provider.is_configured():
            success, sent_code = self.sms_provider.send_sms(phone, code)
            
            if success:
                return {
                    'success': True,
                    'code': code,
                    'provider': 'sms_twilio',
                }
        
        # Both failed
        return {
            'success': False,
            'error': 'Failed to send OTP via both WhatsApp and SMS',
            'code': None,
        }
    
    def verify_otp(self, stored_code: str, provided_code: str, 
                   generated_at: datetime) -> bool:
        """Verify OTP code."""
        return self.whatsapp.verify_code(stored_code, provided_code, generated_at)


# Convenience function for direct use
def send_whatsapp_otp(phone: str, code: str, name: str = "") -> Dict[str, Any]:
    """Send OTP via WhatsApp."""
    provider = WhatsAppOTPProvider()
    return provider.send_otp(phone, code, name)


def send_unified_otp(phone: str, name: str = "") -> Dict[str, Any]:
    """
    Send OTP using best available method (WhatsApp preferred).
    
    Returns:
        {
            'success': bool,
            'code': str (store this),
            'provider': 'whatsapp' | 'sms' | 'none',
            'message_id': str (optional)
        }
    """
    manager = OTPManager()
    return manager.send_otp(phone, name)


# Export
__all__ = [
    'WhatsAppOTPProvider',
    'OTPManager',
    'send_whatsapp_otp',
    'send_unified_otp',
]
