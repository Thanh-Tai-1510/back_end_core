import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config.runtime import DEFAULT_RUNTIME_CONFIG, RuntimeConfig

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

_configured = False
_current_config = DEFAULT_RUNTIME_CONFIG


class Loggers:
    APP = "src"
    API = "src.base.controllers"
    AUTH = "src.base.controllers.auth_controller"
    DB = "src.core.database"
    SECURITY = "src.core.security"
    SERVICE = "src.base.services"


class ErrorOnlyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or Loggers.APP)


def _resolve_level(level_name: str) -> int:
    return getattr(logging, level_name.upper(), logging.INFO)


def _rotating_handler(
    log_dir: Path,
    filename: str,
    level: int,
    formatter: logging.Formatter,
    *,
    log_filter: logging.Filter | None = None,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        log_dir / filename,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    if log_filter is not None:
        handler.addFilter(log_filter)
    return handler


def setup_logging(config: RuntimeConfig | None = None) -> None:
    global _configured, _current_config
    runtime = config or DEFAULT_RUNTIME_CONFIG
    _current_config = runtime

    runtime.log_dir.mkdir(parents=True, exist_ok=True)
    level = _resolve_level(runtime.log_level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    app_handler = _rotating_handler(runtime.log_dir, "app.log", level, formatter)
    api_handler = _rotating_handler(runtime.log_dir, "api.log", level, formatter)
    auth_handler = _rotating_handler(runtime.log_dir, "auth.log", level, formatter)
    db_handler = _rotating_handler(runtime.log_dir, "db.log", level, formatter)
    error_handler = _rotating_handler(
        runtime.log_dir,
        "error.log",
        logging.ERROR,
        formatter,
        log_filter=ErrorOnlyFilter(),
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(app_handler)
    root.addHandler(error_handler)

    for logger_name, handler in (
        (Loggers.API, api_handler),
        (Loggers.AUTH, auth_handler),
        (Loggers.DB, db_handler),
    ):
        module_logger = logging.getLogger(logger_name)
        module_logger.handlers.clear()
        module_logger.addHandler(handler)
        module_logger.setLevel(level)
        module_logger.propagate = True

    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)

    sql_level = logging.INFO if runtime.log_sql else logging.WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(sql_level)

    _configured = True


def apply_logging_config(config: RuntimeConfig) -> None:
    setup_logging(config)
