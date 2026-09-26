import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Continuum"
    APP_URL: str = "http://localhost:3000"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://continuum_app:secure_postgres_password_here@localhost:5432/continuum_db"
    )
    DATABASE_SYNC_URL: str = os.getenv(
        "DATABASE_SYNC_URL",
        "postgresql://continuum_app:secure_postgres_password_here@localhost:5432/continuum_db"
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "continuum_secure_master_production_key_knowledge_vault_91k8")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://continuum.example.com"
    ]

    # Storage Quotas
    FREE_TIER_MISSION_STORAGE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    PREMIUM_TIER_MAX_SINGLE_FILE_BYTES: int = 1024 * 1024 * 1024  # 1 GB
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "/tmp/continuum_storage")
    STORAGE_BUCKET_NAME: str = os.getenv("STORAGE_BUCKET_NAME", "continuum-vault")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    STORAGE_REGION: str = os.getenv("STORAGE_REGION", "af-south-1")

    # Marketplace Fees
    DIRECT_TRANSACTION_FEE_PERCENT: float = 0.08  # 8%
    ASSISTED_TRANSACTION_FEE_PERCENT: float = 0.15 # 15%
    PLATFORM_CURRENCY: str = "ZAR"
    PREMIUM_SUBSCRIPTION_MONTHLY_ZAR: float = 100.00

    # Payment Gateway
    PAYMENT_GATEWAY_PROVIDER: str = os.getenv("PAYMENT_GATEWAY_PROVIDER", "paystack")
    PAYMENT_SECRET_KEY: str = os.getenv("PAYMENT_SECRET_KEY", "sk_test_mock")

    # Biometric Provider (Zero Raw Data Storage)
    BIOMETRIC_PROVIDER: str = os.getenv("BIOMETRIC_PROVIDER", "zero_knowledge")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
