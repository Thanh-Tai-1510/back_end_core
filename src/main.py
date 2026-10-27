from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.base.routes.registry import build_v1_router
from src.core.logging import Loggers, apply_logging_config, get_logger, setup_logging
from src.core.config.runtime import DEFAULT_RUNTIME_CONFIG, get_runtime_config, init_runtime_config
from src.middleware.logging_middleware import RequestLoggingMiddleware

setup_logging(DEFAULT_RUNTIME_CONFIG)
runtime_config = init_runtime_config()
apply_logging_config(runtime_config)

logger = get_logger(Loggers.APP)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_runtime_config()
    logger.info("Starting %s", config.app_name)
    logger.info("Log directory: %s", config.log_dir)
    yield
    logger.info("Shutting down %s", config.app_name)


app = FastAPI(title=runtime_config.app_name, lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(build_v1_router(), prefix=runtime_config.api_v1_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
