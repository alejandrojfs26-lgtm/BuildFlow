from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Environment, settings
from app.core.metrics import db_connection_pool_size

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.environment == Environment.DEVELOPMENT,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def _update_pool_metrics() -> None:
    pool = engine.pool
    db_connection_pool_size.labels(state="size").set(pool.size())
    db_connection_pool_size.labels(state="checkedout").set(pool.checkedout())
    db_connection_pool_size.labels(state="overflow").set(pool.overflow())


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    _update_pool_metrics()


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    _update_pool_metrics()


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
