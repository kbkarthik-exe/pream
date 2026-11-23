from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "A Multimodal Deep Learning Framework for Robust Detection of Synthetic Media"
    TAGLINE: str = "Detect. Analyze. Explain. Verify."
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "debug")
        return bool(v)

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
    RATE_LIMIT_IMAGE_MAX: int = 15
    RATE_LIMIT_IMAGE_WINDOW: int = 60  # seconds
    RATE_LIMIT_VIDEO_MAX: int = 5
    RATE_LIMIT_VIDEO_WINDOW: int = 60  # seconds

    # Text Analysis Engine Configuration
    TEXT_MODEL_NAME: str = "roberta-base-openai-detector"
    TEXT_MODEL_VERSION: str = "1.0.0"
    TEXT_MIN_WORDS: int = 15
    TEXT_MIN_CHARS: int = 50
    TEXT_MAX_CHARS: int = 15000
    TEXT_AI_THRESHOLD: float = 0.70
    TEXT_HUMAN_THRESHOLD: float = 0.30

    # Image Analysis Engine Configuration
    IMAGE_MODEL_NAME: str = "umm-maybe/AI-image-detector"
    IMAGE_MODEL_VERSION: str = "1.0.0"
    IMAGE_MAX_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    IMAGE_MAX_PIXELS: int = 16_000_000  # 16 MP max (protects against decompression bombs)
    IMAGE_MIN_DIMENSION: int = 32  # Minimum 32x32 pixels
    IMAGE_AI_THRESHOLD: float = 0.70
    IMAGE_HUMAN_THRESHOLD: float = 0.30

    # Video Analysis Engine Configuration
    VIDEO_MODEL_NAME: str = "AICF-Video-Forensics-Engine"
    VIDEO_MODEL_VERSION: str = "1.0.0"
    VIDEO_FRAME_CLASSIFIER_ID: str = "umm-maybe/AI-image-detector"
    VIDEO_MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    VIDEO_MAX_DURATION_SECONDS: float = 120.0  # Max 2 minutes
    VIDEO_MAX_RESOLUTION: int = 3840  # Max width or height (4K boundary)
    VIDEO_MAX_SAMPLED_FRAMES: int = 30  # Max frames sampled uniformly
    VIDEO_FRAME_SAMPLE_INTERVAL: float = 1.0  # 1 frame per second
    VIDEO_PROCESSING_TIMEOUT_SECONDS: float = 60.0
    VIDEO_AI_THRESHOLD: float = 0.70
    VIDEO_HUMAN_THRESHOLD: float = 0.30

    # Optional Cloud Verification Providers (Phase 4)
    HIVE_API_KEY: str | None = None
    HIVE_API_BASE_URL: str = "https://api.thehive.ai/api/v2"

    GPTZERO_API_KEY: str | None = None
    GPTZERO_API_BASE_URL: str = "https://api.gptzero.me/v2"

    COPYLEAKS_API_KEY: str | None = None
    COPYLEAKS_EMAIL: str | None = None
    COPYLEAKS_API_BASE_URL: str = "https://api.copyleaks.com/v3"

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
