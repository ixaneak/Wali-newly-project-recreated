from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Compliance service configuration."""
    
    # Database
    database_url: str = "postgresql://wali_user:password@localhost:5432/wali"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    
    # Compliance
    tax_exemption_start_date: str = "2026-01-01"
    tech_fee_percentage: int = 2
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Security
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
