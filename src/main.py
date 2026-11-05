"""FastAPI entrypoint. Run with `uvicorn src.main:app` (repo root) or `python -m src.main`."""

import contextlib
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
for _path in (_SRC_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from core.asyncio_platform import configure_asyncio_for_psycopg

configure_asyncio_for_psycopg()

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from base.routes import build_api_router, build_root_router
from core.config import settings
from core.database import close_db_pool, init_db_pool
from core.exceptions import register_exception_handlers
from core.logging import get_logger, setup_logging
from middleware import (
    RateLimitMiddleware,
    RateLimitRule,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

logger = get_logger()

# Tighter per-IP limits for sensitive endpoints, e.g.
#   RateLimitRule(f"{settings.API_PREFIX}/auth/login", per_minute=10),
RATE_LIMIT_RULES: tuple[RateLimitRule, ...] = ()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.APP_ENV)
    app.state.db_pool = None
    app.state.db_init_error = None

    async with contextlib.AsyncExitStack() as stack:
        app.state.http_client = await stack.enter_async_context(
            httpx.AsyncClient(timeout=settings.HTTP_CLIENT_TIMEOUT)
        )

        if settings.DB_ENABLED:
            try:
                app.state.db_pool = await init_db_pool()
                stack.push_async_callback(close_db_pool)
            except Exception as exc:
                # Keep serving: /health/ready reports 503 until the database is fixed.
                app.state.db_init_error = str(exc)
                logger.exception("Database pool init failed")

        yield

    logger.info("Stopped %s", settings.APP_NAME)


def create_app() -> FastAPI:
    setup_logging(settings.LOG_LEVEL, settings.LOG_DIR if settings.LOG_TO_FILE else None)
    settings.validate_for_startup()

    # The docs publish the whole API surface, so they are off in production unless asked for.
    docs_kwargs = {} if settings.api_docs_enabled else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan, **docs_kwargs)

    register_exception_handlers(app)

    # Middleware added later wraps the ones added earlier (last = outermost).
    cors_origins, cors_credentials = settings.resolved_cors()
    app.add_middleware(RateLimitMiddleware, rules=RATE_LIMIT_RULES)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    app.include_router(build_root_router())
    app.include_router(build_api_router(), prefix=settings.API_PREFIX)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        reload_dirs=[str(_SRC_DIR)] if settings.RELOAD else None,
        reload_excludes=["**/__pycache__/**", "**/*.pyc", "**/app/logs/**", "**/.env"] if settings.RELOAD else None,
        # psycopg async on Windows needs a selector loop (see core/asyncio_platform.py).
        loop="core.asyncio_platform:selector_loop_factory" if sys.platform == "win32" else "auto",
    )


if __name__ == "__main__":
    main()
