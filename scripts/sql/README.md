SQL files here are run by `python scripts/init_db.py` in filename order (`001_xxx.sql`, `002_xxx.sql`, ...).
Write them so they can run again safely (`CREATE TABLE IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, ...).
They run with `search_path` set to `PG_SCHEMA`.
