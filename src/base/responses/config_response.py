from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.base.models.config import AppConfig
from src.core.config.utils import is_sensitive_key, mask_config_value


class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    type: str | None
    value: str | None
    created_at: datetime | None
    is_sensitive: bool = False

    @classmethod
    def from_model(cls, row: AppConfig, *, reveal_sensitive: bool = False) -> "ConfigResponse":
        sensitive = is_sensitive_key(row.key)
        return cls(
            key=row.key,
            type=row.type,
            value=mask_config_value(row.key, row.value, reveal=reveal_sensitive),
            created_at=row.created_at,
            is_sensitive=sensitive,
        )
