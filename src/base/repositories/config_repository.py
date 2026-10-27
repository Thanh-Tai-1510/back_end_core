from sqlalchemy.orm import Session

from src.base.models.config import AppConfig
from src.base.repositories.base import BaseRepository


class ConfigRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_key(self, key: str) -> AppConfig | None:
        return self.db.get(AppConfig, key)

    def list_all(self) -> list[AppConfig]:
        return self.db.query(AppConfig).order_by(AppConfig.key).all()
