"""Async PostgreSQL pool (psycopg 3) and FastAPI dependencies for borrowing connections."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.asyncio_platform import configure_asyncio_for_psycopg

configure_asyncio_for_psycopg()

from fastapi import Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool, PoolTimeout

from core.config import settings
from core.exceptions import ServiceUnavailableError
from core.logging import Loggers, get_logger

logger = get_logger(Loggers.DB)

_pool: AsyncConnectionPool | None = None

POOL_OPEN_TIMEOUT_SEC = 15.0
POOL_ACQUIRE_TIMEOUT_SEC = 10.0
PG_CONNECT_TIMEOUT_SEC = 10


def _target() -> str:
    return f"{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE} (schema={settings.PG_SCHEMA})"


def _conninfo_with_timeout() -> str:
    base = settings.pg_conninfo.strip()
    if "connect_timeout=" in base:
        return base
    return f"{base} connect_timeout={PG_CONNECT_TIMEOUT_SEC}"


def _on_reconnect_failed(pool: AsyncConnectionPool) -> None:
    logger.error("PostgreSQL pool reconnect failed for %s. Check PG_* settings.", _target())


async def _ping(pool: AsyncConnectionPool) -> bool:
    async with pool.connection(timeout=POOL_ACQUIRE_TIMEOUT_SEC) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1 AS ok")
            row = await cur.fetchone()
    return row is not None and row.get("ok") == 1


async def init_db_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is not None:
        return _pool
    pool = AsyncConnectionPool(
        conninfo=_conninfo_with_timeout(),
        kwargs={
            "row_factory": dict_row,
            "options": f"-c search_path={settings.PG_SCHEMA},public",
        },
        min_size=settings.PG_POOL_MIN_SIZE,
        max_size=settings.PG_POOL_MAX_SIZE,
        open=False,
        timeout=POOL_ACQUIRE_TIMEOUT_SEC,
        reconnect_failed=_on_reconnect_failed,
    )
    try:
        await pool.open(wait=True, timeout=POOL_OPEN_TIMEOUT_SEC)
        if not await _ping(pool):
            raise RuntimeError("health query returned no row")
    except Exception as exc:
        await pool.close()
        message = f"Cannot connect to PostgreSQL at {_target()}: {exc}"
        logger.error(message)
        raise RuntimeError(message) from exc
    _pool = pool
    logger.info("PostgreSQL pool opened for %s", _target())
    return pool


async def close_db_pool() -> None:
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None
    logger.info("PostgreSQL pool closed")


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


async def check_connection() -> bool:
    if _pool is None:
        return False
    try:
        return await _ping(_pool)
    except Exception:
        logger.exception("Database health check failed")
        return False


def request_pool(request: Request) -> AsyncConnectionPool:
    pool: AsyncConnectionPool | None = getattr(request.app.state, "db_pool", None)
    if pool is None:
        logger.error("Database pool is not available: %s", getattr(request.app.state, "db_init_error", None))
        raise ServiceUnavailableError("Database is not available")
    return pool


@asynccontextmanager
async def pool_connection(pool: AsyncConnectionPool) -> AsyncIterator[AsyncConnection]:
    """Borrow a connection; commit on success, roll back on error, then return it to the pool.

    Use this for short units of work instead of holding a connection across slow I/O.
    """
    try:
        async with pool.connection(timeout=POOL_ACQUIRE_TIMEOUT_SEC) as conn:
            yield conn
    except PoolTimeout as exc:
        logger.error(
            "Pool timeout after %ss acquiring a connection to %s. Pool exhausted or Postgres unreachable.",
            POOL_ACQUIRE_TIMEOUT_SEC,
            _target(),
        )
        raise ServiceUnavailableError("Database is busy, please retry") from exc


async def get_db(request: Request) -> AsyncIterator[AsyncConnection]:
    """One connection for the whole request. Endpoints that wait on slow upstream calls
    should borrow per step with pool_connection instead."""
    async with pool_connection(request_pool(request)) as conn:
        yield conn


@asynccontextmanager
async def transaction(conn: AsyncConnection) -> AsyncIterator[AsyncConnection]:
    async with conn.transaction():
        yield conn
