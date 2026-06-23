from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.export import ExportStatus
from app.services.export import generate_csv, generate_xlsx
from app.workers.celery_app import celery_app

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(bind=True, max_retries=2)
def run_export(self, export_id: str) -> None:
    db: Session = SessionLocal()
    try:
        from app.models.export import Export

        export = db.query(Export).filter(Export.id == UUID(export_id)).first()
        if not export:
            return

        export.status = ExportStatus.PROCESSING
        db.flush()

        fmt = export.format
        entity = export.entity_type

        if fmt == "xlsx":
            file_path = generate_xlsx(entity, export.tenant_id, db)
        else:
            file_path = generate_csv(entity, export.tenant_id, db)

        export.file_path = file_path
        export.status = ExportStatus.COMPLETED
        db.commit()

    except Exception as exc:
        db.rollback()
        from app.models.export import Export

        db.query(Export).filter(Export.id == UUID(export_id)).update(
            {"status": ExportStatus.FAILED, "error": str(exc)}
        )
        db.commit()
        raise self.retry(exc=exc)

    finally:
        db.close()
