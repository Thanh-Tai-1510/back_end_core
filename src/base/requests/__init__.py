from src.base.requests.auth_request import LoginRequest, RegisterRequest
from src.base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from src.base.requests.menu_request import CreateMenuRequest, UpdateMenuRequest
from src.base.requests.role_request import CreateRoleRequest, UpdateRoleRequest
from src.base.requests.user_request import (
    AdminUpdateUserRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
)

__all__ = [
    "AdminUpdateUserRequest",
    "ChangePasswordRequest",
    "CreateConfigRequest",
    "CreateMenuRequest",
    "CreateRoleRequest",
    "LoginRequest",
    "RegisterRequest",
    "UpdateConfigRequest",
    "UpdateMenuRequest",
    "UpdateProfileRequest",
    "UpdateRoleRequest",
]
