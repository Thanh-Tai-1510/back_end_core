from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.base.models.user import User
from src.base.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def _base_query(self):
        return self.db.query(User).options(joinedload(User.role))

    def get_by_id(self, user_id: int) -> User | None:
        return self._base_query().filter(User.id == user_id).first()

    def get_by_username_or_email(self, identifier: str) -> User | None:
        return (
            self._base_query()
            .filter(
                User.deleted_at.is_(None),
                or_(User.username == identifier, User.email == identifier),
            )
            .first()
        )

    def find_by_email(self, email: str, *, exclude_id: int | None = None) -> User | None:
        query = self.db.query(User).filter(User.email == email)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return query.first()

    def find_by_phone(self, phone: str, *, exclude_id: int | None = None) -> User | None:
        query = self.db.query(User).filter(User.phone == phone)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return query.first()

    def find_registration_conflict(
        self,
        email: str,
        username: str,
        phone: str | None,
    ) -> User | None:
        filters = [User.email == email, User.username == username]
        if phone:
            filters.append(User.phone == phone)
        return self.db.query(User).filter(or_(*filters)).first()
