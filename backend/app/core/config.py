"""Application settings loaded from environment."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the HCP CRM backend."""

    model_config = SettingsConfigDict(
        env_file=(".env", "config/.env", "../config/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+psycopg://hcp_crm:change_me@localhost:5432/hcp_crm"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True

    JWT_SECRET: str = Field(default="change_me_to_a_long_random_secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL: int = 1800
    JWT_REFRESH_TTL: int = 604800

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    AI_TIMEOUT_SECONDS: float = 60.0
    AI_HISTORY_LIMIT: int = 10

    RATE_LIMIT_LOGIN_PER_15MIN: int = 10
    RATE_LIMIT_AI_PER_HOUR: int = 30
    RATE_LIMIT_API_PER_HOUR: int = 600

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_set(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("JWT_SECRET must be a non-empty string")
        return value

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def db_pool_size(self) -> int:
        return self.DB_POOL_SIZE

    @property
    def db_max_overflow(self) -> int:
        return self.DB_MAX_OVERFLOW

    @property
    def db_pool_pre_ping(self) -> bool:
        return self.DB_POOL_PRE_PING

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return self.cors_origin_list

    @property
    def rate_limit_login_per_15min(self) -> int:
        return self.RATE_LIMIT_LOGIN_PER_15MIN

    @property
    def rate_limit_ai_per_hour(self) -> int:
        return self.RATE_LIMIT_AI_PER_HOUR

    @property
    def rate_limit_api_per_hour(self) -> int:
        return self.RATE_LIMIT_API_PER_HOUR

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
