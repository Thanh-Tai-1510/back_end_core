-- Schema: web_app
-- Bảng roles, users, menus

CREATE SCHEMA IF NOT EXISTS web_app;

-- ---------------------------------------------------------------------------
-- Roles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.roles (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    is_system       BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP,
    CONSTRAINT uq_roles_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_roles_code ON web_app.roles (code);
CREATE INDEX IF NOT EXISTS ix_roles_is_active ON web_app.roles (is_active);
CREATE INDEX IF NOT EXISTS ix_roles_deleted_at ON web_app.roles (deleted_at);

INSERT INTO web_app.roles (code, name, description, is_system, sort_order)
VALUES
    ('user', 'Người dùng', 'Quyền truy cập cơ bản', FALSE, 1),
    ('moderator', 'Điều hành', 'Quản lý nội dung', TRUE, 2),
    ('admin', 'Quản trị viên', 'Quản trị hệ thống', TRUE, 3),
    ('system', 'Hệ thống', 'Tài khoản nội bộ', TRUE, 99)
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Users (role_id thay cho cột role cũ)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.users (
    id                  SERIAL PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,

    email               VARCHAR(255) NOT NULL UNIQUE,
    username            VARCHAR(100) NOT NULL UNIQUE,
    hashed_password     VARCHAR(255) NOT NULL,

    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    display_name        VARCHAR(150),
    phone               VARCHAR(20) UNIQUE,
    avatar_url          TEXT,
    bio                 TEXT,
    date_of_birth       DATE,
    gender              VARCHAR(20) NOT NULL DEFAULT 'unspecified',

    role_id             INTEGER NOT NULL REFERENCES web_app.roles (id) ON DELETE RESTRICT,
    locale              VARCHAR(10) NOT NULL DEFAULT 'vi',
    timezone            VARCHAR(64) NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',

    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser        BOOLEAN NOT NULL DEFAULT FALSE,
    is_staff            BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at   TIMESTAMP,

    must_change_password    BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_attempts   INTEGER NOT NULL DEFAULT 0,
    locked_until            TIMESTAMP,
    password_changed_at     TIMESTAMP,

    last_login_at       TIMESTAMP,
    last_login_ip       VARCHAR(45),

    auth_provider       VARCHAR(20) NOT NULL DEFAULT 'local',
    auth_provider_id    VARCHAR(255),

    extra_data          JSONB,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMP,

    created_by_id       INTEGER REFERENCES web_app.users (id) ON DELETE SET NULL,
    updated_by_id       INTEGER REFERENCES web_app.users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_users_email ON web_app.users (email);
CREATE INDEX IF NOT EXISTS ix_users_username ON web_app.users (username);
CREATE INDEX IF NOT EXISTS ix_users_public_id ON web_app.users (public_id);
CREATE INDEX IF NOT EXISTS ix_users_role_id ON web_app.users (role_id);
CREATE INDEX IF NOT EXISTS ix_users_is_active ON web_app.users (is_active);
CREATE INDEX IF NOT EXISTS ix_users_deleted_at ON web_app.users (deleted_at);

-- ---------------------------------------------------------------------------
-- Menus
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.menus (
    id              SERIAL PRIMARY KEY,
    parent_id       INTEGER REFERENCES web_app.menus (id) ON DELETE CASCADE,
    code            VARCHAR(100) NOT NULL,
    name            VARCHAR(150) NOT NULL,
    path            VARCHAR(255),
    icon            VARCHAR(100),
    description     TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    allowed_roles   JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP,
    CONSTRAINT uq_menus_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_menus_parent_id ON web_app.menus (parent_id);
CREATE INDEX IF NOT EXISTS ix_menus_code ON web_app.menus (code);
CREATE INDEX IF NOT EXISTS ix_menus_is_active ON web_app.menus (is_active);
CREATE INDEX IF NOT EXISTS ix_menus_deleted_at ON web_app.menus (deleted_at);

COMMENT ON TABLE web_app.menus IS 'Menu điều hướng ứng dụng';
COMMENT ON COLUMN web_app.menus.allowed_roles IS 'Danh sách role code, ví dụ: ["admin","user"]. NULL = tất cả role';

INSERT INTO web_app.menus (code, name, path, icon, sort_order, allowed_roles)
VALUES
    ('dashboard', 'Tổng quan', '/dashboard', 'LayoutDashboard', 1, NULL),
    ('reports', 'Báo cáo', NULL, 'FileText', 2, '["admin","moderator","user"]'),
    ('reports.financial', 'Báo cáo tài chính', '/reports/financial', 'PieChart', 1, NULL),
    ('reports.balance', 'Bảng cân đối', '/reports/balance-sheet', 'Scale', 2, NULL),
    ('settings', 'Cài đặt', '/settings', 'Settings', 99, '["admin"]')
ON CONFLICT (code) DO NOTHING;

UPDATE web_app.menus AS child
SET parent_id = parent.id
FROM web_app.menus AS parent
WHERE child.code = 'reports.financial' AND parent.code = 'reports';

UPDATE web_app.menus AS child
SET parent_id = parent.id
FROM web_app.menus AS parent
WHERE child.code = 'reports.balance' AND parent.code = 'reports';

-- ---------------------------------------------------------------------------
-- Migration: nếu bảng users cũ còn cột role (VARCHAR), chạy block dưới
-- ---------------------------------------------------------------------------
-- ALTER TABLE web_app.users ADD COLUMN IF NOT EXISTS role_id INTEGER;
-- UPDATE web_app.users AS u
-- SET role_id = r.id
-- FROM web_app.roles AS r
-- WHERE u.role_id IS NULL AND r.code = u.role;
-- ALTER TABLE web_app.users ALTER COLUMN role_id SET NOT NULL;
-- ALTER TABLE web_app.users DROP COLUMN IF EXISTS role;
-- DROP INDEX IF EXISTS web_app.ix_users_role;
-- CREATE INDEX IF NOT EXISTS ix_users_role_id ON web_app.users (role_id);
