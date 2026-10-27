from fastapi import HTTPException, status

from src.base.controllers.deps import ConfigDep, DbSession
from src.core.logging import Loggers, get_logger
from src.base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from src.base.responses.config_response import ConfigResponse
from src.base.services.config_service import ConfigService

logger = get_logger(Loggers.API)

PROTECTED_KEYS = frozenset({"jwt_secret_key", "jwt_algorithm", "jwt_expire_minutes"})


class ConfigController:
    def list_configs(
        self,
        db: DbSession,
        current_user,
        reveal_sensitive: bool = False,
    ) -> list[ConfigResponse]:
        rows = ConfigService(db).list_all()
        can_reveal = reveal_sensitive and current_user.is_superuser
        return [ConfigResponse.from_model(row, reveal_sensitive=can_reveal) for row in rows]

    def refresh_config_cache(self, config: ConfigDep, current_user) -> None:
        config.refresh()
        logger.info("Config cache refreshed by user id=%s", current_user.id)

    def get_config(
        self,
        key: str,
        db: DbSession,
        current_user,
        reveal_sensitive: bool = False,
    ) -> ConfigResponse:
        row = ConfigService(db).get_row(key)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
        can_reveal = reveal_sensitive and current_user.is_superuser
        return ConfigResponse.from_model(row, reveal_sensitive=can_reveal)

    def create_config(
        self,
        request: CreateConfigRequest,
        db: DbSession,
        current_user,
    ) -> ConfigResponse:
        service = ConfigService(db)
        try:
            row = service.create(request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Config created by user id=%s key=%s", current_user.id, request.key)
        return ConfigResponse.from_model(row, reveal_sensitive=current_user.is_superuser)

    def update_config(
        self,
        key: str,
        request: UpdateConfigRequest,
        db: DbSession,
        current_user,
    ) -> ConfigResponse:
        if key in PROTECTED_KEYS and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superuser can modify auth config keys",
            )

        service = ConfigService(db)
        try:
            row = service.update(key, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        logger.info("Config updated by user id=%s key=%s", current_user.id, key)
        return ConfigResponse.from_model(row, reveal_sensitive=current_user.is_superuser)

    def delete_config(self, key: str, db: DbSession, current_user) -> None:
        if key in PROTECTED_KEYS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete protected auth config keys",
            )

        service = ConfigService(db)
        try:
            service.delete(key)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        logger.info("Config deleted by user id=%s key=%s", current_user.id, key)
