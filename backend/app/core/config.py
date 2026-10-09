from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Admin Management Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/pingo",
        description="PostgreSQL connection string"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend"
    )

    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    EMAIL_FROM: str = Field(default="noreply@pingo.com")
    EMAIL_FROM_NAME: str = Field(default="Pingo Admin")

    # Web Push (VAPID)
    VAPID_PRIVATE_KEY: str = Field(default="")
    VAPID_PUBLIC_KEY: str = Field(default="")
    VAPID_CLAIMS_SUB: str = Field(default="mailto:admin@pingo.com")

    # Frontend URL (for CORS and links in emails)
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()