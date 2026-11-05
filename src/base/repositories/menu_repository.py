from typing import Any

from base.repositories.base import BaseRepository

_UPDATABLE = (
    "parent_id",
    "code",
    "name",
    "path",
    "icon",
    "description",
    "permission_code",
    "sort_order",
    "is_active",
)


class MenuRepository(BaseRepository):
    async def get(self, menu_id: int) -> dict[str, Any] | None:
        return await self._fetch_one("SELECT * FROM menus WHERE id = %(id)s", {"id": menu_id})

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        return await self._fetch_one("SELECT * FROM menus WHERE code = %(code)s", {"code": code})

    async def list_all(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        where = "WHERE is_active" if active_only else ""
        return await self._fetch_all(f"SELECT * FROM menus {where} ORDER BY sort_order, id")

    async def has_children(self, menu_id: int) -> bool:
        return bool(
            await self._fetch_scalar(
                "SELECT EXISTS (SELECT 1 FROM menus WHERE parent_id = %(id)s) AS has", {"id": menu_id}
            )
        )

    async def is_in_subtree(self, root_id: int, candidate_id: int) -> bool:
        """True if candidate_id is root_id or one of its descendants."""
        return bool(
            await self._fetch_scalar(
                """
                WITH RECURSIVE subtree AS (
                    SELECT id FROM menus WHERE id = %(root)s
                    UNION ALL
                    SELECT m.id FROM menus m JOIN subtree s ON m.parent_id = s.id
                )
                SELECT EXISTS (SELECT 1 FROM subtree WHERE id = %(candidate)s) AS found
                """,
                {"root": root_id, "candidate": candidate_id},
            )
        )

    async def has_cycle(self) -> bool:
        """True if following parent_id from any menu leads back to itself."""
        return bool(
            await self._fetch_scalar(
                """
                WITH RECURSIVE walk (start_id, parent_id, depth) AS (
                    SELECT id, parent_id, 1 FROM menus WHERE parent_id IS NOT NULL
                    UNION ALL
                    SELECT w.start_id, m.parent_id, w.depth + 1
                    FROM walk w JOIN menus m ON m.id = w.parent_id
                    WHERE m.parent_id IS NOT NULL AND w.parent_id <> w.start_id AND w.depth < 1000
                )
                SELECT EXISTS (SELECT 1 FROM walk WHERE parent_id = start_id) AS found
                """
            )
        )

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        row = await self._fetch_one(
            """
            INSERT INTO menus (parent_id, code, name, path, icon, description, permission_code, sort_order, is_active)
            VALUES (%(parent_id)s, %(code)s, %(name)s, %(path)s, %(icon)s, %(description)s,
                    %(permission_code)s, %(sort_order)s, %(is_active)s)
            RETURNING *
            """,
            data,
        )
        assert row is not None
        return row

    async def update(self, menu_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        return await self._update_returning(
            "menus", {"id": menu_id}, fields, allowed=_UPDATABLE, touch_updated_at=True
        )

    async def delete(self, menu_id: int) -> int:
        return await self._execute("DELETE FROM menus WHERE id = %(id)s", {"id": menu_id})
