"""Create the database and schema if missing, then run scripts/sql/*.sql in filename order.

Usage: python scripts/init_db.py
"""

from pathlib import Path

from psycopg import sql

from _db import connect, settings

SQL_DIR = Path(__file__).resolve().parent / "sql"


def ensure_database() -> None:
    with connect(dbname="postgres", autocommit=True, with_schema=False) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", [settings.PG_DATABASE]).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.PG_DATABASE)))
            print("Created database", settings.PG_DATABASE)


def ensure_schema_and_run_sql() -> None:
    files = sorted(SQL_DIR.glob("*.sql"))
    with connect(with_schema=False) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(settings.PG_SCHEMA)))
        conn.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(settings.PG_SCHEMA)))
        for path in files:
            print("Running", path.name)
            conn.execute(path.read_text(encoding="utf-8"))
        conn.commit()
    print(f"Schema {settings.PG_SCHEMA} ready ({len(files)} SQL file(s) applied)")


if __name__ == "__main__":
    ensure_database()
    ensure_schema_and_run_sql()
