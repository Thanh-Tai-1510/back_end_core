from typing import Any

from base.repositories.base import BaseRepository

_UPDATABLE = ("type", "value")


class ConfigRepository(BaseRepository):
    async def get(self, key: str) -> dict[str, Any] | None:
        return await self._fetch_one("SELECT * FROM config WHERE key = %(key)s", {"key": key})

    async def list_all(self) -> list[dict[str, Any]]:
        return await self._fetch_all("SELECT * FROM config ORDER BY key")

    async def page(
        self,
        *,
        limit: int,
        offset: int,
        type_: str | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = ["TRUE"]
        params: dict[str, Any] = {}
        if type_ is not None:
            conditions.append("type = %(type)s")
            params["type"] = type_
        if search:
            conditions.append("key ILIKE %(search)s")
            params["search"] = f"%{search}%"
        query = f"SELECT * FROM config WHERE {' AND '.join(conditions)} ORDER BY type NULLS LAST, key"
        return await self._fetch_page(query, params, limit=limit, offset=offset)

    async def list_types(self) -> list[str]:
        rows = await self._fetch_all("SELECT DISTINCT type FROM config WHERE type IS NOT NULL ORDER BY type")
        return [row["type"] for row in rows]

    async def create(self, key: str, type_: str | None, value: str | None) -> dict[str, Any]:
        row = await self._fetch_one(
            "INSERT INTO config (key, type, value) VALUES (%(key)s, %(type)s, %(value)s) RETURNING *",
            {"key": key, "type": type_, "value": value},
        )
        assert row is not None
        return row

    async def update(self, key: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        return await self._update_returning("config", {"key": key}, fields, allowed=_UPDATABLE)

    async def delete(self, key: str) -> int:
        return await self._execute("DELETE FROM config WHERE key = %(key)s", {"key": key})
