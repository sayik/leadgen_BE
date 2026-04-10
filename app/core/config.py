from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Leadgen API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "unsafe-development-secret-change-me"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql+asyncpg://leadgen:leadgen@localhost:5432/leadgen"
    cors_origins: list[str] = ["http://localhost:3000"]
    default_timezone: str = "Asia/Kolkata"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
