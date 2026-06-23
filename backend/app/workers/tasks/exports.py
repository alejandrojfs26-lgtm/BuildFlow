"""Export tasks — CSV/XLSX generation.

Uses shared DB session from app.workers.db instead of creating its own engine.
Notifies the requesting user on completion via notification task.
"""

from uuid import UUID

from app.core.constants import ExportStatus
from app.services.export import generate_csv, generate_xlsx
from app.workers.celery_app import celery_app
from app.workers.db import get_db


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def run_export(self, export_id: str) -> None:
    with get_db() as db:
        from app.models.export import Export

        export: Export | None = (
            db.query(Export).filter(Export.id == UUID(export_id)).first()
        )
        if not export:
            return

        export.status = ExportStatus.PROCESSING
        db.flush()

        try:
            fmt = export.format
            entity = export.entity_type

            if fmt == "xlsx":
                file_path = generate_xlsx(entity, export.tenant_id, db)
            else:
                file_path = generate_csv(entity, export.tenant_id, db)

            export.file_path = file_path
            export.status = ExportStatus.COMPLETED

        except Exception as exc:
            export.status = ExportStatus.FAILED
            export.error = str(exc)
            db.flush()
            raise self.retry(exc=exc)

    if export and export.status == ExportStatus.COMPLETED:
        _notify_export_completed.delay(str(export.id), str(export.created_by))


@celery_app.task(acks_late=True)
def _notify_export_completed(export_id: str, user_id: str) -> None:
    from app.workers.tasks.notifications import send_notification

    send_notification(
        user_id=UUID(user_id),
        title="Export Completed",
        body=f"Your export ({export_id[:8]}) is ready to download.",
        notification_type="export_completed",
    )
