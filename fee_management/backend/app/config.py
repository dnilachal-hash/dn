"""Application configuration via pydantic-settings."""
import secrets
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet


def _default_secret_key() -> str:
    return secrets.token_hex(32)


def _default_encryption_key() -> str:
    return Fernet.generate_key().decode()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "HMC Fee Management System"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./fee_management.db"

    SECRET_KEY: str = _default_secret_key()
    ENCRYPTION_KEY: str = _default_encryption_key()

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:5174", "http://localhost:8001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
