"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = "AI Training Service"
    debug: bool = False
    environment: str = "development"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Database settings
    database_url: str = "postgresql+asyncpg://aiuser:aipass@localhost:5433/aitraining"

    # Google Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048

    # .NET API integration
    dotnet_api_url: str = "http://localhost:8080"
    dotnet_api_timeout: int = 30
    service_api_key: Optional[str] = None  # For service-to-service auth

    # Session settings
    max_conversation_history: int = 50  # Maximum messages to keep in context
    completion_marker: str = "{TOPIC_COMPLETED}"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    @property
    def database_url_sync(self) -> str:
        """Returns synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")


# Global settings instance
settings = Settings()
