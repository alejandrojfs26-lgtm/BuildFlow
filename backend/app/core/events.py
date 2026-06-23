from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.logging import setup_logging
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger = structlog.get_logger("buildflow")
    logger.info("app_starting", environment=_app.state._state.get("environment"))

    pool = engine.pool
    logger.info(
        "db_pool_initialised",
        pool_size=pool.size(),
        overflow=pool._max_overflow,
    )

    yield

    engine.dispose()
    logger.info("app_stopped")
