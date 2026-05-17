from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sumify AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")

    # Logging
    LOG_FORMAT: str = Field(default="console", description="Log format: console or json")
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # LLM Settings
    LLM_BASE_URL: str = Field(default="https://api.blablalba.com", description="Base URL for LLM")
    LLM_API_KEY: str = Field(default="blablalba", description="API Key for LLM")
    LLM_MAX_TOKENS: int = Field(default=4096, description="Max tokens for LLM response")
    LLM_TEMPERATURE: float = Field(default=0.3, description="Temperature for LLM")

    # MinIO Settings
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field(default="audio-files", description="MinIO bucket name")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


settings = Settings()
