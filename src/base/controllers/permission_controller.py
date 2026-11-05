from base.requests.pagination import PageParams
from base.requests.permission_request import CreatePermissionRequest, UpdatePermissionRequest
from base.responses.common import Page
from base.responses.permission_response import PermissionGroupResponse, PermissionResponse
from base.services.permission_service import PermissionService


class PermissionController:
    async def page(
        self,
        params: PageParams,
        module: str | None,
        is_active: bool | None,
        search: str | None,
        service: PermissionService,
    ) -> Page[PermissionResponse]:
        rows, total = await service.page(
            limit=params.limit, offset=params.offset, module=module, is_active=is_active, search=search
        )
        return Page.build([PermissionResponse.model_validate(row) for row in rows], total, params)

    async def grouped(self, active_only: bool, service: PermissionService) -> list[PermissionGroupResponse]:
        return [
            PermissionGroupResponse(module=module, permissions=[PermissionResponse.model_validate(r) for r in rows])
            for module, rows in await service.grouped(active_only=active_only)
        ]

    async def get(self, permission_id: int, service: PermissionService) -> PermissionResponse:
        return PermissionResponse.model_validate(await service.get(permission_id))

    async def get_by_code(self, code: str, service: PermissionService) -> PermissionResponse:
        return PermissionResponse.model_validate(await service.get_by_code(code))

    async def create(self, request: CreatePermissionRequest, service: PermissionService) -> PermissionResponse:
        return PermissionResponse.model_validate(await service.create(request))

    async def update(
        self, permission_id: int, request: UpdatePermissionRequest, service: PermissionService
    ) -> PermissionResponse:
        return PermissionResponse.model_validate(await service.update(permission_id, request))

    async def delete(self, permission_id: int, service: PermissionService) -> None:
        await service.delete(permission_id)
