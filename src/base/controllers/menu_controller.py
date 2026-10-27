from fastapi import HTTPException, status

from src.base.controllers.deps import MenuServiceDep
from src.core.logging import Loggers, get_logger
from src.base.requests.menu_request import CreateMenuRequest, UpdateMenuRequest
from src.base.responses.menu_response import MenuResponse, MenuTreeResponse

logger = get_logger(Loggers.API)


class MenuController:
    def get_my_menu_tree(self, current_user, menu_service: MenuServiceDep) -> list[MenuTreeResponse]:
        return menu_service.list_tree_for_user(current_user)

    def list_menus(self, menu_service: MenuServiceDep) -> list[MenuResponse]:
        return [MenuResponse.from_model(menu) for menu in menu_service.list_all()]

    def list_menu_tree(self, menu_service: MenuServiceDep) -> list[MenuTreeResponse]:
        return menu_service.list_tree()

    def get_menu(self, menu_id: int, menu_service: MenuServiceDep) -> MenuResponse:
        menu = menu_service.get_by_id(menu_id)
        if menu is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
        return MenuResponse.from_model(menu)

    def create_menu(
        self,
        request: CreateMenuRequest,
        current_user,
        menu_service: MenuServiceDep,
    ) -> MenuResponse:
        try:
            menu = menu_service.create(request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Menu created by user id=%s code=%s", current_user.id, request.code)
        return MenuResponse.from_model(menu)

    def update_menu(
        self,
        menu_id: int,
        request: UpdateMenuRequest,
        current_user,
        menu_service: MenuServiceDep,
    ) -> MenuResponse:
        menu = menu_service.get_by_id(menu_id)
        if menu is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
        try:
            menu = menu_service.update(menu, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Menu updated by user id=%s menu_id=%s", current_user.id, menu_id)
        return MenuResponse.from_model(menu)

    def delete_menu(self, menu_id: int, current_user, menu_service: MenuServiceDep) -> None:
        menu = menu_service.get_by_id(menu_id)
        if menu is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
        menu_service.soft_delete(menu)
        logger.info("Menu deleted by user id=%s menu_id=%s", current_user.id, menu_id)
