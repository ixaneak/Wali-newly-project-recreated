from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str = "postgresql://wali_user:password@localhost:5432/wali"
    
    # Provider API Keys
    orange_client_id: str | None = None
    orange_client_secret: str | None = None
    orange_merchant_code: str | None = None
    
    wave_api_key: str | None = None
    wave_secret_key: str | None = None
    
    mtn_api_user: str | None = None
    mtn_api_key: str | None = None
    mtn_subscription_key: str | None = None
    
    # SMS
    sms_provider: str | None = "orange" # default
    orange_sms_api_key: str | None = None
    orange_sms_sender_id: str = "Wali"
    
    
    # Internal Services
    policy_service_url: str = "http://localhost:8000"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
