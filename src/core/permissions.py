"""Mã permission cho từng API action (format: module:action)."""


class PermissionCode:
    AUTH_ME = "auth:me"

    USERS_ME_READ = "users:me:read"
    USERS_ME_UPDATE = "users:me:update"
    USERS_ME_CHANGE_PASSWORD = "users:me:change_password"
    USERS_ME_DELETE = "users:me:delete"

    ROLES_LIST = "roles:list"
    ROLES_READ = "roles:read"
    ROLES_CREATE = "roles:create"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"

    MENUS_MY_READ = "menus:my:read"
    MENUS_LIST = "menus:list"
    MENUS_TREE = "menus:tree"
    MENUS_READ = "menus:read"
    MENUS_CREATE = "menus:create"
    MENUS_UPDATE = "menus:update"
    MENUS_DELETE = "menus:delete"

    CONFIG_LIST = "config:list"
    CONFIG_READ = "config:read"
    CONFIG_CREATE = "config:create"
    CONFIG_UPDATE = "config:update"
    CONFIG_DELETE = "config:delete"
    CONFIG_CACHE_REFRESH = "config:cache:refresh"

    PERMISSIONS_LIST = "permissions:list"
    PERMISSIONS_READ = "permissions:read"
    PERMISSIONS_MY = "permissions:my"
    PERMISSIONS_ROLE_READ = "permissions:role:read"
    PERMISSIONS_ROLE_UPDATE = "permissions:role:update"
    PERMISSIONS_USER_READ = "permissions:user:read"
    PERMISSIONS_USER_UPDATE = "permissions:user:update"

    CHAT_SEND = "chat:send"


ALL_PERMISSIONS: list[tuple[str, str, str, str]] = [
    (PermissionCode.AUTH_ME, "Xem thông tin đăng nhập", "auth", "me"),
    (PermissionCode.USERS_ME_READ, "Xem hồ sơ cá nhân", "users", "me:read"),
    (PermissionCode.USERS_ME_UPDATE, "Cập nhật hồ sơ cá nhân", "users", "me:update"),
    (PermissionCode.USERS_ME_CHANGE_PASSWORD, "Đổi mật khẩu", "users", "me:change_password"),
    (PermissionCode.USERS_ME_DELETE, "Xóa tài khoản của mình", "users", "me:delete"),
    (PermissionCode.ROLES_LIST, "Danh sách role", "roles", "list"),
    (PermissionCode.ROLES_READ, "Chi tiết role", "roles", "read"),
    (PermissionCode.ROLES_CREATE, "Tạo role", "roles", "create"),
    (PermissionCode.ROLES_UPDATE, "Cập nhật role", "roles", "update"),
    (PermissionCode.ROLES_DELETE, "Xóa role", "roles", "delete"),
    (PermissionCode.MENUS_MY_READ, "Menu của tôi", "menus", "my:read"),
    (PermissionCode.MENUS_LIST, "Danh sách menu", "menus", "list"),
    (PermissionCode.MENUS_TREE, "Cây menu", "menus", "tree"),
    (PermissionCode.MENUS_READ, "Chi tiết menu", "menus", "read"),
    (PermissionCode.MENUS_CREATE, "Tạo menu", "menus", "create"),
    (PermissionCode.MENUS_UPDATE, "Cập nhật menu", "menus", "update"),
    (PermissionCode.MENUS_DELETE, "Xóa menu", "menus", "delete"),
    (PermissionCode.CONFIG_LIST, "Danh sách config", "config", "list"),
    (PermissionCode.CONFIG_READ, "Chi tiết config", "config", "read"),
    (PermissionCode.CONFIG_CREATE, "Tạo config", "config", "create"),
    (PermissionCode.CONFIG_UPDATE, "Cập nhật config", "config", "update"),
    (PermissionCode.CONFIG_DELETE, "Xóa config", "config", "delete"),
    (PermissionCode.CONFIG_CACHE_REFRESH, "Làm mới cache config", "config", "cache:refresh"),
    (PermissionCode.PERMISSIONS_LIST, "Danh sách permission", "permissions", "list"),
    (PermissionCode.PERMISSIONS_READ, "Chi tiết permission", "permissions", "read"),
    (PermissionCode.PERMISSIONS_MY, "Permission của tôi", "permissions", "my"),
    (PermissionCode.PERMISSIONS_ROLE_READ, "Xem permission của role", "permissions", "role:read"),
    (PermissionCode.PERMISSIONS_ROLE_UPDATE, "Gán permission cho role", "permissions", "role:update"),
    (PermissionCode.PERMISSIONS_USER_READ, "Xem permission riêng user", "permissions", "user:read"),
    (PermissionCode.PERMISSIONS_USER_UPDATE, "Gán permission riêng user", "permissions", "user:update"),
    (PermissionCode.CHAT_SEND, "Gửi tin nhắn chat AI", "chat", "send"),
]

ROLE_DEFAULT_PERMISSIONS: dict[str, list[str]] = {
    "user": [
        PermissionCode.AUTH_ME,
        PermissionCode.USERS_ME_READ,
        PermissionCode.USERS_ME_UPDATE,
        PermissionCode.USERS_ME_CHANGE_PASSWORD,
        PermissionCode.USERS_ME_DELETE,
        PermissionCode.MENUS_MY_READ,
        PermissionCode.PERMISSIONS_MY,
        PermissionCode.CHAT_SEND,
    ],
    "moderator": [
        PermissionCode.AUTH_ME,
        PermissionCode.USERS_ME_READ,
        PermissionCode.USERS_ME_UPDATE,
        PermissionCode.USERS_ME_CHANGE_PASSWORD,
        PermissionCode.MENUS_MY_READ,
        PermissionCode.MENUS_LIST,
        PermissionCode.MENUS_TREE,
        PermissionCode.MENUS_READ,
        PermissionCode.ROLES_LIST,
        PermissionCode.ROLES_READ,
        PermissionCode.PERMISSIONS_MY,
        PermissionCode.PERMISSIONS_LIST,
        PermissionCode.PERMISSIONS_READ,
        PermissionCode.PERMISSIONS_ROLE_READ,
        PermissionCode.CHAT_SEND,
    ],
    "admin": [code for code, *_ in ALL_PERMISSIONS],
    "system": [code for code, *_ in ALL_PERMISSIONS],
}
