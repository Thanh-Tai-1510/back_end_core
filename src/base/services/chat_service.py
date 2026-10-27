import json
from typing import Any

import httpx

from src.base.models.user import User
from src.base.services.config_service import ConfigService
from src.core.logging import Loggers, get_logger

logger = get_logger(Loggers.SERVICE)

WEBHOOK_CONFIG_KEY = "Webhook"
WEBHOOK_TIMEOUT_SECONDS = 120.0


class ChatService:
    def __init__(self, config: ConfigService) -> None:
        self.config = config

    def send_message(
        self,
        user: User,
        message: str,
        session_id: str | None = None,
    ) -> tuple[str, str | None, Any]:
        webhook_url = self._get_webhook_url()
        resolved_session_id = session_id or str(user.public_id)

        payload = {
            "message": message,
            "chatInput": message,
            "sessionId": resolved_session_id,
            "userId": user.id,
            "username": user.username,
        }

        logger.info(
            "Sending chat message to n8n webhook: user_id=%s session_id=%s",
            user.id,
            resolved_session_id,
        )

        try:
            with httpx.Client(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
                response = client.post(webhook_url, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ValueError("Webhook chat phản hồi quá chậm, vui lòng thử lại") from exc
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Webhook chat trả về lỗi HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError("Không thể kết nối webhook chat") from exc

        raw = self._parse_response_body(response)
        reply = self._extract_reply(raw)
        if reply is None:
            reply = json.dumps(raw, ensure_ascii=False) if raw is not None else ""

        return reply, resolved_session_id, raw

    def _get_webhook_url(self) -> str:
        row = self.config.get_row(WEBHOOK_CONFIG_KEY)
        if row is None or not row.value or not row.value.strip():
            raise ValueError(f"Chưa cấu hình webhook chat (key: {WEBHOOK_CONFIG_KEY})")

        if row.type and row.type.lower() != "n8n":
            logger.warning(
                "Config %s type=%s, expected n8n",
                WEBHOOK_CONFIG_KEY,
                row.type,
            )

        return row.value.strip()

    @staticmethod
    def _parse_response_body(response: httpx.Response) -> Any:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()

        text = response.text.strip()
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    @staticmethod
    def _extract_reply(data: Any) -> str | None:
        if data is None:
            return None
        if isinstance(data, str):
            return data.strip() or None
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if "json" in first:
                    return ChatService._extract_reply(first["json"])
                return ChatService._extract_reply(first)
            return ChatService._extract_reply(first)
        if isinstance(data, dict):
            for key in ("output", "text", "response", "message", "reply", "answer", "content"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            for nested_key in ("json", "data", "result"):
                if nested_key in data:
                    nested = ChatService._extract_reply(data[nested_key])
                    if nested:
                        return nested
        return None
