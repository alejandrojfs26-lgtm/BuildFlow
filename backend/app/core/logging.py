"""
Structured JSON logging configuration.

Provides a JSON formatter for structured logging, plus a helper to
bootstrap the root logger.  All application code should use the standard
`logging` module (e.g. `logger = logging.getLogger(__name__)`) and
structured data is passed via the `extra` keyword:

    logger.info("User registered", extra={"user_id": user.id, "tenant_id": tenant.id})
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        extra = getattr(record, "extra_data", None)
        if extra:
            log_entry["data"] = extra

        request_id = getattr(record, "request_id", None)
        if request_id:
            log_entry["request_id"] = request_id

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)

    level = logging.DEBUG if settings.debug else logging.INFO
    root.setLevel(level)

    for lib in ("uvicorn.access", "httpx", "httpcore", "sqlalchemy.engine"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )

    root.info(
        "Logging initialised",
        extra={
            "extra_data": {
                "app": settings.app_name,
                "version": settings.app_version,
            }
        },
    )
