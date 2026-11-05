import time
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from core.config import settings
from core.exceptions import TooManyRequestsError, error_body
from core.logging import Loggers, get_logger

logger = get_logger(Loggers.SECURITY)

_WINDOW_SEC = 60.0
_PRUNE_INTERVAL_SEC = 300.0


@dataclass(frozen=True)
class RateLimitRule:
    """Stricter limit for one path (exact match, trailing slash ignored)."""

    path: str
    per_minute: int
    methods: frozenset[str] = frozenset({"POST"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window limit per client IP, per process.

    Every request counts against RATE_LIMIT_PER_MINUTE; `rules` add tighter limits for
    sensitive paths (login, register, ...). Paths in `exempt_paths` are never limited.

    For multiple workers/instances, swap this for a shared store (e.g. Redis).
    Behind a reverse proxy, run uvicorn with FORWARDED_ALLOW_IPS set to the proxy's
    address so request.client is the real IP. X-Forwarded-For is never read here.
    """

    def __init__(
        self,
        app: ASGIApp,
        rules: tuple[RateLimitRule, ...] = (),
        exempt_paths: frozenset[str] = frozenset({"/health", "/health/ready"}),
    ) -> None:
        super().__init__(app)
        self._rules = {rule.path.rstrip("/") or "/": rule for rule in rules}
        self._exempt = exempt_paths
        self._hits: dict[str, list[float]] = {}
        self._last_prune = time.monotonic()

    def _prune(self, now: float) -> None:
        if now - self._last_prune < _PRUNE_INTERVAL_SEC:
            return
        cutoff = now - _WINDOW_SEC
        self._hits = {key: hits for key, hits in self._hits.items() if hits and hits[-1] > cutoff}
        self._last_prune = now

    def _allow(self, key: str, limit: int, now: float) -> bool:
        cutoff = now - _WINDOW_SEC
        hits = [t for t in self._hits.get(key, ()) if t > cutoff]
        allowed = len(hits) < limit
        if allowed:
            hits.append(now)
        self._hits[key] = hits
        return allowed

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path.rstrip("/") or "/"
        if not settings.RATE_LIMIT_ENABLED or path in self._exempt or request.method == "OPTIONS":
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        self._prune(now)

        checks = [(f"global:{client}", settings.RATE_LIMIT_PER_MINUTE)]
        rule = self._rules.get(path)
        if rule is not None and request.method in rule.methods:
            checks.append((f"{path}:{client}", rule.per_minute))

        for key, limit in checks:
            if not self._allow(key, limit, now):
                logger.warning("Rate limit exceeded: key=%s path=%s", key, request.url.path)
                err = TooManyRequestsError()
                return JSONResponse(
                    status_code=err.status_code,
                    content=error_body(err.code, err.message),
                    headers={"Retry-After": str(int(_WINDOW_SEC))},
                )

        return await call_next(request)
