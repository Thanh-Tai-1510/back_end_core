from typing import Any

from base.requests.config_request import CreateConfigRequest, UpdateConfigRequest
from base.requests.pagination import PageParams
from base.responses.common import MessageResponse, Page
from base.responses.config_response import ConfigResponse
from base.services.config_service import ConfigService, is_sensitive_key, mask_value


def to_response(row: dict[str, Any]) -> ConfigResponse:
    # Secret values never leave the API: they are write-only.
    return ConfigResponse(
        key=row["key"],
        type=row["type"],
        value=mask_value(row["key"], row["value"]),
        is_secret=is_sensitive_key(row["key"]),
        created_at=row.get("created_at"),
    )


class ConfigController:
    async def page(
        self, params: PageParams, type_: str | None, search: str | None, service: ConfigService
    ) -> Page[ConfigResponse]:
        rows, total = await service.page(limit=params.limit, offset=params.offset, type_=type_, search=search)
        return Page.build([to_response(row) for row in rows], total, params)

    async def types(self, service: ConfigService) -> list[str]:
        return await service.list_types()

    async def get(self, key: str, service: ConfigService) -> ConfigResponse:
        return to_response(await service.get(key))

    async def create(self, request: CreateConfigRequest, service: ConfigService) -> ConfigResponse:
        return to_response(await service.create(request))

    async def update(self, key: str, request: UpdateConfigRequest, service: ConfigService) -> ConfigResponse:
        return to_response(await service.update(key, request))

    async def delete(self, key: str, service: ConfigService) -> None:
        await service.delete(key)

    async def refresh_cache(self, service: ConfigService) -> MessageResponse:
        count = await service.refresh_cache()
        return MessageResponse(message=f"Config cache reloaded ({count} keys)")
