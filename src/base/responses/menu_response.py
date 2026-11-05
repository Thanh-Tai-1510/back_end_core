from datetime import datetime

from pydantic import BaseModel


class MenuResponse(BaseModel):
    id: int
    parent_id: int | None
    code: str
    name: str
    path: str | None
    icon: str | None
    description: str | None
    permission_code: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MenuTreeResponse(MenuResponse):
    children: list["MenuTreeResponse"] = []
