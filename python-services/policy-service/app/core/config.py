from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str = "postgresql://wali_user:password@localhost:5432/wali"
    database_replica_url: str | None = None
    use_mock_db: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Compliance

    operating_bank_account: str
    tech_fee_percentage: int = 2
    tax_exemption_start_date: str = "2026-01-01"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    timezone: str = "Africa/Abidjan"
    
    # Security
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    rate_limit_per_minute: int = 10
    
    # Premium limits (XOF)
    min_premium_daily: int = 100
    max_premium_daily: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
