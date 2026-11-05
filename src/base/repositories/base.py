from collections.abc import Iterable, Mapping
from typing import Any

from psycopg import AsyncConnection, sql

Query = str | sql.Composable
Params = Mapping[str, Any] | None


class BaseRepository:
    """Holds a connection and async SQL helpers. Rows come back as dicts (dict_row).

    Write SQL with named placeholders: "SELECT * FROM items WHERE id = %(id)s".
    Never format values into the SQL string; use psycopg.sql for dynamic identifiers.
    """

    def __init__(self, db: AsyncConnection) -> None:
        self.db = db

    async def _fetch_one(self, query: Query, params: Params = None) -> dict[str, Any] | None:
        async with self.db.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchone()

    async def _fetch_all(self, query: Query, params: Params = None) -> list[dict[str, Any]]:
        async with self.db.cursor() as cur:
            await cur.execute(query, params)
            return list(await cur.fetchall())

    async def _fetch_scalar(self, query: Query, params: Params = None) -> Any:
        row = await self._fetch_one(query, params)
        if row is None:
            return None
        return next(iter(row.values()))

    async def _execute(self, query: Query, params: Params = None) -> int:
        """Run a write statement; returns the affected row count."""
        async with self.db.cursor() as cur:
            await cur.execute(query, params)
            return cur.rowcount or 0

    async def _fetch_page(
        self,
        query: str,
        params: Params = None,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Rows for one page plus the total row count of `query`.

        `query` must not have its own LIMIT/OFFSET; put ORDER BY in it for a stable order.
        """
        base_params = dict(params or {})
        total = await self._fetch_scalar(f"SELECT COUNT(*) AS total FROM ({query}) AS _page_src", base_params)
        rows = await self._fetch_all(
            f"{query} LIMIT %(_page_limit)s OFFSET %(_page_offset)s",
            {**base_params, "_page_limit": limit, "_page_offset": offset},
        )
        return rows, int(total or 0)

    async def _update_returning(
        self,
        table: str,
        where: Mapping[str, Any],
        fields: Mapping[str, Any],
        *,
        allowed: Iterable[str],
        touch_updated_at: bool = False,
    ) -> dict[str, Any] | None:
        """UPDATE table SET <fields> WHERE <where> RETURNING *.

        Only columns in `allowed` are written, so request data can be passed straight in.
        With nothing to set, returns the current row unchanged.
        """
        allowed_set = set(allowed)
        values = {col: val for col, val in fields.items() if col in allowed_set}
        where_sql = sql.SQL(" AND ").join(
            sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder(f"w_{col}")) for col in where
        )
        params = {f"w_{col}": val for col, val in where.items()}

        if not values:
            return await self._fetch_one(
                sql.SQL("SELECT * FROM {} WHERE {}").format(sql.Identifier(table), where_sql), params
            )

        assignments = [
            sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder(f"s_{col}")) for col in values
        ]
        if touch_updated_at:
            assignments.append(sql.SQL("updated_at = now()"))
        params.update({f"s_{col}": val for col, val in values.items()})
        query = sql.SQL("UPDATE {} SET {} WHERE {} RETURNING *").format(
            sql.Identifier(table), sql.SQL(", ").join(assignments), where_sql
        )
        return await self._fetch_one(query, params)
