from typing import Any

from pydantic import BaseModel


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None
    raw: Any | None = None
