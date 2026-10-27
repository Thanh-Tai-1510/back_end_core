from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.base.models.config import AppConfig
from src.base.repositories.config_repository import ConfigRepository
from src.base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from src.core.config.utils import is_sensitive_key, mask_config_value

logger = get_logger(Loggers.SERVICE)

__all__ = ["ConfigService", "is_sensitive_key", "mask_config_value"]


class ConfigService:
    def __init__(self, db: Session) -> None:
        self.repo = ConfigRepository(db)
        self._cache: dict[str, str] = {}

    def get(self, key: str, default: str | None = None) -> str | None:
        if key in self._cache:
            return self._cache[key]

        row = self.repo.get_by_key(key)
        if row is None or row.value is None:
            logger.debug("Config key not found: %s", key)
            return default

        self._cache[key] = row.value
        return row.value

    def get_row(self, key: str) -> AppConfig | None:
        return self.repo.get_by_key(key)

    def list_all(self) -> list[AppConfig]:
        return self.repo.list_all()

    def create(self, request: CreateConfigRequest) -> AppConfig:
        if self.repo.get_by_key(request.key):
            raise ValueError(f"Config key '{request.key}' already exists")

        row = AppConfig(key=request.key, type=request.type, value=request.value)
        self.repo.add(row)
        self.repo.commit()
        self.repo.refresh(row)
        self.refresh()
        logger.info("Config created: key=%s", request.key)
        return row

    def update(self, key: str, request: UpdateConfigRequest) -> AppConfig:
        row = self.repo.get_by_key(key)
        if row is None:
            raise ValueError(f"Config key '{key}' not found")

        data = request.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(row, field, value)

        self.repo.commit()
        self.repo.refresh(row)
        self.refresh()
        logger.info("Config updated: key=%s", key)
        return row

    def delete(self, key: str) -> None:
        row = self.repo.get_by_key(key)
        if row is None:
            raise ValueError(f"Config key '{key}' not found")

        self.repo.delete(row)
        self.repo.commit()
        self.refresh()
        logger.info("Config deleted: key=%s", key)

    def get_int(self, key: str, default: int) -> int:
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning("Invalid int config value for key=%s", key)
            return default

    def get_jwt_secret_key(self) -> str:
        secret = self.get("jwt_secret_key")
        if not secret:
            logger.error("Missing jwt_secret_key in config table")
            raise RuntimeError(
                "Missing 'jwt_secret_key' in config table. "
                "Insert it before using authentication."
            )
        return secret

    def get_jwt_algorithm(self) -> str:
        return self.get("jwt_algorithm") or "HS256"

    def get_jwt_expire_minutes(self) -> int:
        return self.get_int("jwt_expire_minutes", default=60)

    def refresh(self) -> None:
        self._cache.clear()
        logger.info("Config cache cleared")
