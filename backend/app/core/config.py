import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FinMind AI"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:8000"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./finmind.db"  # Uses SQLite for fast local development
    
    # Redis Cache Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Security & JWT
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Global settings instance
settings = Settings()
