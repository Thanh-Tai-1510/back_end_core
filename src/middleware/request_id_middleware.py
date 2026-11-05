"""Give every request an id (from X-Request-ID or a new one) and echo it on the response."""

import re
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADER = "X-Request-ID"
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class RequestIdMiddleware:
    """Plain ASGI so streaming responses are not buffered. The id is in request.state.request_id."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = ""
        for key, value in scope.get("headers") or ():
            if key == b"x-request-id":
                incoming = value.decode("latin-1").strip()
                break
        # Only trust a client-sent id that is short and log-safe.
        request_id = incoming if _VALID_ID.match(incoming) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).setdefault(HEADER, request_id)
            await send(message)

        await self.app(scope, receive, send_with_id)
