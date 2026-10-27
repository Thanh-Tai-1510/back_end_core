from typing import Annotated

from fastapi import APIRouter, status

from src.base.controllers.deps import MenuServiceDep, require_permission
from src.base.controllers.menu_controller import MenuController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.menu_request import CreateMenuRequest, UpdateMenuRequest
from src.base.responses.menu_response import MenuResponse, MenuTreeResponse

router = APIRouter(prefix="/menus", tags=["menus"])
controller = MenuController()


@router.get("/my/tree", response_model=list[MenuTreeResponse])
def get_my_menu_tree(
    current_user: Annotated[User, require_permission(PermissionCode.MENUS_MY_READ)],
    menu_service: MenuServiceDep,
) -> list[MenuTreeResponse]:
    return controller.get_my_menu_tree(current_user, menu_service)


@router.get("", response_model=list[MenuResponse])
def list_menus(
    _: Annotated[User, require_permission(PermissionCode.MENUS_LIST)],
    menu_service: MenuServiceDep,
) -> list[MenuResponse]:
    return controller.list_menus(menu_service)


@router.get("/tree", response_model=list[MenuTreeResponse])
def list_menu_tree(
    _: Annotated[User, require_permission(PermissionCode.MENUS_TREE)],
    menu_service: MenuServiceDep,
) -> list[MenuTreeResponse]:
    return controller.list_menu_tree(menu_service)


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(
    menu_id: int,
    _: Annotated[User, require_permission(PermissionCode.MENUS_READ)],
    menu_service: MenuServiceDep,
) -> MenuResponse:
    return controller.get_menu(menu_id, menu_service)


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    request: CreateMenuRequest,
    current_user: Annotated[User, require_permission(PermissionCode.MENUS_CREATE)],
    menu_service: MenuServiceDep,
) -> MenuResponse:
    return controller.create_menu(request, current_user, menu_service)


@router.put("/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    request: UpdateMenuRequest,
    current_user: Annotated[User, require_permission(PermissionCode.MENUS_UPDATE)],
    menu_service: MenuServiceDep,
) -> MenuResponse:
    return controller.update_menu(menu_id, request, current_user, menu_service)


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: int,
    current_user: Annotated[User, require_permission(PermissionCode.MENUS_DELETE)],
    menu_service: MenuServiceDep,
) -> None:
    controller.delete_menu(menu_id, current_user, menu_service)
