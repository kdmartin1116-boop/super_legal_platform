import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator
from pathlib import Path


class Settings(BaseSettings):
    # Main configuration
    app_name: str = Field(default="Sovereign Legal Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    backend_root: Path = Field(default_factory=lambda: Path(__file__).parent)
    
    # Security
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./sovereign_legal.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    
    # File Upload
    max_content_length: int = Field(default=52428800, description="Max file upload size (50MB)")
    upload_folder: str = Field(default="uploads/", description="Upload directory")
    allowed_extensions: List[str] = Field(
        default=["pdf", "jpg", "jpeg", "png", "txt", "doc", "docx"],
        description="Allowed file extensions"
    )
    
    # Storage configuration
    use_s3: bool = Field(default=False, description="Use S3 for file storage")
    s3_bucket: Optional[str] = Field(default=None, description="S3 bucket name")
    s3_region: str = Field(default="us-east-1", description="S3 region")
    
    @validator('upload_folder')
    def validate_upload_folder(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    # Rate Limiting
    rate_limit_storage_url: str = "memory://"
    default_rate_limit: str = "100/hour"
    
    # External Services
    redis_url: str = "redis://localhost:6379"
    elasticsearch_url: str = "http://localhost:9200"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # API Configuration
    api_title: str = "Sovereign Legal Platform API"
    api_description: str = "Comprehensive legal technology platform API"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    return Settings()


settings = get_settings()