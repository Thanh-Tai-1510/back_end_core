"""Sync psycopg connection for scripts, using the same settings as the app."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from core.config import settings  # noqa: E402


def connect(*, dbname: str | None = None, autocommit: bool = False, with_schema: bool = True) -> psycopg.Connection:
    conninfo = settings.pg_conninfo
    if dbname is not None:
        conninfo = conninfo.replace(f"dbname={settings.PG_DATABASE}", f"dbname={dbname}")
    options = f"-c search_path={settings.PG_SCHEMA},public" if with_schema else ""
    return psycopg.connect(conninfo, autocommit=autocommit, row_factory=dict_row, options=options)
