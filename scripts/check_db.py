import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from src.core.database import engine

with engine.connect() as conn:
    rows = conn.execute(
        text(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('public', 'web_app')
              AND table_name IN ('users', 'config')
            ORDER BY 1, 2
            """
        )
    ).fetchall()
    print("Tables:", rows)
    print("search_path:", conn.execute(text("SHOW search_path")).scalar())
    for schema in ("public", "web_app"):
        try:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."users"')).scalar()
            print(f"{schema}.users count:", count)
        except Exception as exc:
            print(f"{schema}.users:", exc)
