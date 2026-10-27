from fastapi import HTTPException, status

from src.base.controllers.deps import RoleServiceDep
from src.core.logging import Loggers, get_logger
from src.base.requests.role_request import CreateRoleRequest, UpdateRoleRequest
from src.base.responses.role_response import RoleResponse

logger = get_logger(Loggers.API)


class RoleController:
    def list_roles(self, role_service: RoleServiceDep) -> list[RoleResponse]:
        return [RoleResponse.from_model(role) for role in role_service.list_roles()]

    def get_role(self, role_id: int, role_service: RoleServiceDep) -> RoleResponse:
        role = role_service.get_by_id(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return RoleResponse.from_model(role)

    def create_role(
        self,
        request: CreateRoleRequest,
        current_user,
        role_service: RoleServiceDep,
    ) -> RoleResponse:
        try:
            role = role_service.create(request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Role created by user id=%s code=%s", current_user.id, request.code)
        return RoleResponse.from_model(role)

    def update_role(
        self,
        role_id: int,
        request: UpdateRoleRequest,
        current_user,
        role_service: RoleServiceDep,
    ) -> RoleResponse:
        role = role_service.get_by_id(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        role = role_service.update(role, request)
        logger.info("Role updated by user id=%s role_id=%s", current_user.id, role_id)
        return RoleResponse.from_model(role)

    def delete_role(self, role_id: int, current_user, role_service: RoleServiceDep) -> None:
        role = role_service.get_by_id(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        try:
            role_service.soft_delete(role)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Role deleted by user id=%s role_id=%s", current_user.id, role_id)
