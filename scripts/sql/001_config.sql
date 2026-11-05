-- Runtime key/value config. `type` is a group name (app, auth, mail, ...).
CREATE TABLE IF NOT EXISTS config (
    key         TEXT PRIMARY KEY,
    type        TEXT,
    value       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_config_type ON config (type);
