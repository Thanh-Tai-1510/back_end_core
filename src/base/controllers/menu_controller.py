from base.requests.menu_request import CreateMenuRequest, ReorderMenusRequest, UpdateMenuRequest
from base.responses.menu_response import MenuResponse, MenuTreeResponse
from base.services.menu_service import MenuService


class MenuController:
    async def list_menus(self, active_only: bool, service: MenuService) -> list[MenuResponse]:
        return [MenuResponse.model_validate(row) for row in await service.list_menus(active_only=active_only)]

    async def tree(self, active_only: bool, service: MenuService) -> list[MenuTreeResponse]:
        return [MenuTreeResponse.model_validate(node) for node in await service.tree(active_only=active_only)]

    async def get(self, menu_id: int, service: MenuService) -> MenuResponse:
        return MenuResponse.model_validate(await service.get(menu_id))

    async def create(self, request: CreateMenuRequest, service: MenuService) -> MenuResponse:
        return MenuResponse.model_validate(await service.create(request))

    async def update(self, menu_id: int, request: UpdateMenuRequest, service: MenuService) -> MenuResponse:
        return MenuResponse.model_validate(await service.update(menu_id, request))

    async def reorder(self, request: ReorderMenusRequest, service: MenuService) -> list[MenuResponse]:
        return [MenuResponse.model_validate(row) for row in await service.reorder(request)]

    async def delete(self, menu_id: int, cascade: bool, service: MenuService) -> None:
        await service.delete(menu_id, cascade=cascade)
