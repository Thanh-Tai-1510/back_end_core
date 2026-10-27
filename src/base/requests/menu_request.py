from pydantic import BaseModel, Field


class CreateMenuRequest(BaseModel):
    parent_id: int | None = None
    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_.]*$")
    name: str = Field(min_length=1, max_length=150)
    path: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=100)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True
    allowed_roles: list[str] | None = None


class UpdateMenuRequest(BaseModel):
    parent_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    path: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=100)
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    allowed_roles: list[str] | None = None
