from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Chỉ đọc cấu hình kết nối PostgreSQL từ .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: int = 5432
    PG_DATABASE: str
    PG_SCHEMA: str = "web_app"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
