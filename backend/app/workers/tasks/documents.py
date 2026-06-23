"""Document processing pipeline — thumbnails, text extraction, metadata.

Flow (per document):
  1. Generate thumbnail (images) or preview (PDF)
  2. Extract text content (PDF text layer)
  3. Store metadata on the document model

Called from DocumentService.create() and PhotoService.create() via .delay().
"""

from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.workers.celery_app import celery_app
from app.workers.db import get_db

STORAGE = Path(settings.storage_local_path)
THUMBNAIL_DIR = STORAGE / ".thumbnails"


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def process_document(self, document_id: str) -> None:
    """Post-upload pipeline for documents: thumbnail + text extraction."""
    with get_db() as db:
        from app.models.document import Document

        doc: Document | None = (
            db.query(Document)
            .filter(Document.id == UUID(document_id))
            .first()
        )
        if not doc:
            return

        source = STORAGE / doc.file_path
        if not source.exists():
            return

        doc_type = doc.file_type
        metadata: dict = {}

        if doc_type == "application/pdf":
            thumbnail = _generate_pdf_thumbnail(source, doc.id)
            text = _extract_pdf_text(source)
            if text:
                metadata["text_preview"] = text[:500]
        elif doc_type in ("image/jpeg", "image/png"):
            thumbnail = _generate_image_thumbnail(source, doc.id)
        else:
            thumbnail = None

        if thumbnail:
            metadata["thumbnail_path"] = str(thumbnail)

        if metadata:
            from sqlalchemy import update

            stmt = (
                update(Document)
                .where(Document.id == doc.id)
                .values(metadata=metadata)
            )
            db.execute(stmt)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def process_photo(self, photo_id: str) -> None:
    """Post-upload pipeline for photos: thumbnail generation."""
    with get_db() as db:
        from app.models.photo import Photo

        photo: Photo | None = (
            db.query(Photo)
            .filter(Photo.id == UUID(photo_id))
            .first()
        )
        if not photo:
            return

        source = STORAGE / photo.file_path
        if not source.exists():
            return

        thumbnail = _generate_image_thumbnail(source, photo.id)
        if thumbnail:
            from sqlalchemy import update

            stmt = (
                update(Photo)
                .where(Photo.id == photo.id)
                .values(thumbnail_path=str(thumbnail))
            )
            db.execute(stmt)


# ---------------------------------------------------------------------------
# Helpers — each gracefully handles missing optional dependencies
# ---------------------------------------------------------------------------


def _generate_image_thumbnail(source: Path, obj_id: UUID) -> Path | None:
    """Create a 300px-wide JPEG thumbnail next to the original."""
    try:
        from PIL import Image
    except ImportError:
        return None

    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMBNAIL_DIR / f"{obj_id.hex}_thumb.jpg"
    if dest.exists():
        return dest

    try:
        img = Image.open(source)
        img.thumbnail((300, 300))
        img.convert("RGB").save(dest, "JPEG", quality=80)
        return dest
    except Exception:
        return None


def _generate_pdf_thumbnail(source: Path, obj_id: UUID) -> Path | None:
    """Render first page of a PDF as a thumbnail image."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMBNAIL_DIR / f"{obj_id.hex}_thumb.jpg"
    if dest.exists():
        return dest

    try:
        doc = fitz.open(str(source))
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.3, 0.3))
        pix.save(str(dest))
        doc.close()
        return dest
    except Exception:
        return None


def _extract_pdf_text(source: Path) -> str | None:
    """Extract text content from a PDF."""
    try:
        import fitz
    except ImportError:
        return None

    try:
        doc = fitz.open(str(source))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip() or None
    except Exception:
        return None
