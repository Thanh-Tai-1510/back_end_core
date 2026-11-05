from collections.abc import Collection
from typing import Any

from psycopg import AsyncConnection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from base.repositories.menu_repository import MenuRepository
from base.repositories.permission_repository import PermissionRepository
from base.requests.menu_request import CreateMenuRequest, ReorderMenusRequest, UpdateMenuRequest
from base.services.base import BaseService
from core.exceptions import BadRequestError, ConflictError, NotFoundError
from core.logging import Loggers, get_logger

logger = get_logger(f"{Loggers.SERVICE}.menu")

MenuNode = dict[str, Any]
# Columns that are NOT NULL: an explicit null in an update means "no change".
_NOT_NULL_FIELDS = {"code", "name", "sort_order", "is_active"}


def build_tree(rows: list[dict[str, Any]], allowed_permissions: Collection[str] | None = None) -> list[MenuNode]:
    """Nest flat rows (already ordered by sort_order) into a tree.

    With allowed_permissions, items whose permission_code is not in it are dropped with their
    subtree, and groups (no path) left without children are dropped too.
    """
    nodes = {row["id"]: {**row, "children": []} for row in rows}
    roots: list[MenuNode] = []
    for node in nodes.values():
        parent = nodes.get(node["parent_id"]) if node["parent_id"] is not None else None
        if parent is not None:
            parent["children"].append(node)
        elif node["parent_id"] is None:
            roots.append(node)
        # A parent missing from rows (e.g. inactive) hides the whole branch.

    if allowed_permissions is None:
        return roots

    allowed = set(allowed_permissions)

    def visible(node: MenuNode) -> bool:
        code = node["permission_code"]
        if code is not None and code not in allowed:
            return False
        node["children"] = [child for child in node["children"] if visible(child)]
        return bool(node["path"]) or bool(node["children"])

    return [root for root in roots if visible(root)]


class MenuService(BaseService):
    def __init__(self, db: AsyncConnection) -> None:
        super().__init__(db)
        self.repo = MenuRepository(db)
        self.permissions = PermissionRepository(db)

    async def list_menus(self, *, active_only: bool) -> list[dict[str, Any]]:
        return await self.repo.list_all(active_only=active_only)

    async def tree(
        self,
        *,
        active_only: bool,
        allowed_permissions: Collection[str] | None = None,
    ) -> list[MenuNode]:
        """Pass allowed_permissions (e.g. the current user's codes) to get only what they may see."""
        return build_tree(await self.repo.list_all(active_only=active_only), allowed_permissions)

    async def get(self, menu_id: int) -> dict[str, Any]:
        row = await self.repo.get(menu_id)
        if row is None:
            raise NotFoundError(f"Menu {menu_id} not found")
        return row

    async def create(self, request: CreateMenuRequest) -> dict[str, Any]:
        await self._check_code_free(request.code)
        if request.parent_id is not None:
            await self._check_parent_exists(request.parent_id)
        await self._check_permission(request.permission_code)
        try:
            row = await self.repo.create(request.model_dump())
        except UniqueViolation as exc:
            raise ConflictError(f"Menu code '{request.code}' already exists") from exc
        except ForeignKeyViolation as exc:
            raise BadRequestError("Parent menu or permission no longer exists") from exc
        logger.info("Menu created: id=%s code=%s", row["id"], row["code"])
        return row

    async def update(self, menu_id: int, request: UpdateMenuRequest) -> dict[str, Any]:
        current = await self.get(menu_id)
        fields = {
            key: value
            for key, value in request.model_dump(exclude_unset=True).items()
            if value is not None or key not in _NOT_NULL_FIELDS
        }
        if "code" in fields and fields["code"] != current["code"]:
            await self._check_code_free(fields["code"])
        if fields.get("parent_id") is not None:
            await self._check_parent_exists(fields["parent_id"])
            if await self.repo.is_in_subtree(menu_id, fields["parent_id"]):
                raise BadRequestError("A menu cannot be moved under itself or one of its children")
        if "permission_code" in fields:
            await self._check_permission(fields["permission_code"])
        try:
            row = await self.repo.update(menu_id, fields)
        except UniqueViolation as exc:
            raise ConflictError(f"Menu code '{fields.get('code')}' already exists") from exc
        except ForeignKeyViolation as exc:
            raise BadRequestError("Parent menu or permission no longer exists") from exc
        if row is None:
            raise NotFoundError(f"Menu {menu_id} not found")
        logger.info("Menu updated: id=%s fields=%s", menu_id, sorted(fields))
        return row

    async def reorder(self, request: ReorderMenusRequest) -> list[dict[str, Any]]:
        ids = [item.id for item in request.items]
        if len(set(ids)) != len(ids):
            raise BadRequestError("Each menu id may appear only once")
        async with self.transaction():
            for item in request.items:
                if item.parent_id == item.id:
                    raise BadRequestError(f"Menu {item.id} cannot be its own parent")
                try:
                    row = await self.repo.update(item.id, {"sort_order": item.sort_order, "parent_id": item.parent_id})
                except ForeignKeyViolation as exc:
                    raise BadRequestError(f"Parent menu {item.parent_id} not found") from exc
                if row is None:
                    raise NotFoundError(f"Menu {item.id} not found")
            if await self.repo.has_cycle():
                raise BadRequestError("This order would put a menu under its own child")
        logger.info("Menus reordered: %s item(s)", len(ids))
        return await self.repo.list_all()

    async def delete(self, menu_id: int, *, cascade: bool) -> None:
        await self.get(menu_id)
        if not cascade and await self.repo.has_children(menu_id):
            raise ConflictError("Menu has children: delete them first or pass cascade=true")
        await self.repo.delete(menu_id)
        logger.info("Menu deleted: id=%s cascade=%s", menu_id, cascade)

    async def _check_code_free(self, code: str) -> None:
        if await self.repo.get_by_code(code) is not None:
            raise ConflictError(f"Menu code '{code}' already exists")

    async def _check_parent_exists(self, parent_id: int) -> None:
        if await self.repo.get(parent_id) is None:
            raise BadRequestError(f"Parent menu {parent_id} not found")

    async def _check_permission(self, code: str | None) -> None:
        if code is not None and await self.permissions.get_by_code(code) is None:
            raise BadRequestError(f"Permission '{code}' not found")
