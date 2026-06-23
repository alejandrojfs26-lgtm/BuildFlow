"""
Structured JSON logging configuration.

Uses structlog under the hood for structured, contextual logging.
All application code should use:

    import structlog
    logger = structlog.get_logger("buildflow")

Context can be bound via:

    logger = logger.bind(request_id=..., tenant_id=...)
"""

import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

import structlog

from app.core.config import settings

trace_context: ContextVar[dict] = ContextVar("trace_context", default=None)
_RENDERER = structlog.processors.JSONRenderer()


def _add_span(_logger, _method_name, event_dict):
    ctx = trace_context.get()
    if ctx:
        event_dict.update(ctx)
    return event_dict


def _add_timestamp(_logger, _method_name, event_dict):
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def setup_logging() -> None:
    structlog.configure(
        processors=[
            _add_timestamp,
            _add_span,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _RENDERER,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    root.addHandler(handler)

    level = logging.DEBUG if settings.debug else logging.INFO
    root.setLevel(level)

    for lib in ("uvicorn.access", "httpx", "httpcore", "sqlalchemy.engine"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )

    logger = structlog.get_logger("buildflow")
    logger.info("Logging initialised", app=settings.app_name, version=settings.app_version)
