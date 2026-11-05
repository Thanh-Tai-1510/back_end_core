-- Navigation menu tree. permission_code (optional) = permission needed to see the item.
CREATE TABLE IF NOT EXISTS menus (
    id               SERIAL PRIMARY KEY,
    parent_id        INTEGER REFERENCES menus (id) ON DELETE CASCADE,
    code             VARCHAR(100) NOT NULL UNIQUE,
    name             VARCHAR(150) NOT NULL,
    path             VARCHAR(255),
    icon             VARCHAR(100),
    description      TEXT,
    permission_code  VARCHAR(100) REFERENCES permissions (code) ON UPDATE CASCADE ON DELETE SET NULL,
    sort_order       INTEGER   NOT NULL DEFAULT 0,
    is_active        BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT now(),
    updated_at       TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT ck_menus_not_own_parent CHECK (parent_id IS NULL OR parent_id <> id)
);
CREATE INDEX IF NOT EXISTS ix_menus_parent_id ON menus (parent_id);
