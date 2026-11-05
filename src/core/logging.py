import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5


class Loggers:
    """Logger names. Child loggers (e.g. "app.service.orders") inherit the parent's handlers."""

    APP = "app"
    ACCESS = "app.access"
    DB = "app.db"
    SECURITY = "app.security"
    SERVICE = "app.service"


# Loggers that also get their own file, besides app.log and error.log.
_DEDICATED_FILES: dict[str, str] = {
    Loggers.ACCESS: "access.log",
    Loggers.DB: "db.log",
    Loggers.SECURITY: "security.log",
}


class _ErrorOnlyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or Loggers.APP)


def _rotating_handler(path: Path, level: int, formatter: logging.Formatter) -> RotatingFileHandler:
    handler = RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def setup_logging(level_name: str = "INFO", log_dir: Path | None = None) -> None:
    """Console always; rotating files under log_dir when given. Safe to call more than once."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        root.addHandler(_rotating_handler(log_dir / "app.log", level, formatter))
        error_handler = _rotating_handler(log_dir / "error.log", logging.ERROR, formatter)
        error_handler.addFilter(_ErrorOnlyFilter())
        root.addHandler(error_handler)

    for name, filename in _DEDICATED_FILES.items():
        named = logging.getLogger(name)
        named.handlers.clear()
        named.setLevel(level)
        named.propagate = True
        if log_dir is not None:
            named.addHandler(_rotating_handler(log_dir / filename, level, formatter))

    for noisy in ("watchfiles", "watchfiles.main", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).setLevel(level)
