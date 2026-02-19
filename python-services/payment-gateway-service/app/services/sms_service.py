import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SmsService:
    @staticmethod
    def send_confirmation(phone_number: str, message: str):
        """
        Send confirmation SMS.
        Currently logs the message. Ready for Orange SMS API integration.
        """
        logger.info(f"========== SMS NOTIFICATION ==========")
        logger.info(f"TO: {phone_number}")
        logger.info(f"MSG: {message}")
        logger.info(f"PROVIDER: {settings.sms_provider}")
        logger.info(f"======================================")
        
        # Integration with Orange SMS API would go here
        # if settings.orange_sms_api_key:
        #     requests.post(...)
