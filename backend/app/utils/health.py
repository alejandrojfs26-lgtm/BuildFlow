from datetime import UTC, datetime

import redis as redis_lib
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings


class HealthCheck:
    def __init__(self, db: Session):
        self.db = db
        self.checks: dict[str, dict] = {}
        self.healthy = True

    def _check_database(self) -> None:
        start = datetime.now(UTC)
        try:
            self.db.execute(text("SELECT 1"))
            elapsed = (datetime.now(UTC) - start).total_seconds()
            self.checks["database"] = {
                "status": "up",
                "latency_ms": round(elapsed * 1000, 2),
            }
        except Exception as exc:
            self.healthy = False
            self.checks["database"] = {"status": "down", "error": str(exc)}

    def _check_redis(self) -> None:
        try:
            client = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
            client.ping()
            self.checks["redis"] = {"status": "up"}
        except Exception as exc:
            self.healthy = False
            self.checks["redis"] = {"status": "down", "error": str(exc)}

    def _check_celery_broker(self) -> None:
        try:
            client = redis_lib.from_url(settings.celery_broker_url, socket_connect_timeout=2)
            client.ping()
            self.checks["celery_broker"] = {"status": "up"}
        except Exception as exc:
            self.healthy = False
            self.checks["celery_broker"] = {"status": "down", "error": str(exc)}

    def _check_storage(self) -> None:
        try:
            path = settings.storage_local_path
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".health"
            probe.touch()
            probe.unlink()
            self.checks["storage"] = {"status": "up"}
        except Exception as exc:
            self.healthy = False
            self.checks["storage"] = {"status": "down", "error": str(exc)}

    def liveness(self) -> dict:
        return {
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        }

    def readiness(self, deep: bool = False) -> dict:
        self._check_database()
        if deep:
            self._check_redis()
            self._check_celery_broker()
            self._check_storage()

        return {
            "status": "healthy" if self.healthy else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": self.checks,
        }
