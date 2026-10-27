from fastapi import HTTPException, status

from src.base.controllers.deps import PermissionServiceDep
from src.core.logging import Loggers, get_logger
from src.base.requests.permission_request import UpdateRolePermissionsRequest, UpdateUserPermissionsRequest
from src.base.responses.permission_response import (
    MyPermissionsResponse,
    PermissionResponse,
    RolePermissionsResponse,
    UserPermissionsResponse,
)

logger = get_logger(Loggers.API)


class PermissionController:
    def get_my_permissions(self, current_user, permission_service: PermissionServiceDep) -> MyPermissionsResponse:
        return MyPermissionsResponse.from_codes(permission_service.get_effective_codes(current_user))

    def list_permissions(self, permission_service: PermissionServiceDep) -> list[PermissionResponse]:
        return [PermissionResponse.from_model(p) for p in permission_service.list_permissions()]

    def get_permission(self, permission_id: int, permission_service: PermissionServiceDep) -> PermissionResponse:
        permission = permission_service.get_by_id(permission_id)
        if permission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        return PermissionResponse.from_model(permission)

    def get_role_permissions(
        self,
        role_id: int,
        permission_service: PermissionServiceDep,
    ) -> RolePermissionsResponse:
        role = permission_service.get_role_permissions(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return RolePermissionsResponse.from_model(role)

    def update_role_permissions(
        self,
        role_id: int,
        request: UpdateRolePermissionsRequest,
        current_user,
        permission_service: PermissionServiceDep,
    ) -> RolePermissionsResponse:
        role = permission_service.get_role_permissions(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        try:
            role = permission_service.update_role_permissions(role, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Role permissions updated by user id=%s role_id=%s", current_user.id, role_id)
        return RolePermissionsResponse.from_model(role)

    def get_user_permissions(
        self,
        user_id: int,
        permission_service: PermissionServiceDep,
    ) -> UserPermissionsResponse:
        user = permission_service.get_user_overrides(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        role_codes = permission_service.repo.get_role_permission_codes(user.role_id)
        effective = permission_service.get_effective_codes(user)
        return UserPermissionsResponse.build(user, role_codes, effective)

    def update_user_permissions(
        self,
        user_id: int,
        request: UpdateUserPermissionsRequest,
        current_user,
        permission_service: PermissionServiceDep,
    ) -> UserPermissionsResponse:
        user = permission_service.get_user_overrides(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        try:
            user = permission_service.update_user_permissions(user, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("User permissions updated by user id=%s target_user_id=%s", current_user.id, user_id)
        role_codes = permission_service.repo.get_role_permission_codes(user.role_id)
        effective = permission_service.get_effective_codes(user)
        return UserPermissionsResponse.build(user, role_codes, effective)
