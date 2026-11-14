import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/buildguard"
    SQLITE_URL: str = "sqlite:///./buildguard.db"
    USE_SQLITE: bool = True
    
    # Security
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # LLM Providers
    LLM_PROVIDER: str = "none"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Storage
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 20
    
    # API / Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Computer Vision
    CV_MODEL_PATH: str = "./models"
    CV_FALLBACK_MODE: bool = True
    CV_CONFIDENCE_THRESHOLD: float = 0.5

    # Legacy setting accepted for existing .env files; analysis never uses synthetic fallback.
    DEMO_MODE: Optional[bool] = None

settings = Settings()

# Ensure storage path exists
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
