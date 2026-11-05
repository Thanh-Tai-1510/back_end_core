from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from base.controllers.deps import AdminGuard, PageParamsDep, PermissionServiceDep
from base.controllers.permission_controller import PermissionController
from base.requests.permission_request import (
    PERMISSION_CODE_PATTERN,
    CreatePermissionRequest,
    UpdatePermissionRequest,
)
from base.responses.common import Page
from base.responses.permission_response import PermissionGroupResponse, PermissionResponse

router = APIRouter(prefix="/permissions", tags=["permissions"], dependencies=[AdminGuard])
controller = PermissionController()


@router.get("", response_model=Page[PermissionResponse])
async def list_permissions(
    params: PageParamsDep,
    service: PermissionServiceDep,
    module: str | None = None,
    is_active: bool | None = None,
    q: Annotated[str | None, Query(max_length=100, description="Search in code and name")] = None,
) -> Page[PermissionResponse]:
    return await controller.page(params, module, is_active, q, service)


@router.get("/grouped", response_model=list[PermissionGroupResponse])
async def list_permissions_grouped(
    service: PermissionServiceDep,
    active_only: bool = True,
) -> list[PermissionGroupResponse]:
    """Every permission grouped by module, e.g. for a role/permission matrix screen."""
    return await controller.grouped(active_only, service)


@router.get("/code/{code}", response_model=PermissionResponse)
async def get_permission_by_code(
    code: Annotated[str, Path(max_length=100, pattern=PERMISSION_CODE_PATTERN)],
    service: PermissionServiceDep,
) -> PermissionResponse:
    return await controller.get_by_code(code, service)


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(permission_id: int, service: PermissionServiceDep) -> PermissionResponse:
    return await controller.get(permission_id, service)


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(request: CreatePermissionRequest, service: PermissionServiceDep) -> PermissionResponse:
    return await controller.create(request, service)


@router.patch("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int, request: UpdatePermissionRequest, service: PermissionServiceDep
) -> PermissionResponse:
    return await controller.update(permission_id, request, service)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(permission_id: int, service: PermissionServiceDep) -> None:
    await controller.delete(permission_id, service)
