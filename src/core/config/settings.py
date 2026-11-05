"""All settings come from environment variables (or .env files for local dev)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Later files win, so secrets/.env overrides a root .env. Real environment variables beat both.
ENV_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "src/core/config/secrets/.env",
)

_DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Web API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = Field(default="development", description="development | staging | production")
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    RELOAD: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = PROJECT_ROOT / "app" / "logs"
    LOG_TO_FILE: bool = True

    # PostgreSQL
    DB_ENABLED: bool = True
    PG_USER: str = "postgres"
    PG_PASSWORD: str = ""
    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DATABASE: str = "postgres"
    PG_SCHEMA: str = "public"
    PG_POOL_MIN_SIZE: int = Field(default=1, ge=0)
    PG_POOL_MAX_SIZE: int = Field(default=10, ge=1)

    # JWT (used by core.security helpers when a project adds auth)
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1)

    # HTTP / security
    CORS_ORIGINS: str = Field(
        default="",
        description="Comma-separated origins. Empty = localhost dev ports, or none in production.",
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    API_DOCS_ENABLED: bool | None = Field(
        default=None,
        description="Serve /docs, /redoc, /openapi.json. Unset = on except in production.",
    )
    SECURITY_HEADERS_ENABLED: bool = True
    SECURITY_HSTS_MAX_AGE: int = Field(default=31_536_000, ge=0)
    SECURITY_CSP: str = "default-src 'none'; frame-ancestors 'none'"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = Field(default=300, ge=1, description="Default per-IP limit for all routes.")
    EXPOSE_READINESS_ERRORS: bool = False
    HTTP_CLIENT_TIMEOUT: float = Field(default=30.0, gt=0)

    # Admin API (config / permission / menu writes) until the project has real auth.
    ADMIN_API_KEY: str | None = Field(
        default=None,
        description="Required in header X-API-Key. Unset = open in dev, refused in production.",
    )

    # Cache for the `config` table (ConfigService.get_value)
    CONFIG_CACHE_TTL_SECONDS: float = Field(default=60.0, ge=0)

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def _normalize_app_env(cls, value: object) -> str:
        return str(value or "development").strip().lower()

    @field_validator("LOG_DIR", mode="after")
    @classmethod
    def _resolve_log_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def api_docs_enabled(self) -> bool:
        if self.API_DOCS_ENABLED is not None:
            return self.API_DOCS_ENABLED
        return not self.is_production

    @property
    def pg_conninfo(self) -> str:
        return (
            f"host={self.PG_HOST} port={self.PG_PORT} dbname={self.PG_DATABASE} "
            f"user={self.PG_USER} password={self.PG_PASSWORD}"
        )

    def cors_origin_list(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return [] if self.is_production else list(_DEV_CORS_ORIGINS)
        return [part.strip() for part in raw.split(",") if part.strip()]

    def resolved_cors(self) -> tuple[list[str], bool]:
        origins = self.cors_origin_list()
        # Browsers reject credentials with a wildcard origin.
        allow_credentials = self.CORS_ALLOW_CREDENTIALS and "*" not in origins
        return origins, allow_credentials

    def validate_for_startup(self) -> None:
        if not self.is_production:
            return
        if "*" in self.cors_origin_list():
            raise RuntimeError("CORS_ORIGINS cannot include * in production")
        if self.JWT_SECRET_KEY is not None and len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
        if self.ADMIN_API_KEY is not None and len(self.ADMIN_API_KEY) < 32:
            raise RuntimeError("ADMIN_API_KEY must be at least 32 characters in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
