from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config.env import settings
from src.core.logging import Loggers, get_logger

logger = get_logger(Loggers.DB)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.PG_SCHEMA)


@event.listens_for(Engine, "connect")
def on_db_connect(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET search_path TO {settings.PG_SCHEMA}, public")
    cursor.close()
    logger.debug("Database connection established (search_path=%s)", settings.PG_SCHEMA)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        logger.exception("Database session error")
        db.rollback()
        raise
    finally:
        db.close()
