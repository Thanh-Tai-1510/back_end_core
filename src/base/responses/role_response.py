from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, role) -> "RoleResponse":
        return cls.model_validate(role)
