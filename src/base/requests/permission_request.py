from pydantic import BaseModel, Field

from src.base.models.enums import PermissionEffect


class UserPermissionOverrideItem(BaseModel):
    permission_id: int
    effect: PermissionEffect
    note: str | None = Field(default=None, max_length=500)


class UpdateRolePermissionsRequest(BaseModel):
    permission_ids: list[int]


class UpdateUserPermissionsRequest(BaseModel):
    overrides: list[UserPermissionOverrideItem]
