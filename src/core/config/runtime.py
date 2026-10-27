from dataclasses import dataclass
from pathlib import Path

from src.core.config.env import PROJECT_ROOT

DEFAULT_APP_NAME = "Financial Statement API"
DEFAULT_API_V1_PREFIX = "/api/v1"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_SQL = False
DEFAULT_LOG_DIR = PROJECT_ROOT / "app" / "logs"


@dataclass(frozen=True)
class RuntimeConfig:
    app_name: str
    api_v1_prefix: str
    log_level: str
    log_sql: bool
    log_dir: Path


DEFAULT_RUNTIME_CONFIG = RuntimeConfig(
    app_name=DEFAULT_APP_NAME,
    api_v1_prefix=DEFAULT_API_V1_PREFIX,
    log_level=DEFAULT_LOG_LEVEL,
    log_sql=DEFAULT_LOG_SQL,
    log_dir=DEFAULT_LOG_DIR,
)

_runtime_config: RuntimeConfig | None = None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_log_dir(value: str | None) -> Path:
    if not value:
        return DEFAULT_LOG_DIR
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def load_runtime_config() -> RuntimeConfig:
    from src.core.database import SessionLocal
    from src.core.logging import Loggers, get_logger
    from src.base.services.config_service import ConfigService

    logger = get_logger(Loggers.APP)
    db = SessionLocal()
    try:
        service = ConfigService(db)
        runtime = RuntimeConfig(
            app_name=service.get("app_name", DEFAULT_APP_NAME) or DEFAULT_APP_NAME,
            api_v1_prefix=service.get("api_v1_prefix", DEFAULT_API_V1_PREFIX)
            or DEFAULT_API_V1_PREFIX,
            log_level=service.get("log_level", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL,
            log_sql=_parse_bool(service.get("log_sql"), DEFAULT_LOG_SQL),
            log_dir=_resolve_log_dir(service.get("log_dir")),
        )
        logger.info("Runtime config loaded from database")
        return runtime
    except Exception:
        logger.warning("Failed to load runtime config from database, using defaults")
        return DEFAULT_RUNTIME_CONFIG
    finally:
        db.close()


def init_runtime_config() -> RuntimeConfig:
    global _runtime_config
    _runtime_config = load_runtime_config()
    return _runtime_config


def get_runtime_config() -> RuntimeConfig:
    if _runtime_config is None:
        return DEFAULT_RUNTIME_CONFIG
    return _runtime_config
