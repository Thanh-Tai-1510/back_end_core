from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.base.models.enums import PermissionEffect
from src.base.models.permission import Permission, UserPermission
from src.base.models.role import Role
from src.base.models.user import User


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    module: str
    action: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, permission: Permission) -> "PermissionResponse":
        return cls.model_validate(permission)


class UserPermissionOverrideResponse(BaseModel):
    permission_id: int
    permission_code: str
    permission_name: str
    effect: PermissionEffect
    note: str | None

    @classmethod
    def from_model(cls, override: UserPermission) -> "UserPermissionOverrideResponse":
        return cls(
            permission_id=override.permission_id,
            permission_code=override.permission.code,
            permission_name=override.permission.name,
            effect=PermissionEffect.from_value(override.effect),
            note=override.note,
        )


class RolePermissionsResponse(BaseModel):
    role_id: int
    role_code: str
    role_name: str
    permissions: list[PermissionResponse]

    @classmethod
    def from_model(cls, role: Role) -> "RolePermissionsResponse":
        return cls(
            role_id=role.id,
            role_code=role.code,
            role_name=role.name,
            permissions=[PermissionResponse.from_model(p) for p in role.permissions],
        )


class UserPermissionsResponse(BaseModel):
    user_id: int
    username: str
    role_id: int
    role_code: str
    role_permissions: list[str]
    overrides: list[UserPermissionOverrideResponse]
    effective_permissions: list[str]

    @classmethod
    def build(
        cls,
        user: User,
        role_codes: set[str],
        effective_codes: set[str],
    ) -> "UserPermissionsResponse":
        return cls(
            user_id=user.id,
            username=user.username,
            role_id=user.role_id,
            role_code=user.role.code,
            role_permissions=sorted(role_codes),
            overrides=[UserPermissionOverrideResponse.from_model(o) for o in user.permission_overrides],
            effective_permissions=sorted(effective_codes),
        )


class MyPermissionsResponse(BaseModel):
    permissions: list[str]

    @classmethod
    def from_codes(cls, codes: set[str]) -> "MyPermissionsResponse":
        return cls(permissions=sorted(codes))
