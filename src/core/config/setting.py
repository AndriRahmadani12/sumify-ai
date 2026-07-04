from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sumify AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")

    # Logging
    LOG_FORMAT: str = Field(default="console", description="Log format: console or json")
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sumify",
        description="Async SQLAlchemy database URL (driver asyncpg)",
    )
    DB_ECHO: bool = Field(default=False, description="Echo SQL statements (debug only)")

    # LLM Settings
    LLM_BASE_URL: str = Field(default="https://api.blablalba.com", description="Base URL for LLM")
    LLM_API_KEY: str = Field(default="blablalba", description="API Key for LLM")
    LLM_MAX_TOKENS: int = Field(default=4096, description="Max tokens for LLM response")
    LLM_TEMPERATURE: float = Field(default=0.3, description="Temperature for LLM")

    # Whisper Settings
    WHISPER_MODEL_SIZE: str = Field(default="base", description="Whisper model size: tiny, base, small, medium, large")
    WHISPER_DEVICE: str | None = Field(default=None, description="Whisper device: cpu, cuda, None for auto")

    # MinIO Settings
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field(default="audio-files", description="MinIO bucket name")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")

    # Celery Settings
    broker_url: str = Field(default="redis://localhost:6379/1")
    result_backend: str = Field(default="redis://localhost:6379/2")
    task_serializer: str = Field(default="json")
    accept_content: List[str] = Field(default=["json"])
    result_serializer: str = Field(default="json")
    timezone: str = Field(default="UTC")
    enable_utc: bool = Field(default=True)
    task_track_started: bool = Field(default=True)
    task_time_limit: int = Field(default=3600, ge=60)
    worker_prefetch_multiplier: int = Field(default=1, ge=1)

    # NB: untuk BaseSettings, env_file HARUS lewat SettingsConfigDict (bukan ConfigDict),
    # kalau tidak file .env tidak akan terbaca.
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


settings = Settings()
