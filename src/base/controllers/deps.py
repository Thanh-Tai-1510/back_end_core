"""Shared FastAPI dependencies. Add a `get_<feature>_service` + `<Feature>ServiceDep` per feature."""

import hmac
from typing import Annotated

import httpx
from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader
from psycopg import AsyncConnection

from base.requests.pagination import PageParams
from base.services.config_service import ConfigService
from base.services.menu_service import MenuService
from base.services.permission_service import PermissionService
from core.config import settings
from core.database import get_db
from core.exceptions import ServiceUnavailableError, UnauthorizedError
from core.logging import Loggers, get_logger

logger = get_logger(Loggers.SECURITY)

DbConn = Annotated[AsyncConnection, Depends(get_db)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    """App-wide client (connection pooling); created and closed in the app lifespan."""
    return request.app.state.http_client


HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


RequestId = Annotated[str, Depends(get_request_id)]

PageParamsDep = Annotated[PageParams, Depends()]


# --- Admin guard -------------------------------------------------------------------------
# Protects admin endpoints with a shared key until the project adds real auth; then swap
# require_admin for a permission check on the current user.

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="Value of ADMIN_API_KEY",
)


async def require_admin(request: Request, api_key: Annotated[str | None, Security(_api_key_header)]) -> None:
    expected = settings.ADMIN_API_KEY
    if not expected:
        if settings.is_production:
            raise ServiceUnavailableError("ADMIN_API_KEY is not configured")
        return  # Development without a key: open, for convenience.
    if not api_key or not hmac.compare_digest(api_key.encode("utf-8"), expected.encode("utf-8")):
        client = request.client.host if request.client else "unknown"
        logger.warning("Admin key rejected: %s %s from %s", request.method, request.url.path, client)
        raise UnauthorizedError("Invalid or missing X-API-Key")


AdminGuard = Depends(require_admin)


# --- Services ----------------------------------------------------------------------------


def get_config_service(db: DbConn) -> ConfigService:
    return ConfigService(db)


def get_permission_service(db: DbConn) -> PermissionService:
    return PermissionService(db)


def get_menu_service(db: DbConn) -> MenuService:
    return MenuService(db)


ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]
PermissionServiceDep = Annotated[PermissionService, Depends(get_permission_service)]
MenuServiceDep = Annotated[MenuService, Depends(get_menu_service)]
