import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Accuro"
    TAGLINE: str = "Accurate accounts. You review, Accuro does the rest."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "accuro-production-grade-super-secret-key-32charsmin!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database
    # Default to SQLite for zero-config local runs, easily overridden with postgresql:// in Docker / Prod
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./accuro.db")
    
    # Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local" or "s3"
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "./storage")
    S3_ENDPOINT: Optional[str] = os.getenv("S3_ENDPOINT", None)
    S3_BUCKET: str = os.getenv("S3_BUCKET", "accuro-documents")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY", None)
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY", None)
    
    # Redis / Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI Providers
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "deterministic_mock")  # "vision_llm", "deterministic_mock", "gemini", "openai"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    
    # DPDP Compliance (India Data Protection)
    DPDP_FIELD_ENCRYPTION_KEY: str = os.getenv("DPDP_FIELD_ENCRYPTION_KEY", "accuro_dpdp_encryption_secret_key_32b!")
    DEFAULT_DATA_RETENTION_YEARS: int = 8  # Statutory requirement under Indian Income Tax Act / GST Act
    
    # Productivity Metric Benchmark (minutes saved per document automatically drafted)
    MANUAL_ENTRY_BENCHMARK_MINUTES: float = 15.0

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
