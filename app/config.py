from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "AI Training Service"
    debug: bool = False
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+asyncpg://aiuser:aipass@localhost:5433/aitraining"

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048

    dotnet_api_url: str = "http://localhost:8080"
    dotnet_api_timeout: int = 30
    service_api_key: Optional[str] = None

    dotnet_api_retry_attempts: int = 5
    dotnet_api_retry_base_delay: float = 1.0
    dotnet_api_retry_max_delay: float = 60.0
    dotnet_api_retry_exponential_base: float = 2.0

    max_conversation_history: int = 50
    completion_marker: str = "{TOPIC_COMPLETED}"

    cors_origins: list[str] = ["*"]

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
