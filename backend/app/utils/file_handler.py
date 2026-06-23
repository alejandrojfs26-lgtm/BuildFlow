import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppError

BASE_DIR = Path(settings.storage_local_path)


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_file(content: bytes, subdirectory: str, ext: str) -> str:
    filename = f"{uuid.uuid4().hex}{ext}"
    relative = f"{subdirectory}/{filename}"
    full_path = BASE_DIR / relative
    ensure_dir(full_path)
    full_path.write_bytes(content)
    return relative


def get_absolute_path(relative_path: str) -> Path:
    return BASE_DIR / relative_path


def resolve_safe_path(file_path: str) -> Path:
    resolved = (BASE_DIR / file_path).resolve()
    base = BASE_DIR.resolve()
    if base not in resolved.parents and resolved != base:
        raise AppError("Access denied", code="forbidden_path", status_code=403)
    return resolved


def delete_file(relative_path: str) -> None:
    path = BASE_DIR / relative_path
    if path.exists():
        path.unlink()
