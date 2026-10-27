from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.base.models.menu import Menu
from src.base.models.user import User
from src.base.repositories.menu_repository import MenuRepository
from src.base.requests.menu_request import CreateMenuRequest, UpdateMenuRequest
from src.base.responses.menu_response import MenuResponse, MenuTreeResponse

logger = get_logger(Loggers.SERVICE)


class MenuService:
    def __init__(self, db: Session) -> None:
        self.repo = MenuRepository(db)

    def list_all(self) -> list[Menu]:
        return self.repo.list_all()

    def list_tree(self) -> list[MenuTreeResponse]:
        return self._build_tree(self.repo.list_all())

    def list_tree_for_user(self, user: User) -> list[MenuTreeResponse]:
        role_code = user.role.code
        visible = [
            menu
            for menu in self.repo.list_active()
            if self._is_visible_for_role(menu, role_code)
        ]
        return self._build_tree(visible)

    def get_by_id(self, menu_id: int) -> Menu | None:
        menu = self.repo.get_by_id(menu_id)
        if menu is None or menu.is_deleted:
            return None
        return menu

    def create(self, request: CreateMenuRequest) -> Menu:
        if self.repo.code_exists(request.code):
            raise ValueError(f"Menu code '{request.code}' already exists")
        if request.parent_id is not None:
            self._ensure_parent_exists(request.parent_id)

        menu = Menu(
            parent_id=request.parent_id,
            code=request.code,
            name=request.name,
            path=request.path,
            icon=request.icon,
            description=request.description,
            sort_order=request.sort_order,
            is_active=request.is_active,
            allowed_roles=request.allowed_roles,
        )
        self.repo.add(menu)
        self.repo.commit()
        self.repo.refresh(menu)
        logger.info("Menu created: id=%s code=%s", menu.id, menu.code)
        return menu

    def update(self, menu: Menu, request: UpdateMenuRequest) -> Menu:
        data = request.model_dump(exclude_unset=True)
        if "parent_id" in data:
            parent_id = data["parent_id"]
            if parent_id == menu.id:
                raise ValueError("Menu cannot be its own parent")
            if parent_id is not None:
                self._ensure_parent_exists(parent_id)

        for field, value in data.items():
            setattr(menu, field, value)

        self.repo.commit()
        self.repo.refresh(menu)
        logger.info("Menu updated: id=%s", menu.id)
        return menu

    def soft_delete(self, menu: Menu) -> None:
        menu.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        menu.is_active = False
        self.repo.commit()
        logger.info("Menu soft-deleted: id=%s", menu.id)

    def _ensure_parent_exists(self, parent_id: int) -> None:
        parent = self.get_by_id(parent_id)
        if parent is None:
            raise ValueError("Parent menu not found")

    @staticmethod
    def _is_visible_for_role(menu: Menu, role_code: str) -> bool:
        if menu.allowed_roles is None:
            return True
        return role_code in menu.allowed_roles

    @staticmethod
    def _build_tree(menus: list[Menu]) -> list[MenuTreeResponse]:
        menu_ids = {menu.id for menu in menus}
        by_parent: dict[int | None, list[Menu]] = defaultdict(list)
        for menu in menus:
            effective_parent = menu.parent_id if menu.parent_id in menu_ids else None
            by_parent[effective_parent].append(menu)

        for items in by_parent.values():
            items.sort(key=lambda item: (item.sort_order, item.id))

        def attach(node: Menu) -> MenuTreeResponse:
            children = [attach(child) for child in by_parent.get(node.id, [])]
            return MenuTreeResponse.from_model(node, children=children)

        return [attach(menu) for menu in by_parent.get(None, [])]
