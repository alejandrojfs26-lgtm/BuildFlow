"""In-app notification tasks — alerts, reminders, status changes.

Currently sends via console log + Redis pub/sub (extensible to WebSocket).
The `send_notification` helper is imported and used by other task modules.
"""

from uuid import UUID

from app.workers.celery_app import celery_app


def send_notification(
    user_id: UUID,
    title: str,
    body: str,
    notification_type: str = "general",
    tenant_id: UUID | None = None,
) -> None:
    """Synchronous helper called from other tasks. Dispatches to backends."""
    _log_notification(user_id, title, body, notification_type)
    _publish_to_redis(user_id, title, body, notification_type)


def _log_notification(
    user_id: UUID, title: str, body: str, notification_type: str
) -> None:
    import structlog

    logger = structlog.get_logger("buildflow.notifications")
    logger.info(
        "notification",
        user_id=str(user_id),
        title=title,
        type=notification_type,
    )


def _publish_to_redis(
    user_id: UUID, title: str, body: str, notification_type: str
) -> None:
    """Publish notification to Redis channel for real-time delivery."""
    import json

    try:
        from app.utils.redis_client import redis_client

        channel = f"notifications:{user_id.hex}"
        payload = json.dumps({
            "type": notification_type,
            "title": title,
            "body": body,
        })
        redis_client.publish(channel, payload)
    except Exception:
        pass  # Redis unavailable — notifications degrade gracefully


# ---------------------------------------------------------------------------
# Scheduled / event-driven notification tasks
# ---------------------------------------------------------------------------


@celery_app.task(acks_late=True)
def notify_low_stock(tenant_id: str) -> None:
    """Check all materials for low stock and notify tenant admins.

    Triggered by Celery Beat (scheduled) or called after material update.
    """
    from app.workers.db import get_db

    with get_db() as db:
        from app.models.material import Material

        low_stock_items = (
            db.query(Material)
            .filter(
                Material.tenant_id == UUID(tenant_id),
                Material.stock <= Material.min_stock,
            )
            .all()
        )

        if not low_stock_items:
            return

        from app.core.constants import Role
        from app.models.user import User

        admins = (
            db.query(User)
            .filter(
                User.tenant_id == UUID(tenant_id),
                User.role.in_([Role.ADMIN, Role.PROJECT_MANAGER]),
                User.is_active.is_(True),
            )
            .all()
        )

        names = ", ".join(m.name for m in low_stock_items[:5])
        count = len(low_stock_items)
        body = (
            f"{count} material{'s' if count > 1 else ''} low on stock: {names}"
            + ("..." if count > 5 else "")
        )

        for admin in admins:
            send_notification(
                user_id=admin.id,
                title="Low Stock Alert",
                body=body,
                notification_type="low_stock",
                tenant_id=UUID(tenant_id),
            )


@celery_app.task(acks_late=True)
def notify_project_status_change(
    project_id: str, tenant_id: str, old_status: str, new_status: str
) -> None:
    """Notify project stakeholders of a status transition."""
    from app.workers.db import get_db

    with get_db() as db:
        from app.core.constants import Role
        from app.models.project import Project
        from app.models.project_worker import ProjectWorker
        from app.models.user import User

        project: Project | None = (
            db.query(Project)
            .filter(Project.id == UUID(project_id))
            .first()
        )
        if not project:
            return

        # Notify project managers + admins
        managers = (
            db.query(User)
            .filter(
                User.tenant_id == UUID(tenant_id),
                User.role.in_([Role.ADMIN, Role.PROJECT_MANAGER]),
                User.is_active.is_(True),
            )
            .all()
        )

        # Notify assigned workers
        assignments = (
            db.query(ProjectWorker)
            .filter(
                ProjectWorker.project_id == project.id,
                ProjectWorker.is_active.is_(True),
            )
            .all()
        )
        assigned_user_ids = {a.worker_id for a in assignments}
        workers = (
            db.query(User)
            .filter(
                User.tenant_id == UUID(tenant_id),
                User.id.in_(assigned_user_ids),
                User.is_active.is_(True),
            )
            .all()
        )

        title = f"Project {project.name}: {old_status} → {new_status}"
        body = f"Status changed from {old_status} to {new_status}."

        for user in managers + workers:
            send_notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type="project_status_change",
                tenant_id=UUID(tenant_id),
            )


@celery_app.task(acks_late=True)
def notify_daily_report_reminder(tenant_id: str) -> None:
    """Remind workers who haven't submitted a report today.

    Intended for daily Celery Beat schedule (end of workday).
    """
    from datetime import date

    from app.workers.db import get_db

    with get_db() as db:
        from app.models.daily_report import DailyReport
        from app.models.user import User
        from app.models.worker import Worker

        today = date.today()
        tenant_uuid = UUID(tenant_id)

        workers_with_reports = (
            db.query(DailyReport.worker_id)
            .filter(
                DailyReport.tenant_id == tenant_uuid,
                DailyReport.date == today,
            )
            .subquery()
        )

        missing_workers = (
            db.query(Worker)
            .filter(
                Worker.tenant_id == tenant_uuid,
                Worker.is_active.is_(True),
                ~Worker.id.in_(workers_with_reports),
            )
            .all()
        )

        for worker in missing_workers:
            if not worker.user_id:
                continue

            user = (
                db.query(User)
                .filter(User.id == worker.user_id)
                .first()
            )
            if not user or not user.is_active:
                continue

            send_notification(
                user_id=user.id,
                title="Daily Report Reminder",
                body="You haven't submitted your daily report for today.",
                notification_type="report_reminder",
                tenant_id=tenant_uuid,
            )
