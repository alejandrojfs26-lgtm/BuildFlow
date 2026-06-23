"""Celery application configuration for BuildFlow.

Routing:
  - exports.*        → queue=exports   (long, I/O-bound)
  - reports.*        → queue=reports   (long, CPU+I/O)
  - emails.*         → queue=emails    (fast, I/O-bound, rate-limited)
  - documents.*      → queue=documents (medium, CPU-bound)
  - notifications.*  → queue=default   (fast)
  - ai.*             → queue=ai        (long, CPU-bound)

Each queue can have dedicated worker pools and concurrency settings.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "buildflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Time
    timezone="America/Santiago",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Timeouts
    task_soft_time_limit=300,
    task_time_limit=600,
    # Result expiration (cleanup after 7 days)
    result_expires=60 * 60 * 24 * 7,
    # Rate limits per task type
    task_annotations={
        "emails.send_welcome_email": {"rate_limit": "10/m"},
        "emails.send_password_reset_email": {"rate_limit": "5/m"},
        "emails.send_report_approved_email": {"rate_limit": "20/m"},
    },
    # Queue routing
    task_routes={
        "exports.*": {"queue": "exports"},
        "reports.*": {"queue": "reports"},
        "emails.*": {"queue": "emails"},
        "documents.*": {"queue": "documents"},
        "notifications.*": {"queue": "default"},
        "ai.*": {"queue": "ai"},
    },
    # Auto-discovery
    imports=(
        "app.workers.tasks.emails",
        "app.workers.tasks.reports",
        "app.workers.tasks.exports",
        "app.workers.tasks.documents",
        "app.workers.tasks.notifications",
        "app.workers.tasks.ai",
    ),
)

celery_app.autodiscover_tasks(["app.workers.tasks"])
