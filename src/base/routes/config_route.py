from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from base.controllers.config_controller import ConfigController
from base.controllers.deps import AdminGuard, ConfigServiceDep, PageParamsDep
from base.requests.config_request import CONFIG_KEY_PATTERN, CreateConfigRequest, UpdateConfigRequest
from base.responses.common import MessageResponse, Page
from base.responses.config_response import ConfigResponse

# All config endpoints are admin-only: the values drive app behaviour.
router = APIRouter(prefix="/config", tags=["config"], dependencies=[AdminGuard])
controller = ConfigController()

ConfigKey = Annotated[str, Path(pattern=CONFIG_KEY_PATTERN)]


@router.get("", response_model=Page[ConfigResponse])
async def list_config(
    params: PageParamsDep,
    service: ConfigServiceDep,
    type: Annotated[str | None, Query(description="Filter by group")] = None,
    q: Annotated[str | None, Query(max_length=100, description="Search in key")] = None,
) -> Page[ConfigResponse]:
    return await controller.page(params, type, q, service)


@router.get("/types", response_model=list[str])
async def list_config_types(service: ConfigServiceDep) -> list[str]:
    return await controller.types(service)


@router.post("/cache/refresh", response_model=MessageResponse)
async def refresh_config_cache(service: ConfigServiceDep) -> MessageResponse:
    return await controller.refresh_cache(service)


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(key: ConfigKey, service: ConfigServiceDep) -> ConfigResponse:
    return await controller.get(key, service)


@router.post("", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(request: CreateConfigRequest, service: ConfigServiceDep) -> ConfigResponse:
    return await controller.create(request, service)


@router.patch("/{key}", response_model=ConfigResponse)
async def update_config(key: ConfigKey, request: UpdateConfigRequest, service: ConfigServiceDep) -> ConfigResponse:
    return await controller.update(key, request, service)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(key: ConfigKey, service: ConfigServiceDep) -> None:
    await controller.delete(key, service)
