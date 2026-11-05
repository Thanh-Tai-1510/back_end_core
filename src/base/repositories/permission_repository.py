from typing import Any

from base.repositories.base import BaseRepository

_UPDATABLE = ("name", "module", "action", "description", "is_active")


class PermissionRepository(BaseRepository):
    async def get(self, permission_id: int) -> dict[str, Any] | None:
        return await self._fetch_one("SELECT * FROM permissions WHERE id = %(id)s", {"id": permission_id})

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        return await self._fetch_one("SELECT * FROM permissions WHERE code = %(code)s", {"code": code})

    async def existing_codes(self, codes: list[str]) -> set[str]:
        rows = await self._fetch_all("SELECT code FROM permissions WHERE code = ANY(%(codes)s)", {"codes": codes})
        return {row["code"] for row in rows}

    async def page(
        self,
        *,
        limit: int,
        offset: int,
        module: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = ["TRUE"]
        params: dict[str, Any] = {}
        if module is not None:
            conditions.append("module = %(module)s")
            params["module"] = module
        if is_active is not None:
            conditions.append("is_active = %(is_active)s")
            params["is_active"] = is_active
        if search:
            conditions.append("(code ILIKE %(search)s OR name ILIKE %(search)s)")
            params["search"] = f"%{search}%"
        query = f"SELECT * FROM permissions WHERE {' AND '.join(conditions)} ORDER BY module, code"
        return await self._fetch_page(query, params, limit=limit, offset=offset)

    async def list_all(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        where = "WHERE is_active" if active_only else ""
        return await self._fetch_all(f"SELECT * FROM permissions {where} ORDER BY module, code")

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        row = await self._fetch_one(
            """
            INSERT INTO permissions (code, name, module, action, description, is_active)
            VALUES (%(code)s, %(name)s, %(module)s, %(action)s, %(description)s, %(is_active)s)
            RETURNING *
            """,
            data,
        )
        assert row is not None
        return row

    async def update(self, permission_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        return await self._update_returning(
            "permissions", {"id": permission_id}, fields, allowed=_UPDATABLE, touch_updated_at=True
        )

    async def delete(self, permission_id: int) -> int:
        return await self._execute("DELETE FROM permissions WHERE id = %(id)s", {"id": permission_id})
