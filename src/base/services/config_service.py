import json
import re
import time
from typing import Any

from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation

from base.repositories.config_repository import ConfigRepository
from base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from base.services.base import BaseService
from core.config import settings
from core.exceptions import ConflictError, NotFoundError
from core.logging import Loggers, get_logger

logger = get_logger(f"{Loggers.SERVICE}.config")

# A key is secret when its last word is one of these (smtp_password, n8n_inbound_secret)
# or its last two words are (jwt_secret_key, openai_api_key). "access_token_expire_minutes"
# and "cors_allow_credentials" are not secrets: their last word is a unit or a flag.
_SECRET_LAST_WORDS = {"secret", "password", "passwd", "pwd", "token", "credential", "apikey", "dsn"}
_SECRET_LAST_PAIRS = {("secret", "key"), ("api", "key"), ("private", "key"), ("access", "key"), ("signing", "key")}
MASK = "********"
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}

# Process-wide cache of key -> value. Writes clear it after commit; other workers pick up
# changes within CONFIG_CACHE_TTL_SECONDS.
_cache: dict[str, str | None] | None = None
_cache_loaded_at = 0.0


def is_sensitive_key(key: str) -> bool:
    words = [word for word in re.split(r"[_.:\-]+", key.lower()) if word]
    if not words:
        return False
    return words[-1] in _SECRET_LAST_WORDS or tuple(words[-2:]) in _SECRET_LAST_PAIRS


def mask_value(key: str, value: str | None) -> str | None:
    if value and is_sensitive_key(key):
        return MASK
    return value


def invalidate_config_cache() -> None:
    global _cache
    _cache = None


class ConfigService(BaseService):
    def __init__(self, db: AsyncConnection) -> None:
        super().__init__(db)
        self.repo = ConfigRepository(db)

    # --- typed reads for application code (cached) ---

    async def _values(self) -> dict[str, str | None]:
        global _cache, _cache_loaded_at
        now = time.monotonic()
        if _cache is None or now - _cache_loaded_at > settings.CONFIG_CACHE_TTL_SECONDS:
            _cache = {row["key"]: row["value"] for row in await self.repo.list_all()}
            _cache_loaded_at = now
        return _cache

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        value = (await self._values()).get(key)
        return default if value is None else value

    async def get_int(self, key: str, default: int) -> int:
        value = await self.get_value(key)
        try:
            return int(value) if value is not None else default
        except ValueError:
            logger.warning("Config %s is not an int: using default", key)
            return default

    async def get_float(self, key: str, default: float) -> float:
        value = await self.get_value(key)
        try:
            return float(value) if value is not None else default
        except ValueError:
            logger.warning("Config %s is not a number: using default", key)
            return default

    async def get_bool(self, key: str, default: bool) -> bool:
        value = await self.get_value(key)
        if value is None:
            return default
        lowered = value.strip().lower()
        if lowered in _TRUE:
            return True
        if lowered in _FALSE:
            return False
        logger.warning("Config %s is not a bool: using default", key)
        return default

    async def get_json(self, key: str, default: Any = None) -> Any:
        value = await self.get_value(key)
        try:
            return json.loads(value) if value is not None else default
        except ValueError:
            logger.warning("Config %s is not valid JSON: using default", key)
            return default

    async def refresh_cache(self) -> int:
        invalidate_config_cache()
        return len(await self._values())

    # --- admin CRUD (uncached) ---

    async def page(self, *, limit: int, offset: int, type_: str | None, search: str | None):
        return await self.repo.page(limit=limit, offset=offset, type_=type_, search=search)

    async def list_types(self) -> list[str]:
        return await self.repo.list_types()

    async def get(self, key: str) -> dict[str, Any]:
        row = await self.repo.get(key)
        if row is None:
            raise NotFoundError(f"Config '{key}' not found")
        return row

    async def create(self, request: CreateConfigRequest) -> dict[str, Any]:
        if await self.repo.get(request.key) is not None:
            raise ConflictError(f"Config '{request.key}' already exists")
        try:
            row = await self.repo.create(request.key, request.type, request.value)
        except UniqueViolation as exc:
            raise ConflictError(f"Config '{request.key}' already exists") from exc
        await self._commit()
        logger.info("Config created: key=%s", request.key)
        return row

    async def update(self, key: str, request: UpdateConfigRequest) -> dict[str, Any]:
        row = await self.repo.update(key, request.model_dump(exclude_unset=True))
        if row is None:
            raise NotFoundError(f"Config '{key}' not found")
        await self._commit()
        logger.info("Config updated: key=%s fields=%s", key, sorted(request.model_fields_set))
        return row

    async def delete(self, key: str) -> None:
        if await self.repo.delete(key) == 0:
            raise NotFoundError(f"Config '{key}' not found")
        await self._commit()
        logger.info("Config deleted: key=%s", key)

    async def _commit(self) -> None:
        # Commit before clearing the cache, so a concurrent reload can't cache the old value.
        await self.db.commit()
        invalidate_config_cache()
