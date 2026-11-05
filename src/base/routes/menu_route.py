from fastapi import APIRouter, status

from base.controllers.deps import AdminGuard, MenuServiceDep
from base.controllers.menu_controller import MenuController
from base.requests.menu_request import CreateMenuRequest, ReorderMenusRequest, UpdateMenuRequest
from base.responses.menu_response import MenuResponse, MenuTreeResponse

# Reads are open (the frontend builds its sidebar from them); writes need the admin key.
router = APIRouter(prefix="/menus", tags=["menus"])
controller = MenuController()


@router.get("", response_model=list[MenuResponse])
async def list_menus(service: MenuServiceDep, active_only: bool = False) -> list[MenuResponse]:
    return await controller.list_menus(active_only, service)


@router.get("/tree", response_model=list[MenuTreeResponse])
async def menu_tree(service: MenuServiceDep, active_only: bool = True) -> list[MenuTreeResponse]:
    return await controller.tree(active_only, service)


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(menu_id: int, service: MenuServiceDep) -> MenuResponse:
    return await controller.get(menu_id, service)


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED, dependencies=[AdminGuard])
async def create_menu(request: CreateMenuRequest, service: MenuServiceDep) -> MenuResponse:
    return await controller.create(request, service)


@router.put("/reorder", response_model=list[MenuResponse], dependencies=[AdminGuard])
async def reorder_menus(request: ReorderMenusRequest, service: MenuServiceDep) -> list[MenuResponse]:
    """Save a drag-and-drop result: new parent and sort_order per menu, in one transaction."""
    return await controller.reorder(request, service)


@router.patch("/{menu_id}", response_model=MenuResponse, dependencies=[AdminGuard])
async def update_menu(menu_id: int, request: UpdateMenuRequest, service: MenuServiceDep) -> MenuResponse:
    return await controller.update(menu_id, request, service)


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[AdminGuard])
async def delete_menu(menu_id: int, service: MenuServiceDep, cascade: bool = False) -> None:
    """With children: 409 unless cascade=true, which deletes the whole subtree."""
    await controller.delete(menu_id, cascade, service)
