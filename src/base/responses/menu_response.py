from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.base.models.menu import Menu


class MenuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    code: str
    name: str
    path: str | None
    icon: str | None
    description: str | None
    sort_order: int
    is_active: bool
    allowed_roles: list[str] | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, menu: Menu) -> "MenuResponse":
        return cls.model_validate(menu)


class MenuTreeResponse(MenuResponse):
    children: list["MenuTreeResponse"] = Field(default_factory=list)

    @classmethod
    def from_model(cls, menu: Menu, *, children: list["MenuTreeResponse"] | None = None) -> "MenuTreeResponse":
        data = cls.model_validate(menu).model_dump()
        data["children"] = children or []
        return cls(**data)
