"""
SIEM Integration for WALI Security Monitoring

Sends security events to external SIEM systems:
- Splunk
- ELK Stack (Elasticsearch)
- Datadog
- AWS CloudWatch
- Custom webhook

CIMA Requirement: All security events must be centrally monitored
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class SIEMProvider(Enum):
    """Supported SIEM providers."""
    SPLUNK = "splunk"
    ELASTICSEARCH = "elasticsearch"
    DATADOG = "datadog"
    CLOUDWATCH = "cloudwatch"
    WEBHOOK = "webhook"


@dataclass
class SecurityEvent:
    """Standardized security event format."""
    timestamp: str
    event_type: str
    severity: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    details: Dict[str, Any]
    service: str
    environment: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class SIEMClient:
    """
    SIEM integration client.
    
    Usage:
        client = SIEMClient.from_env()
        client.send_event({
            'event_type': 'login_failure',
            'severity': 'warning',
            'user_id': 'user123',
            'ip_address': '192.168.1.1',
        })
    """
    
    def __init__(
        self,
        provider: SIEMProvider,
        endpoint: str,
        api_key: Optional[str] = None,
        index: str = "security",
        source: str = "wali",
    ):
        self.provider = provider
        self.endpoint = endpoint
        self.api_key = api_key
        self.index = index
        self.source = source
        
        # Track metrics
        self.events_sent = 0
        self.events_failed = 0
    
    @classmethod
    def from_env(cls) -> Optional['SIEMClient']:
        """Create SIEM client from environment variables."""
        provider_str = os.getenv('SIEM_PROVIDER', '').lower()
        
        if not provider_str:
            logger.info("SIEM not configured (SIEM_PROVIDER not set)")
            return None
        
        try:
            provider = SIEMProvider(provider_str)
        except ValueError:
            logger.error(f"Unknown SIEM provider: {provider_str}")
            return None
        
        endpoint = os.getenv('SIEM_ENDPOINT')
        if not endpoint:
            logger.error("SIEM_ENDPOINT not set")
            return None
        
        return cls(
            provider=provider,
            endpoint=endpoint,
            api_key=os.getenv('SIEM_API_KEY'),
            index=os.getenv('SIEM_INDEX', 'security'),
            source=os.getenv('SIEM_SOURCE', 'wali'),
        )
    
    def send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send security event to SIEM."""
        try:
            # Build standardized event
            event = SecurityEvent(
                timestamp=event_data.get('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ')),
                event_type=event_data.get('event_type', 'unknown'),
                severity=event_data.get('severity', 'info'),
                user_id=event_data.get('user_id'),
                ip_address=event_data.get('ip_address'),
                user_agent=event_data.get('user_agent'),
                request_id=event_data.get('request_id'),
                details=event_data.get('details', {}),
                service=event_data.get('service', 'unknown'),
                environment=event_data.get('environment', os.getenv('ENVIRONMENT', 'unknown')),
            )
            
            # Send based on provider
            if self.provider == SIEMProvider.SPLUNK:
                return self._send_splunk(event)
            elif self.provider == SIEMProvider.ELASTICSEARCH:
                return self._send_elasticsearch(event)
            elif self.provider == SIEMProvider.DATADOG:
                return self._send_datadog(event)
            elif self.provider == SIEMProvider.CLOUDWATCH:
                return self._send_cloudwatch(event)
            elif self.provider == SIEMProvider.WEBHOOK:
                return self._send_webhook(event)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send SIEM event: {e}")
            self.events_failed += 1
            return False
    
    def _send_splunk(self, event: SecurityEvent) -> bool:
        """Send event to Splunk HTTP Event Collector."""
        headers = {
            'Authorization': f'Splunk {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'event': event.to_dict(),
            'sourcetype': '_json',
            'source': self.source,
            'index': self.index,
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=10,
        )
        
        if response.status_code == 200:
            self.events_sent += 1
            return True
        else:
            logger.error(f"Splunk error: {response.status_code} - {response.text}")
            self.events_failed += 1
            return False
    
    def _send_elasticsearch(self, event: SecurityEvent) -> bool:
        """Send event to Elasticsearch."""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['Authorization'] = f'ApiKey {self.api_key}'
        
        # Index name with date
        index_name = f"{self.index}-{time.strftime('%Y.%m.%d')}"
        url = f"{self.endpoint}/{index_name}/_doc"
        
        response = requests.post(
            url,
            headers=headers,
            json=event.to_dict(),
            timeout=10,
        )
        
        if response.status_code in [200, 201]:
            self.events_sent += 1
            return True
        else:
            logger.error(f"Elasticsearch error: {response.status_code} - {response.text}")
            self.events_failed += 1
            return False
    
    def _send_datadog(self, event: SecurityEvent) -> bool:
        """Send event to Datadog."""
        headers = {
            'DD-API-KEY': self.api_key,
            'Content-Type': 'application/json',
        }
        
        # Datadog log format
        payload = {
            'ddsource': self.source,
            'service': event.service,
            'hostname': event.environment,
            'message': event.to_dict(),
        }
        
        response = requests.post(
            'https://http-intake.logs.datadoghq.com/v1/input',
            headers=headers,
            json=payload,
            timeout=10,
        )
        
        if response.status_code == 200:
            self.events_sent += 1
            return True
        else:
            logger.error(f"Datadog error: {response.status_code} - {response.text}")
            self.events_failed += 1
            return False
    
    def _send_cloudwatch(self, event: SecurityEvent) -> bool:
        """Send event to AWS CloudWatch Logs."""
        try:
            import boto3
            
            client = boto3.client('logs')
            
            # Put log event
            response = client.put_log_events(
                logGroupName=f'/wali/{self.environment}/security',
                logStreamName=event.event_type,
                logEvents=[
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': event.to_json(),
                    }
                ],
            )
            
            self.events_sent += 1
            return True
            
        except Exception as e:
            logger.error(f"CloudWatch error: {e}")
            self.events_failed += 1
            return False
    
    def _send_webhook(self, event: SecurityEvent) -> bool:
        """Send event to custom webhook."""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=event.to_dict(),
            timeout=10,
        )
        
        if response.status_code in [200, 201, 202]:
            self.events_sent += 1
            return True
        else:
            logger.error(f"Webhook error: {response.status_code} - {response.text}")
            self.events_failed += 1
            return False
    
    def get_metrics(self) -> Dict[str, int]:
        """Get SIEM client metrics."""
        return {
            'events_sent': self.events_sent,
            'events_failed': self.events_failed,
        }


# ═════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═════════════════════════════════════════════════════════════════

class SecurityEventLogger:
    """Helper class for logging security events in FastAPI apps."""
    
    def __init__(self):
        self.siem = SIEMClient.from_env()
    
    def log(
        self,
        event_type: str,
        severity: str = 'info',
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict] = None,
        service: str = 'unknown',
    ):
        """Log security event to both logger and SIEM."""
        event_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'event_type': event_type,
            'severity': severity,
            'user_id': user_id,
            'ip_address': ip_address,
            'request_id': request_id,
            'details': details or {},
            'service': service,
        }
        
        # Log to Python logger
        log_message = f"SECURITY_EVENT: {event_data}"
        
        if severity == 'critical':
            logger.critical(log_message)
        elif severity == 'error':
            logger.error(log_message)
        elif severity == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Send to SIEM if configured
        if self.siem:
            self.siem.send_event(event_data)


# Global logger instance
_security_logger: Optional[SecurityEventLogger] = None


def get_security_logger() -> SecurityEventLogger:
    """Get global security logger."""
    global _security_logger
    if _security_logger is None:
        _security_logger = SecurityEventLogger()
    return _security_logger


def log_security_event(**kwargs):
    """Convenience function to log security event."""
    get_security_logger().log(**kwargs)


# ═════════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES
# ═════════════════════════════════════════════════════════════════

"""
Required environment variables for SIEM integration:

# Splunk
SIEM_PROVIDER=splunk
SIEM_ENDPOINT=https://splunk.wali.ci:8088/services/collector/event
SIEM_API_KEY=<hec_token>
SIEM_INDEX=security

# Elasticsearch
SIEM_PROVIDER=elasticsearch
SIEM_ENDPOINT=https://elasticsearch.wali.ci:9200
SIEM_API_KEY=<api_key>
SIEM_INDEX=security-events

# Datadog
SIEM_PROVIDER=datadog
SIEM_API_KEY=<datadog_api_key>

# Custom Webhook
SIEM_PROVIDER=webhook
SIEM_ENDPOINT=https://security.wali.ci/webhook
SIEM_API_KEY=<webhook_secret>
"""


if __name__ == '__main__':
    # Test SIEM integration
    print("Testing SIEM Integration...")
    
    # Create test event
    test_event = {
        'event_type': 'test_event',
        'severity': 'info',
        'user_id': 'test_user',
        'ip_address': '127.0.0.1',
        'details': {'test': True},
        'service': 'test',
    }
    
    # Try to send
    siem = SIEMClient.from_env()
    if siem:
        success = siem.send_event(test_event)
        print(f"Test event sent: {success}")
        print(f"Metrics: {siem.get_metrics()}")
    else:
        print("SIEM not configured")
