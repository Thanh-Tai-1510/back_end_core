-- Permission catalogue. code = "module:action", e.g. "orders:read", "users:me:update".
CREATE TABLE IF NOT EXISTS permissions (
    id           SERIAL PRIMARY KEY,
    code         VARCHAR(100) NOT NULL UNIQUE,
    name         VARCHAR(150) NOT NULL,
    module       VARCHAR(50)  NOT NULL,
    action       VARCHAR(50)  NOT NULL,
    description  TEXT,
    is_active    BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_permissions_module ON permissions (module);
