from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, entity: object) -> None:
        self.db.add(entity)

    def delete(self, entity: object) -> None:
        self.db.delete(entity)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: object, *, attribute_names: list[str] | None = None) -> None:
        if attribute_names:
            self.db.refresh(entity, attribute_names=attribute_names)
        else:
            self.db.refresh(entity)

    def rollback(self) -> None:
        self.db.rollback()
