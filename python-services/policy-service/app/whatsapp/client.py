"""
Meta WhatsApp Business API Client.

Production-grade client with:
- HMAC-SHA256 webhook signature verification
- Exponential backoff retry (3 attempts: 2s, 4s, 8s)
- Circuit breaker (switch to SMS after 5 failures in 60s)
- Idempotency keys
- Cross-border transfer logging (Law 2013-450)
"""
import hmac
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from uuid import uuid4

import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)

from .models import (
    OutboundMessage, 
    MessageType, 
    LanguageCode,
    CrossBorderTransferLog
)

logger = logging.getLogger(__name__)


class WhatsAppAPIError(Exception):
    """WhatsApp API error."""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open - API is temporarily disabled."""
    pass


class WhatsAppClient:
    """
    Meta WhatsApp Business API Client.
    
    Features:
    - Webhook signature verification
    - Rate limiting with retry
    - Circuit breaker pattern
    - Idempotency
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    # Circuit breaker settings
    CIRCUIT_FAILURE_THRESHOLD = 5
    CIRCUIT_TIMEOUT_SECONDS = 60
    
    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        app_secret: Optional[str] = None,
        webhook_verify_token: Optional[str] = None,
        redis_client=None,
        db_session=None
    ):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.app_secret = app_secret
        self.webhook_verify_token = webhook_verify_token
        self.redis = redis_client
        self.db = db_session
        
        # Circuit breaker state
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._circuit_open = False
        
        # HTTP client with timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker allows requests."""
        if not self._circuit_open:
            return
        
        # Check if timeout has passed
        if self._last_failure_time:
            elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
            if elapsed > self.CIRCUIT_TIMEOUT_SECONDS:
                logger.info("Circuit breaker timeout passed, resetting")
                self._reset_circuit_breaker()
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker open. Try again in {self.CIRCUIT_TIMEOUT_SECONDS - elapsed:.0f}s"
                )
    
    def _record_failure(self):
        """Record an API failure for circuit breaker."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self.CIRCUIT_FAILURE_THRESHOLD:
            logger.error(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
            self._circuit_open = True
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker after timeout."""
        self._failure_count = 0
        self._last_failure_time = None
        self._circuit_open = False
        logger.info("Circuit breaker reset")
    
    def _record_success(self):
        """Record successful API call."""
        if self._failure_count > 0:
            self._failure_count = 0
            logger.info("Failure count reset after success")
    
    def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
        
        Returns:
            True if signature is valid
        """
        if not self.app_secret:
            logger.warning("APP_SECRET not set, skipping signature verification")
            return True
        
        if not signature:
            logger.error("Missing X-Hub-Signature-256 header")
            return False
        
        # Signature format: sha256=<hash>
        expected_signature = hmac.new(
            self.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Extract hash from header
        if "=" in signature:
            _, received_hash = signature.split("=", 1)
        else:
            received_hash = signature
        
        is_valid = hmac.compare_digest(expected_signature, received_hash)
        
        if not is_valid:
            logger.error("Webhook signature verification failed")
        
        return is_valid
    
    def verify_webhook_token(self, token: str) -> bool:
        """Verify webhook verification token."""
        if not self.webhook_verify_token:
            return True
        return token == self.webhook_verify_token
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.HTTPError, WhatsAppAPIError)),
        reraise=True
    )
    def send_message(
        self, 
        message: OutboundMessage,
        track_cross_border: bool = True
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Meta API.
        
        Args:
            message: Outbound message
            track_cross_border: Log to compliance table
        
        Returns:
            API response
        
        Raises:
            WhatsAppAPIError: On API error
            CircuitBreakerOpen: If circuit is open
        """
        self._check_circuit_breaker()
        
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        # Idempotency key
        idempotency_key = message.idempotency_key or str(uuid4())
        headers["X-Idempotency-Key"] = idempotency_key
        
        # Build payload based on message type
        payload = self._build_payload(message)
        
        try:
            response = self.client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Record success
            self._record_success()
            
            # Log cross-border transfer
            if track_cross_border and self.db:
                self._log_cross_border_transfer(
                    phone=message.phone,
                    transfer_type="message",
                    data_categories=["personal"]
                )
            
            logger.info(f"Message sent to {message.phone}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            self._record_failure()
            
            error_data = e.response.json() if e.response.text else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            error_code = error_data.get("error", {}).get("code", "unknown")
            
            logger.error(f"WhatsApp API error: {error_message}")
            raise WhatsAppAPIError(error_message, error_code, error_data)
            
        except httpx.RequestError as e:
            self._record_failure()
            logger.error(f"WhatsApp API request error: {e}")
            raise WhatsAppAPIError(f"Request failed: {str(e)}")
    
    def _build_payload(self, message: OutboundMessage) -> Dict[str, Any]:
        """Build API payload based on message type."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.phone,
        }
        
        if message.type == MessageType.TEXT and message.text:
            payload["type"] = "text"
            payload["text"] = {"body": message.text}
            
        elif message.type == MessageType.TEMPLATE and message.template_name:
            payload["type"] = "template"
            payload["template"] = {
                "name": message.template_name,
                "language": {
                    "code": message.template_language or "fr"
                }
            }
            if message.template_params:
                payload["template"]["components"] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(param.get("value", ""))}
                            for param in message.template_params
                        ]
                    }
                ]
                
        elif message.type == MessageType.IMAGE:
            payload["type"] = "image"
            if message.media_id:
                payload["image"] = {"id": message.media_id}
            elif message.media_url:
                payload["image"] = {"link": message.media_url}
                
        elif message.type == MessageType.INTERACTIVE and message.interactive:
            payload["type"] = "interactive"
            payload["interactive"] = message.interactive
        
        return payload
    
    def send_template_message(
        self,
        phone: str,
        template_name: str,
        language: str = "fr",
        params: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Convenience method for sending template messages."""
        message = OutboundMessage(
            phone=phone,
            type=MessageType.TEMPLATE,
            template_name=template_name,
            template_language=language,
            template_params=[{"value": p} for p in (params or [])]
        )
        return self.send_message(message)
    
    def download_media(
        self, 
        media_id: str, 
        destination_path: str
    ) -> str:
        """
        Download media from Meta CDN.
        
        Args:
            media_id: Meta's media ID
            destination_path: Where to save the file
        
        Returns:
            Path to downloaded file
        """
        self._check_circuit_breaker()
        
        # Get media URL
        url = f"{self.BASE_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # Get download URL
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            
            media_data = response.json()
            download_url = media_data.get("url")
            
            if not download_url:
                raise WhatsAppAPIError("No download URL in response")
            
            # Download file
            file_response = self.client.get(download_url, headers=headers)
            file_response.raise_for_status()
            
            with open(destination_path, "wb") as f:
                f.write(file_response.content)
            
            self._record_success()
            logger.info(f"Media downloaded: {destination_path}")
            
            return destination_path
            
        except httpx.HTTPError as e:
            self._record_failure()
            raise WhatsAppAPIError(f"Media download failed: {str(e)}")
    
    def get_media_info(self, media_id: str) -> Dict[str, Any]:
        """Get media metadata."""
        url = f"{self.BASE_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise WhatsAppAPIError(f"Failed to get media info: {str(e)}")
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """Mark an inbound message as read."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.warning(f"Failed to mark message as read: {e}")
            return False
    
    def _log_cross_border_transfer(
        self,
        phone: str,
        transfer_type: str,
        data_categories: List[str]
    ):
        """Log cross-border data transfer for Law 2013-450 compliance."""
        if not self.db:
            return
        
        try:
            log = CrossBorderTransferLog(
                transfer_type=transfer_type,
                destination_country="US",
                destination_provider="Meta Platforms Inc.",
                data_subject_phone=phone,
                data_categories=data_categories,
                legal_basis="contract_performance",
                retention_years=3,
                purge_after=datetime.utcnow() + timedelta(days=3*365)
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log cross-border transfer: {e}")
            self.db.rollback()
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
