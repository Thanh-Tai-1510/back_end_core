from src.base.controllers.deps import (
    AuthServiceDep,
    ConfigDep,
    CurrentUser,
    DbSession,
    MenuServiceDep,
    PermissionServiceDep,
    RoleServiceDep,
    UserServiceDep,
    require_permission,
)
from src.base.routes.registry import V1_ROUTES, build_v1_router, list_v1_routes
from src.base.services import (
    AuthService,
    ConfigService,
    MenuService,
    PermissionService,
    RoleService,
    UserService,
)

__all__ = [
    "AuthService",
    "AuthServiceDep",
    "ConfigDep",
    "ConfigService",
    "CurrentUser",
    "DbSession",
    "MenuService",
    "MenuServiceDep",
    "PermissionService",
    "PermissionServiceDep",
    "RoleService",
    "RoleServiceDep",
    "UserService",
    "UserServiceDep",
    "V1_ROUTES",
    "build_v1_router",
    "list_v1_routes",
    "require_permission",
]
