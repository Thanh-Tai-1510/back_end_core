"""Security headers on every response.

Plain ASGI (not BaseHTTPMiddleware) so streaming responses (SSE, file downloads) are not buffered.
"""

from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.config import settings as app_settings

_BASE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Swagger/ReDoc load JS and CSS from a CDN, so they get no CSP. They are off in production.
_CSP_EXEMPT_PATHS: frozenset[str] = frozenset({"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"})


def _is_secure_request(scope: Scope) -> bool:
    """Direct https, or a proxy that terminated TLS and set X-Forwarded-Proto."""
    if scope.get("scheme") == "https":
        return True
    for key, value in scope.get("headers") or ():
        if key == b"x-forwarded-proto":
            return value.decode("latin-1").split(",")[0].strip().lower() == "https"
    return False


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        settings = app_settings
        if scope["type"] != "http" or not settings.SECURITY_HEADERS_ENABLED:
            await self.app(scope, receive, send)
            return

        csp = settings.SECURITY_CSP.strip() if scope.get("path", "") not in _CSP_EXEMPT_PATHS else ""
        # HSTS only over https: sending it over http does nothing and can lock a dev domain.
        hsts_max_age = settings.SECURITY_HSTS_MAX_AGE if _is_secure_request(scope) else 0

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in _BASE_HEADERS.items():
                    headers.setdefault(name, value)
                if csp:
                    headers.setdefault("Content-Security-Policy", csp)
                if hsts_max_age > 0:
                    headers.setdefault("Strict-Transport-Security", f"max-age={hsts_max_age}; includeSubDomains")
            await send(message)

        await self.app(scope, receive, send_with_headers)
