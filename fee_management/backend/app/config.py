"""Application configuration via pydantic-settings."""
import secrets
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


def _default_secret_key() -> str:
    return secrets.token_hex(32)  # 64 hex chars


def _default_encryption_key() -> str:
    return Fernet.generate_key().decode()


class Settings(BaseSettings):
    APP_NAME: str = "HMC Fee Management System"
    APP_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./fee_management.db"

    SECRET_KEY: str = _default_secret_key()
    ENCRYPTION_KEY: str = _default_encryption_key()

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:5174", "http://localhost:8001"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
