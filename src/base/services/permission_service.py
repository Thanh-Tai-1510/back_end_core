from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.core.permissions import ALL_PERMISSIONS
from src.base.models.permission import Permission
from src.base.models.role import Role
from src.base.models.user import User
from src.base.repositories.permission_repository import PermissionRepository
from src.base.requests.permission_request import (
    UpdateRolePermissionsRequest,
    UpdateUserPermissionsRequest,
)

logger = get_logger(Loggers.SERVICE)


class PermissionService:
    def __init__(self, db: Session) -> None:
        self.repo = PermissionRepository(db)

    def list_permissions(self) -> list[Permission]:
        return self.repo.list_all()

    def get_by_id(self, permission_id: int) -> Permission | None:
        return self.repo.get_by_id(permission_id)

    def has_permission(self, user: User, permission_code: str) -> bool:
        if user.is_superuser:
            return True
        return permission_code in self.get_effective_codes(user)

    def get_effective_codes(self, user: User) -> set[str]:
        if user.is_superuser:
            return {code for code, *_ in ALL_PERMISSIONS}

        role_codes = self.repo.get_role_permission_codes(user.role_id)
        grant_codes, deny_codes = self.repo.get_user_override_codes(user.id)
        return (role_codes | grant_codes) - deny_codes

    def get_role_permissions(self, role_id: int) -> Role | None:
        return self.repo.get_role_with_permissions(role_id)

    def get_user_overrides(self, user_id: int) -> User | None:
        return self.repo.get_user_with_overrides(user_id)

    def update_role_permissions(self, role: Role, request: UpdateRolePermissionsRequest) -> Role:
        if role.is_system and role.code in {"admin", "system"}:
            raise ValueError("Cannot modify permissions of system admin roles")

        invalid_ids = set(request.permission_ids)
        valid = (
            self.repo.db.query(Permission.id)
            .filter(Permission.id.in_(invalid_ids), Permission.is_active.is_(True))
            .all()
        )
        valid_ids = {row[0] for row in valid}
        if invalid_ids - valid_ids:
            raise ValueError("One or more permissions not found or inactive")

        self.repo.replace_role_permissions(role, request.permission_ids)
        self.repo.commit()
        self.repo.refresh(role)
        logger.info("Role permissions updated: role_id=%s", role.id)
        return self.repo.get_role_with_permissions(role.id) or role

    def update_user_permissions(self, user: User, request: UpdateUserPermissionsRequest) -> User:
        seen: set[int] = set()
        overrides: list[tuple[int, str, str | None]] = []
        for item in request.overrides:
            if item.permission_id in seen:
                raise ValueError("Duplicate permission in overrides")
            seen.add(item.permission_id)
            effect = item.effect.value if hasattr(item.effect, "value") else str(item.effect)
            if effect not in {"grant", "deny"}:
                raise ValueError("Effect must be grant or deny")
            permission = self.repo.get_by_id(item.permission_id)
            if permission is None or not permission.is_active:
                raise ValueError(f"Permission id={item.permission_id} not found or inactive")
            overrides.append((item.permission_id, effect, item.note))

        self.repo.replace_user_overrides(user, overrides)
        self.repo.commit()
        logger.info("User permission overrides updated: user_id=%s", user.id)
        return self.repo.get_user_with_overrides(user.id) or user

    def seed_permissions(self) -> None:
        for code, name, module, action in ALL_PERMISSIONS:
            existing = self.repo.get_by_code(code)
            if existing is None:
                self.repo.db.add(
                    Permission(
                        code=code,
                        name=name,
                        module=module,
                        action=action,
                        description=name,
                    )
                )
        self.repo.commit()

    def seed_role_permissions(self) -> None:
        from src.core.permissions import ROLE_DEFAULT_PERMISSIONS

        for role_code, permission_codes in ROLE_DEFAULT_PERMISSIONS.items():
            role = self.repo.db.query(Role).filter(Role.code == role_code).first()
            if role is None:
                continue
            permission_ids = []
            for code in permission_codes:
                perm = self.repo.get_by_code(code)
                if perm:
                    permission_ids.append(perm.id)
            if permission_ids:
                self.repo.replace_role_permissions(role, permission_ids)
        self.repo.commit()
