import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.logging import Loggers, get_logger

logger = get_logger(Loggers.ACCESS)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        client = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "-")

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "[%s] %s %s from %s failed after %.2fms",
                request_id,
                request.method,
                request.url.path,
                client,
                (time.perf_counter() - start) * 1000,
            )
            raise

        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            "[%s] %s %s %s from %s - %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            client,
            (time.perf_counter() - start) * 1000,
        )
        return response
