"""Shared database session factory for Celery workers.

Each worker process creates its own engine (connection pool).
Sessions are request-scoped: one per task invocation, closed in finally.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=4,
    max_overflow=8,
    pool_recycle=3600,
    echo=False,
)

_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@contextmanager
def get_db() -> Generator[Session]:
    """Yield a scoped session, rolling back on error, closing always."""
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
