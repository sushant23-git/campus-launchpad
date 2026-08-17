from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres_password@db:5432/campus_launchpad"
    REDIS_URL: str = "redis://cache:6379/0"
    JWT_SECRET_KEY: str = "super_secret_jwt_signing_key_change_me_in_production"
    JWT_REFRESH_SECRET_KEY: str = "super_secret_refresh_signing_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TOTP_ISSUER: str = "CampusLaunchpadDev"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    FILE_STORAGE_PROVIDER: str = "local"
    FILE_STORAGE_PATH: str = "./uploads"
    FILE_STORAGE_BUCKET: str = "campus-launchpad-uploads"
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api/v1"
    
    # AI & Integrations settings
    AI_PROVIDER_KEY: str = "mock"
    AI_MODEL_NAME: str = "mock-model"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
