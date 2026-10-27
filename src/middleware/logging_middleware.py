import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import Loggers, get_logger

logger = get_logger(Loggers.API)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.perf_counter()
        client = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s from %s failed after %.2fms",
                request.method,
                request.url.path,
                client,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            "%s %s %s from %s - %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            client,
            duration_ms,
        )
        return response
