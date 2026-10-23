from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AICF — AI Content Forensics & Authenticity Intelligence Platform"
    TAGLINE: str = "Detect. Analyze. Explain. Verify."
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aicf_db"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Session & Security
    SECRET_KEY: str = "aicf-insecure-development-secret-key-change-in-production"
    SESSION_EXPIRE_MINUTES: int = 1440  # 24 hours
    COOKIE_NAME: str = "aicf_session"
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_HTTPONLY: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_MAX: int = 5
    RATE_LIMIT_LOGIN_WINDOW: int = 60  # seconds
    RATE_LIMIT_REGISTER_MAX: int = 3
    RATE_LIMIT_REGISTER_WINDOW: int = 60  # seconds
    RATE_LIMIT_TEXT_MAX: int = 20
    RATE_LIMIT_TEXT_WINDOW: int = 60  # seconds

    # Text Analysis Engine Configuration
    TEXT_MODEL_NAME: str = "roberta-base-openai-detector"
    TEXT_MODEL_VERSION: str = "1.0.0"
    TEXT_MIN_WORDS: int = 15
    TEXT_MIN_CHARS: int = 50
    TEXT_MAX_CHARS: int = 15000
    TEXT_AI_THRESHOLD: float = 0.70
    TEXT_HUMAN_THRESHOLD: float = 0.30

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
