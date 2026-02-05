from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Claims service configuration settings."""
    
    # Database
    database_url: str = "postgresql://wali_user:password@localhost:5432/wali"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # MinIO (S3-compatible storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "wali_admin"
    minio_secret_key: str = "password"
    minio_bucket_name: str = "wali-claims"
    minio_secure: bool = False  # Set True for HTTPS in production
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    
    # Claims validation
    max_image_size_mb: int = 5
    allowed_image_extensions: list[str] = [".jpg", ".jpeg", ".png"]
    min_image_dimensions: tuple[int, int] = (640, 480)
    exif_timestamp_hours_limit: int = 24
    
    # Fraud detection
    phash_similarity_threshold: int = 5  # Hamming distance threshold
    
    # Compliance
    claims_retention_days: int = 2555  # 7 years for insurance law
    
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    use_mock_db: bool = False
    
    # Security
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
