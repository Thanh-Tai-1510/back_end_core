from typing import Annotated

from fastapi import APIRouter

from src.base.controllers.deps import PermissionServiceDep, require_permission
from src.base.controllers.permission_controller import PermissionController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.permission_request import UpdateRolePermissionsRequest, UpdateUserPermissionsRequest
from src.base.responses.permission_response import (
    MyPermissionsResponse,
    PermissionResponse,
    RolePermissionsResponse,
    UserPermissionsResponse,
)

router = APIRouter(prefix="/permissions", tags=["permissions"])
controller = PermissionController()


@router.get("/my", response_model=MyPermissionsResponse)
def get_my_permissions(
    current_user: Annotated[User, require_permission(PermissionCode.PERMISSIONS_MY)],
    permission_service: PermissionServiceDep,
) -> MyPermissionsResponse:
    return controller.get_my_permissions(current_user, permission_service)


@router.get("", response_model=list[PermissionResponse])
def list_permissions(
    _: Annotated[User, require_permission(PermissionCode.PERMISSIONS_LIST)],
    permission_service: PermissionServiceDep,
) -> list[PermissionResponse]:
    return controller.list_permissions(permission_service)


@router.get("/roles/{role_id}", response_model=RolePermissionsResponse)
def get_role_permissions(
    role_id: int,
    _: Annotated[User, require_permission(PermissionCode.PERMISSIONS_ROLE_READ)],
    permission_service: PermissionServiceDep,
) -> RolePermissionsResponse:
    return controller.get_role_permissions(role_id, permission_service)


@router.put("/roles/{role_id}", response_model=RolePermissionsResponse)
def update_role_permissions(
    role_id: int,
    request: UpdateRolePermissionsRequest,
    current_user: Annotated[User, require_permission(PermissionCode.PERMISSIONS_ROLE_UPDATE)],
    permission_service: PermissionServiceDep,
) -> RolePermissionsResponse:
    return controller.update_role_permissions(role_id, request, current_user, permission_service)


@router.get("/users/{user_id}", response_model=UserPermissionsResponse)
def get_user_permissions(
    user_id: int,
    _: Annotated[User, require_permission(PermissionCode.PERMISSIONS_USER_READ)],
    permission_service: PermissionServiceDep,
) -> UserPermissionsResponse:
    return controller.get_user_permissions(user_id, permission_service)


@router.put("/users/{user_id}", response_model=UserPermissionsResponse)
def update_user_permissions(
    user_id: int,
    request: UpdateUserPermissionsRequest,
    current_user: Annotated[User, require_permission(PermissionCode.PERMISSIONS_USER_UPDATE)],
    permission_service: PermissionServiceDep,
) -> UserPermissionsResponse:
    return controller.update_user_permissions(user_id, request, current_user, permission_service)


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(
    permission_id: int,
    _: Annotated[User, require_permission(PermissionCode.PERMISSIONS_READ)],
    permission_service: PermissionServiceDep,
) -> PermissionResponse:
    return controller.get_permission(permission_id, permission_service)
