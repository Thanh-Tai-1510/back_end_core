"""Create tables in web_app schema and seed auth config rows."""

import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text

from src.base.models.config import AppConfig
from src.base.models.menu import Menu
from src.base.models.permission import Permission, RolePermission, UserPermission
from src.base.models.role import Role
from src.base.models.user import User
from src.base.services.permission_service import PermissionService
from src.core.config import settings
from src.core.database import Base, SessionLocal, engine
from src.core.security import get_password_hash

DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@local.dev")
DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")

DEFAULT_SYSTEM_EMAIL = os.getenv("SYSTEM_EMAIL", "system@local.dev")
DEFAULT_SYSTEM_USERNAME = os.getenv("SYSTEM_USERNAME", "system")
DEFAULT_SYSTEM_PASSWORD = os.getenv("SYSTEM_PASSWORD", "System@123")


def _maintenance_database_url() -> str:
    return (
        f"postgresql+psycopg2://{settings.PG_USER}:{settings.PG_PASSWORD}"
        f"@{settings.PG_HOST}:{settings.PG_PORT}/postgres"
    )


def ensure_database() -> None:
    """Create PG_DATABASE if missing (connects via maintenance db `postgres`)."""
    maintenance_engine = create_engine(_maintenance_database_url(), isolation_level="AUTOCOMMIT")
    try:
        with maintenance_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.PG_DATABASE},
            ).first()
            if exists:
                print(f"  = database: {settings.PG_DATABASE} (exists)")
                return

            conn.execute(text(f'CREATE DATABASE "{settings.PG_DATABASE}"'))
            print(f"  + database: {settings.PG_DATABASE}")
    finally:
        maintenance_engine.dispose()


def ensure_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.PG_SCHEMA}"'))


def cleanup_legacy_public_users() -> None:
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
                """
            )
        ).first()
        if exists:
            conn.execute(text("DROP TABLE public.users CASCADE"))
            print("  - dropped legacy public.users")


def seed_roles(db) -> None:
    defaults = [
        ("user", "Người dùng", "Quyền truy cập cơ bản", False, 1),
        ("moderator", "Điều hành", "Quản lý nội dung", True, 2),
        ("admin", "Quản trị viên", "Quản trị hệ thống", True, 3),
        ("system", "Hệ thống", "Tài khoản nội bộ", True, 99),
    ]
    for code, name, description, is_system, sort_order in defaults:
        existing = db.query(Role).filter(Role.code == code).first()
        if existing is None:
            db.add(
                Role(
                    code=code,
                    name=name,
                    description=description,
                    is_system=is_system,
                    sort_order=sort_order,
                )
            )
            print(f"  + role: {code}")
        else:
            print(f"  = role: {code} (exists)")


def seed_app_config(db) -> None:
    defaults = {
        "app_name": ("app", "Financial Statement API"),
        "api_v1_prefix": ("app", "/api/v1"),
        "log_level": ("app", "INFO"),
        "log_sql": ("app", "false"),
        "log_dir": ("app", "app/logs"),
    }
    for key, (config_type, value) in defaults.items():
        existing = db.get(AppConfig, key)
        if existing is None:
            db.add(AppConfig(key=key, type=config_type, value=value))
            print(f"  + config: {key}")
        else:
            print(f"  = config: {key} (exists)")


def seed_admin_user(db) -> None:
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if admin_role is None:
        print("  ! admin role not found, skip admin user")
        return

    existing = (
        db.query(User)
        .filter((User.username == DEFAULT_ADMIN_USERNAME) | (User.email == DEFAULT_ADMIN_EMAIL))
        .first()
    )
    if existing:
        print(f"  = admin user: {DEFAULT_ADMIN_USERNAME} (exists)")
        return

    now = datetime.now(UTC).replace(tzinfo=None)
    db.add(
        User(
            email=DEFAULT_ADMIN_EMAIL,
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            display_name="Administrator",
            role_id=admin_role.id,
            is_active=True,
            is_superuser=True,
            is_staff=True,
            is_verified=True,
            must_change_password=True,
            password_changed_at=now,
        )
    )
    print(f"  + admin user: {DEFAULT_ADMIN_USERNAME} ({DEFAULT_ADMIN_EMAIL})")


def seed_system_user(db) -> None:
    system_role = db.query(Role).filter(Role.code == "system").first()
    if system_role is None:
        print("  ! system role not found, skip system user")
        return

    existing = (
        db.query(User)
        .filter((User.username == DEFAULT_SYSTEM_USERNAME) | (User.email == DEFAULT_SYSTEM_EMAIL))
        .first()
    )
    if existing:
        print(f"  = system user: {DEFAULT_SYSTEM_USERNAME} (exists)")
        return

    now = datetime.now(UTC).replace(tzinfo=None)
    db.add(
        User(
            email=DEFAULT_SYSTEM_EMAIL,
            username=DEFAULT_SYSTEM_USERNAME,
            hashed_password=get_password_hash(DEFAULT_SYSTEM_PASSWORD),
            display_name="System Account",
            role_id=system_role.id,
            is_active=True,
            is_superuser=True,
            is_staff=True,
            is_verified=True,
            must_change_password=False,
            password_changed_at=now,
        )
    )
    print(f"  + system user: {DEFAULT_SYSTEM_USERNAME} ({DEFAULT_SYSTEM_EMAIL})")


def seed_auth_config(db) -> None:
    defaults = {
        "jwt_secret_key": secrets.token_urlsafe(32),
        "jwt_algorithm": "HS256",
        "jwt_expire_minutes": "60",
    }
    for key, value in defaults.items():
        existing = db.get(AppConfig, key)
        if existing is None:
            db.add(AppConfig(key=key, type="auth", value=value))
            print(f"  + config: {key}")
        else:
            print(f"  = config: {key} (exists)")


def main() -> None:
    print(f"Using database: {settings.PG_DATABASE}")
    print(f"Using schema: {settings.PG_SCHEMA}")
    print("Ensuring database exists...")
    ensure_database()
    print("Ensuring schema exists...")
    ensure_schema()

    print("Cleaning legacy tables...")
    cleanup_legacy_public_users()

    print("Creating tables...")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Role.__table__,
            Permission.__table__,
            RolePermission.__table__,
            User.__table__,
            UserPermission.__table__,
            AppConfig.__table__,
            Menu.__table__,
        ],
    )

    db = SessionLocal()
    try:
        print("Seeding roles...")
        seed_roles(db)
        print("Seeding app config...")
        seed_app_config(db)
        print("Seeding auth config...")
        seed_auth_config(db)
        db.commit()

        print("Seeding permissions...")
        PermissionService(db).seed_permissions()
        print("Seeding role permissions...")
        PermissionService(db).seed_role_permissions()
        print("Seeding admin user...")
        seed_admin_user(db)
        print("Seeding system user...")
        seed_system_user(db)
        db.commit()
    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    main()
