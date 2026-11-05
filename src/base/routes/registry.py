"""Single place where feature routers are plugged into the app.

To add a feature: create base/routes/<feature>_route.py with `router = APIRouter(prefix=..., tags=[...])`,
import it here and add it to API_ROUTERS (served under settings.API_PREFIX) or ROOT_ROUTERS (no prefix).
"""

from fastapi import APIRouter

from base.routes import config_route, health_route, menu_route, permission_route

# Served under settings.API_PREFIX (e.g. /api/v1/items).
API_ROUTERS: tuple[APIRouter, ...] = (
    config_route.router,
    permission_route.router,
    menu_route.router,
)

# Served without prefix.
ROOT_ROUTERS: tuple[APIRouter, ...] = (health_route.router,)


def _combine(routers: tuple[APIRouter, ...]) -> APIRouter:
    combined = APIRouter()
    for router in routers:
        combined.include_router(router)
    return combined


def build_api_router() -> APIRouter:
    return _combine(API_ROUTERS)


def build_root_router() -> APIRouter:
    return _combine(ROOT_ROUTERS)
