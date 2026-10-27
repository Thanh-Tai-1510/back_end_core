from typing import Annotated

from fastapi import APIRouter, status

from src.base.controllers.deps import ConfigDep, DbSession, require_permission
from src.base.controllers.config_controller import ConfigController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from src.base.responses.config_response import ConfigResponse

router = APIRouter(prefix="/config", tags=["config"])
controller = ConfigController()


@router.get("", response_model=list[ConfigResponse])
def list_configs(
    db: DbSession,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_LIST)],
    reveal_sensitive: bool = False,
) -> list[ConfigResponse]:
    return controller.list_configs(db, current_user, reveal_sensitive)


@router.post("/cache/refresh", status_code=status.HTTP_204_NO_CONTENT)
def refresh_config_cache(
    config: ConfigDep,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_CACHE_REFRESH)],
) -> None:
    controller.refresh_config_cache(config, current_user)


@router.get("/{key}", response_model=ConfigResponse)
def get_config(
    key: str,
    db: DbSession,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_READ)],
    reveal_sensitive: bool = False,
) -> ConfigResponse:
    return controller.get_config(key, db, current_user, reveal_sensitive)


@router.post("", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    request: CreateConfigRequest,
    db: DbSession,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_CREATE)],
) -> ConfigResponse:
    return controller.create_config(request, db, current_user)


@router.put("/{key}", response_model=ConfigResponse)
def update_config(
    key: str,
    request: UpdateConfigRequest,
    db: DbSession,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_UPDATE)],
) -> ConfigResponse:
    return controller.update_config(key, request, db, current_user)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    key: str,
    db: DbSession,
    current_user: Annotated[User, require_permission(PermissionCode.CONFIG_DELETE)],
) -> None:
    controller.delete_config(key, db, current_user)
