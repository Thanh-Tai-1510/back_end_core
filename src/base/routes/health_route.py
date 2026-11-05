"""Liveness and readiness probes (for load balancers, Docker, Kubernetes)."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import check_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def liveness() -> dict[str, str]:
    """The process is up. Does not touch dependencies."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    """Ready to serve traffic: the database answers (when DB_ENABLED)."""
    checks: dict[str, object] = {}
    if settings.DB_ENABLED:
        db_ok = await check_connection()
        db_check: dict[str, object] = {"ok": db_ok}
        if not db_ok and (settings.EXPOSE_READINESS_ERRORS or not settings.is_production):
            db_check["error"] = getattr(request.app.state, "db_init_error", None)
        checks["database"] = db_check

    ready = all(check["ok"] for check in checks.values())  # type: ignore[index]
    return JSONResponse(status_code=200 if ready else 503, content={"ready": ready, "checks": checks})
