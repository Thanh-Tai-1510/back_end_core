from datetime import datetime

from pydantic import BaseModel


class ConfigResponse(BaseModel):
    key: str
    type: str | None
    value: str | None
    is_secret: bool
    created_at: datetime | None = None
