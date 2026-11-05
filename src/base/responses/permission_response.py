from datetime import datetime

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    module: str
    action: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PermissionGroupResponse(BaseModel):
    module: str
    permissions: list[PermissionResponse]
