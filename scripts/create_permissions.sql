-- Schema: web_app
-- Bảng quản lý permission theo role + override riêng từng user

CREATE SCHEMA IF NOT EXISTS web_app;

-- ---------------------------------------------------------------------------
-- Permissions (danh mục quyền API action)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.permissions (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(100) NOT NULL,
    name            VARCHAR(150) NOT NULL,
    module          VARCHAR(50) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_permissions_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_permissions_code ON web_app.permissions (code);
CREATE INDEX IF NOT EXISTS ix_permissions_module ON web_app.permissions (module);
CREATE INDEX IF NOT EXISTS ix_permissions_is_active ON web_app.permissions (is_active);

COMMENT ON TABLE web_app.permissions IS 'Danh mục quyền cho từng API action';
COMMENT ON COLUMN web_app.permissions.code IS 'Mã quyền, ví dụ: users:me:read, roles:create';

-- ---------------------------------------------------------------------------
-- Role permissions (quyền mặc định theo role)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.role_permissions (
    role_id         INTEGER NOT NULL REFERENCES web_app.roles (id) ON DELETE CASCADE,
    permission_id   INTEGER NOT NULL REFERENCES web_app.permissions (id) ON DELETE CASCADE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS ix_role_permissions_role_id ON web_app.role_permissions (role_id);
CREATE INDEX IF NOT EXISTS ix_role_permissions_permission_id ON web_app.role_permissions (permission_id);

COMMENT ON TABLE web_app.role_permissions IS 'Gán permission cho role';

-- ---------------------------------------------------------------------------
-- User permissions (override riêng từng tài khoản)
-- effect: grant = cấp thêm quyền, deny = thu hồi quyền (ưu tiên cao hơn role)
-- Quyền hiệu lực = (role_permissions + user grant) - user deny
-- Superuser bypass toàn bộ kiểm tra permission
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_app.user_permissions (
    user_id         INTEGER NOT NULL REFERENCES web_app.users (id) ON DELETE CASCADE,
    permission_id   INTEGER NOT NULL REFERENCES web_app.permissions (id) ON DELETE CASCADE,
    effect          VARCHAR(10) NOT NULL CHECK (effect IN ('grant', 'deny')),
    note            TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, permission_id)
);

CREATE INDEX IF NOT EXISTS ix_user_permissions_user_id ON web_app.user_permissions (user_id);
CREATE INDEX IF NOT EXISTS ix_user_permissions_permission_id ON web_app.user_permissions (permission_id);

COMMENT ON TABLE web_app.user_permissions IS 'Override permission riêng cho từng user';
COMMENT ON COLUMN web_app.user_permissions.effect IS 'grant = cấp thêm, deny = thu hồi';

-- ---------------------------------------------------------------------------
-- Seed permissions (chạy sau khi đã có bảng roles)
-- ---------------------------------------------------------------------------
INSERT INTO web_app.permissions (code, name, module, action, description) VALUES
    ('auth:me', 'Xem thông tin đăng nhập', 'auth', 'me', 'Xem thông tin đăng nhập'),
    ('users:me:read', 'Xem hồ sơ cá nhân', 'users', 'me:read', 'Xem hồ sơ cá nhân'),
    ('users:me:update', 'Cập nhật hồ sơ cá nhân', 'users', 'me:update', 'Cập nhật hồ sơ cá nhân'),
    ('users:me:change_password', 'Đổi mật khẩu', 'users', 'me:change_password', 'Đổi mật khẩu'),
    ('users:me:delete', 'Xóa tài khoản của mình', 'users', 'me:delete', 'Xóa tài khoản của mình'),
    ('roles:list', 'Danh sách role', 'roles', 'list', 'Danh sách role'),
    ('roles:read', 'Chi tiết role', 'roles', 'read', 'Chi tiết role'),
    ('roles:create', 'Tạo role', 'roles', 'create', 'Tạo role'),
    ('roles:update', 'Cập nhật role', 'roles', 'update', 'Cập nhật role'),
    ('roles:delete', 'Xóa role', 'roles', 'delete', 'Xóa role'),
    ('menus:my:read', 'Menu của tôi', 'menus', 'my:read', 'Menu của tôi'),
    ('menus:list', 'Danh sách menu', 'menus', 'list', 'Danh sách menu'),
    ('menus:tree', 'Cây menu', 'menus', 'tree', 'Cây menu'),
    ('menus:read', 'Chi tiết menu', 'menus', 'read', 'Chi tiết menu'),
    ('menus:create', 'Tạo menu', 'menus', 'create', 'Tạo menu'),  
    ('menus:update', 'Cập nhật menu', 'menus', 'update', 'Cập nhật menu'),
    ('menus:delete', 'Xóa menu', 'menus', 'delete', 'Xóa menu'),
    ('config:list', 'Danh sách config', 'config', 'list', 'Danh sách config'),
    ('config:read', 'Chi tiết config', 'config', 'read', 'Chi tiết config'),
    ('config:create', 'Tạo config', 'config', 'create', 'Tạo config'),
    ('config:update', 'Cập nhật config', 'config', 'update', 'Cập nhật config'),
    ('config:delete', 'Xóa config', 'config', 'delete', 'Xóa config'),
    ('config:cache:refresh', 'Làm mới cache config', 'config', 'cache:refresh', 'Làm mới cache config'),
    ('permissions:list', 'Danh sách permission', 'permissions', 'list', 'Danh sách permission'),
    ('permissions:read', 'Chi tiết permission', 'permissions', 'read', 'Chi tiết permission'),
    ('permissions:my', 'Permission của tôi', 'permissions', 'my', 'Permission của tôi'),
    ('permissions:role:read', 'Xem permission của role', 'permissions', 'role:read', 'Xem permission của role'),
    ('permissions:role:update', 'Gán permission cho role', 'permissions', 'role:update', 'Gán permission cho role'),
    ('permissions:user:read', 'Xem permission riêng user', 'permissions', 'user:read', 'Xem permission riêng user'),
    ('permissions:user:update', 'Gán permission riêng user', 'permissions', 'user:update', 'Gán permission riêng user'),
    ('chat:send', 'Gửi tin nhắn chat AI', 'chat', 'send', 'Gửi tin nhắn chat AI')
ON CONFLICT (code) DO NOTHING;

-- Gán permission mặc định cho role user
INSERT INTO web_app.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM web_app.roles r
CROSS JOIN web_app.permissions p
WHERE r.code = 'user'
  AND p.code IN (
    'auth:me', 'users:me:read', 'users:me:update', 'users:me:change_password',
    'users:me:delete', 'menus:my:read', 'permissions:my', 'chat:send'
  )
ON CONFLICT DO NOTHING;

-- Gán permission mặc định cho role moderator
INSERT INTO web_app.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM web_app.roles r
CROSS JOIN web_app.permissions p
WHERE r.code = 'moderator'
  AND p.code IN (
    'auth:me', 'users:me:read', 'users:me:update', 'users:me:change_password',
    'menus:my:read', 'menus:list', 'menus:tree', 'menus:read',
    'roles:list', 'roles:read', 'permissions:my', 'permissions:list',
    'permissions:read', 'permissions:role:read', 'chat:send'
  )
ON CONFLICT DO NOTHING;

-- Gán permission mặc định cho role admin (tất cả permission)
INSERT INTO web_app.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM web_app.roles r
CROSS JOIN web_app.permissions p
WHERE r.code IN ('admin', 'system')
ON CONFLICT DO NOTHING;

-- Ví dụ override riêng cho user (grant thêm quyền roles:list)
-- INSERT INTO web_app.user_permissions (user_id, permission_id, effect, note)
-- SELECT u.id, p.id, 'grant', 'Cấp thêm quyền xem role'
-- FROM web_app.users u, web_app.permissions p
-- WHERE u.username = 'demo' AND p.code = 'roles:list'
-- ON CONFLICT DO NOTHING;

-- Ví dụ thu hồi quyền riêng (deny users:me:delete)
-- INSERT INTO web_app.user_permissions (user_id, permission_id, effect, note)
-- SELECT u.id, p.id, 'deny', 'Không cho phép tự xóa tài khoản'
-- FROM web_app.users u, web_app.permissions p
-- WHERE u.username = 'demo' AND p.code = 'users:me:delete'
-- ON CONFLICT DO NOTHING;
