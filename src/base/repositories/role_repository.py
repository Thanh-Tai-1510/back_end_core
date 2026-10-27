from sqlalchemy.orm import Session

from src.base.models.role import Role
from src.base.repositories.base import BaseRepository


class RoleRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def get_by_code(self, code: str) -> Role | None:
        return self.db.query(Role).filter(Role.code == code).first()

    def get_active_by_id(self, role_id: int) -> Role | None:
        return (
            self.db.query(Role)
            .filter(
                Role.id == role_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
            )
            .first()
        )

    def get_default_user_role(self) -> Role | None:
        return (
            self.db.query(Role)
            .filter(
                Role.code == "user",
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
            )
            .first()
        )

    def list_all(self, *, include_deleted: bool = False) -> list[Role]:
        query = self.db.query(Role).order_by(Role.sort_order, Role.id)
        if not include_deleted:
            query = query.filter(Role.deleted_at.is_(None))
        return query.all()

    def code_exists(self, code: str, *, exclude_id: int | None = None) -> bool:
        query = self.db.query(Role).filter(Role.code == code)
        if exclude_id is not None:
            query = query.filter(Role.id != exclude_id)
        return query.first() is not None
