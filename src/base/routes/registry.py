from dataclasses import dataclass

from fastapi import APIRouter

from src.base.routes import (
    auth_route,
    chat_route,
    config_route,
    menu_route,
    permission_route,
    role_route,
    user_route,
)


@dataclass(frozen=True)
class RouteEntry:
    router: APIRouter
    name: str
    description: str = ""


V1_ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry(auth_route.router, "auth", "Đăng ký, đăng nhập, thông tin phiên"),
    RouteEntry(user_route.router, "users", "Hồ sơ người dùng"),
    RouteEntry(chat_route.router, "chat", "Chat AI qua n8n webhook"),
    RouteEntry(config_route.router, "config", "Cấu hình hệ thống"),
    RouteEntry(role_route.router, "roles", "Quản lý role"),
    RouteEntry(menu_route.router, "menus", "Quản lý menu"),
    RouteEntry(permission_route.router, "permissions", "Quản lý permission"),
)


def build_v1_router() -> APIRouter:
    api_router = APIRouter()
    for entry in V1_ROUTES:
        api_router.include_router(entry.router)
    return api_router


def list_v1_routes() -> list[dict[str, str]]:
    return [
        {"name": entry.name, "description": entry.description, "prefix": entry.router.prefix}
        for entry in V1_ROUTES
    ]
