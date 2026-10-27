from typing import Annotated

from fastapi import APIRouter, status

from src.base.controllers.deps import RoleServiceDep, require_permission
from src.base.controllers.role_controller import RoleController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.role_request import CreateRoleRequest, UpdateRoleRequest
from src.base.responses.role_response import RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])
controller = RoleController()


@router.get("", response_model=list[RoleResponse])
def list_roles(
    _: Annotated[User, require_permission(PermissionCode.ROLES_LIST)],
    role_service: RoleServiceDep,
) -> list[RoleResponse]:
    return controller.list_roles(role_service)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    _: Annotated[User, require_permission(PermissionCode.ROLES_READ)],
    role_service: RoleServiceDep,
) -> RoleResponse:
    return controller.get_role(role_id, role_service)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    request: CreateRoleRequest,
    current_user: Annotated[User, require_permission(PermissionCode.ROLES_CREATE)],
    role_service: RoleServiceDep,
) -> RoleResponse:
    return controller.create_role(request, current_user, role_service)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: UpdateRoleRequest,
    current_user: Annotated[User, require_permission(PermissionCode.ROLES_UPDATE)],
    role_service: RoleServiceDep,
) -> RoleResponse:
    return controller.update_role(role_id, request, current_user, role_service)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    current_user: Annotated[User, require_permission(PermissionCode.ROLES_DELETE)],
    role_service: RoleServiceDep,
) -> None:
    controller.delete_role(role_id, current_user, role_service)
