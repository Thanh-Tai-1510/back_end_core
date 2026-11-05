"""Check the database connection and list tables in PG_SCHEMA.  Usage: python scripts/check_db.py"""

from _db import connect, settings

with connect(autocommit=True) as conn:
    version = conn.execute("SELECT version() AS v").fetchone()["v"]
    print("Connected:", f"{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}")
    print("Server:", version)
    print("search_path:", conn.execute("SHOW search_path").fetchone()["search_path"])
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY 1",
        [settings.PG_SCHEMA],
    ).fetchall()
    print(f"Tables in {settings.PG_SCHEMA}:", [r["table_name"] for r in rows] or "(none)")
