from pydantic import BaseModel, Field

MENU_CODE_PATTERN = r"^[a-z0-9_.-]{1,100}$"


class CreateMenuRequest(BaseModel):
    code: str = Field(pattern=MENU_CODE_PATTERN, examples=["settings"])
    name: str = Field(min_length=1, max_length=150)
    parent_id: int | None = None
    path: str | None = Field(default=None, max_length=255, examples=["/settings"])
    icon: str | None = Field(default=None, max_length=100)
    description: str | None = None
    permission_code: str | None = Field(default=None, max_length=100, description="Permission needed to see it")
    sort_order: int = 0
    is_active: bool = True


class UpdateMenuRequest(BaseModel):
    """Send only fields to change. `parent_id: null` moves the item to the root."""

    code: str | None = Field(default=None, pattern=MENU_CODE_PATTERN)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    parent_id: int | None = None
    path: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=100)
    description: str | None = None
    permission_code: str | None = Field(default=None, max_length=100)
    sort_order: int | None = None
    is_active: bool | None = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int
    parent_id: int | None = None


class ReorderMenusRequest(BaseModel):
    """Bulk drag-and-drop save: new parent and position for each listed menu."""

    items: list[ReorderItem] = Field(min_length=1, max_length=500)
