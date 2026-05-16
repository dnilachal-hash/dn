from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Homoeopathic Medical College Payroll System"
    APP_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./payroll.db"

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING_64_CHARS_MIN_xxxxxxxxxx"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 30

    ENCRYPTION_KEY: str = "wzN5XzG8FfRgvJqK6mY9bN3hW2pT4cE7sL1aQ0uI8oM="  # Fernet 32-byte b64

    DATA_DIR: Path = Path("./data")
    UPLOAD_DIR: Path = Path("./data/uploads")
    REPORTS_DIR: Path = Path("./data/reports")
    BACKUP_DIR: Path = Path("./data/backups")
    LOG_DIR: Path = Path("./data/logs")

    ORGANISATION_NAME: str = "Homoeopathic Medical College & Hospital"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]


settings = Settings()
for d in (settings.DATA_DIR, settings.UPLOAD_DIR, settings.REPORTS_DIR, settings.BACKUP_DIR, settings.LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)
