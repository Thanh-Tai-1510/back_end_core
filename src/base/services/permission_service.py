from itertools import groupby
from typing import Any

from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation

from base.repositories.permission_repository import PermissionRepository
from base.requests.permission_request import CreatePermissionRequest, UpdatePermissionRequest
from base.services.base import BaseService
from core.exceptions import ConflictError, NotFoundError
from core.logging import Loggers, get_logger

logger = get_logger(f"{Loggers.SERVICE}.permission")


class PermissionService(BaseService):
    def __init__(self, db: AsyncConnection) -> None:
        super().__init__(db)
        self.repo = PermissionRepository(db)

    async def page(
        self,
        *,
        limit: int,
        offset: int,
        module: str | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        return await self.repo.page(limit=limit, offset=offset, module=module, is_active=is_active, search=search)

    async def grouped(self, *, active_only: bool) -> list[tuple[str, list[dict[str, Any]]]]:
        """All permissions grouped by module (rows come sorted by module)."""
        rows = await self.repo.list_all(active_only=active_only)
        return [(module, list(items)) for module, items in groupby(rows, key=lambda row: row["module"])]

    async def get(self, permission_id: int) -> dict[str, Any]:
        row = await self.repo.get(permission_id)
        if row is None:
            raise NotFoundError(f"Permission {permission_id} not found")
        return row

    async def get_by_code(self, code: str) -> dict[str, Any]:
        row = await self.repo.get_by_code(code)
        if row is None:
            raise NotFoundError(f"Permission '{code}' not found")
        return row

    async def create(self, request: CreatePermissionRequest) -> dict[str, Any]:
        if await self.repo.get_by_code(request.code) is not None:
            raise ConflictError(f"Permission '{request.code}' already exists")
        try:
            row = await self.repo.create(request.model_dump())
        except UniqueViolation as exc:
            raise ConflictError(f"Permission '{request.code}' already exists") from exc
        logger.info("Permission created: code=%s", request.code)
        return row

    async def update(self, permission_id: int, request: UpdatePermissionRequest) -> dict[str, Any]:
        fields = request.model_dump(exclude_unset=True)
        # These columns are NOT NULL; an explicit null means "no change".
        fields = {key: value for key, value in fields.items() if value is not None or key == "description"}
        row = await self.repo.update(permission_id, fields)
        if row is None:
            raise NotFoundError(f"Permission {permission_id} not found")
        logger.info("Permission updated: id=%s fields=%s", permission_id, sorted(fields))
        return row

    async def delete(self, permission_id: int) -> None:
        """Hard delete. Menus that required it become visible to everyone (permission_code -> NULL)."""
        if await self.repo.delete(permission_id) == 0:
            raise NotFoundError(f"Permission {permission_id} not found")
        logger.info("Permission deleted: id=%s", permission_id)
