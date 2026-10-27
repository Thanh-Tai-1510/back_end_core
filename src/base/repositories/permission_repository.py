from sqlalchemy.orm import Session, joinedload

from src.base.models.permission import Permission, RolePermission, UserPermission
from src.base.models.role import Role
from src.base.models.user import User


class PermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self, *, active_only: bool = True) -> list[Permission]:
        query = self.db.query(Permission).order_by(Permission.module, Permission.code)
        if active_only:
            query = query.filter(Permission.is_active.is_(True))
        return query.all()

    def get_by_id(self, permission_id: int) -> Permission | None:
        return self.db.get(Permission, permission_id)

    def get_by_code(self, code: str) -> Permission | None:
        return self.db.query(Permission).filter(Permission.code == code).first()

    def get_role_with_permissions(self, role_id: int) -> Role | None:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.id == role_id, Role.deleted_at.is_(None))
            .first()
        )

    def get_user_with_overrides(self, user_id: int) -> User | None:
        return (
            self.db.query(User)
            .options(
                joinedload(User.role),
                joinedload(User.permission_overrides).joinedload(UserPermission.permission),
            )
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def get_role_permission_codes(self, role_id: int) -> set[str]:
        rows = (
            self.db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(
                RolePermission.role_id == role_id,
                Permission.is_active.is_(True),
            )
            .all()
        )
        return {row[0] for row in rows}

    def get_user_override_codes(self, user_id: int) -> tuple[set[str], set[str]]:
        rows = (
            self.db.query(Permission.code, UserPermission.effect)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .filter(
                UserPermission.user_id == user_id,
                Permission.is_active.is_(True),
            )
            .all()
        )
        grants = {code for code, effect in rows if effect == "grant"}
        denies = {code for code, effect in rows if effect == "deny"}
        return grants, denies

    def replace_role_permissions(self, role: Role, permission_ids: list[int]) -> None:
        role.permissions.clear()
        if permission_ids:
            permissions = (
                self.db.query(Permission)
                .filter(Permission.id.in_(permission_ids), Permission.is_active.is_(True))
                .all()
            )
            role.permissions = permissions

    def replace_user_overrides(
        self,
        user: User,
        overrides: list[tuple[int, str, str | None]],
    ) -> None:
        self.db.query(UserPermission).filter(UserPermission.user_id == user.id).delete()
        for permission_id, effect, note in overrides:
            self.db.add(
                UserPermission(
                    user_id=user.id,
                    permission_id=permission_id,
                    effect=effect,
                    note=note,
                )
            )

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)
