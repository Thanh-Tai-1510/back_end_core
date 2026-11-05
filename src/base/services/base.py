from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection

from core.database import transaction


class BaseService:
    """Holds the request's connection. Subclasses build their repositories from self.db.

    get_db commits when the request succeeds and rolls back on error. Use
    `async with self.transaction():` to group writes that must succeed or fail together
    inside a single request.
    """

    def __init__(self, db: AsyncConnection) -> None:
        self.db = db

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        async with transaction(self.db) as conn:
            yield conn
