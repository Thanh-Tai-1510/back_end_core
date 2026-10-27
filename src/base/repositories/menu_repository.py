from sqlalchemy.orm import Session

from src.base.models.menu import Menu
from src.base.repositories.base import BaseRepository


class MenuRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, menu_id: int) -> Menu | None:
        return self.db.get(Menu, menu_id)

    def get_by_code(self, code: str) -> Menu | None:
        return self.db.query(Menu).filter(Menu.code == code).first()

    def code_exists(self, code: str, *, exclude_id: int | None = None) -> bool:
        query = self.db.query(Menu).filter(Menu.code == code)
        if exclude_id is not None:
            query = query.filter(Menu.id != exclude_id)
        return query.first() is not None

    def list_all(self, *, include_deleted: bool = False) -> list[Menu]:
        query = self.db.query(Menu).order_by(Menu.sort_order, Menu.id)
        if not include_deleted:
            query = query.filter(Menu.deleted_at.is_(None))
        return query.all()

    def list_active(self) -> list[Menu]:
        return (
            self.db.query(Menu)
            .filter(Menu.deleted_at.is_(None), Menu.is_active.is_(True))
            .order_by(Menu.sort_order, Menu.id)
            .all()
        )
